from fakes import FakeClient, text, tool

from course import SAMPLE_REPO, Hooks, repo_tools, run_agent


def _valid_alternation(messages):
    roles = [m["role"] for m in messages]
    return roles[0] == "user" and all(a != b for a, b in zip(roles, roles[1:]))


def test_tool_result_clearing_keeps_newest(load):
    ch10 = load("ch10-compaction/compaction.py")
    client = FakeClient([tool("read_file", {"path": "inventory/stats.py"}) for _ in range(5)] + [text("done")])
    result = run_agent(client, "t", repo_tools(SAMPLE_REPO))
    cleared = ch10.clear_old_tool_results(result.messages, keep_last=2)
    contents = [b["content"] for m in cleared if isinstance(m["content"], list)
                for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_result"]
    assert contents[:3] == [ch10.CLEARED] * 3
    assert all(c != ch10.CLEARED for c in contents[3:])
    # original history is not mutated
    assert ch10.CLEARED not in str(result.messages)


def test_parallel_results_reach_the_model_before_clearing(load):
    ch10 = load("ch10-compaction/compaction.py")
    from fakes import Block, Response, Usage

    eight_reads = Response([Block("tool_use", id=f"r{i}", name="read_file", input={"path": "inventory/stats.py"})
                            for i in range(8)], "tool_use", Usage())
    client = FakeClient([eight_reads, text("done")])
    seen = []
    run_agent(client, "read everything", repo_tools(SAMPLE_REPO),
              hooks=Hooks(before_model=lambda m: seen.append(ch10.clear_old_tool_results(m, 1)) or seen[-1]))
    newest = seen[-1][-1]["content"]
    assert len(newest) == 8 and all(b["content"] != ch10.CLEARED for b in newest)


def test_compactor_summarises_and_keeps_pairs(load):
    ch10 = load("ch10-compaction/compaction.py")
    script = [tool("read_file", {"path": "inventory/stats.py"}) for _ in range(6)] + [text("done")]
    agent_client = FakeClient(script)
    summary_client = FakeClient([text("- task: review\n- read stats.py") for _ in range(10)])
    compactor = ch10.Compactor(summary_client, budget=1200, threshold=0.5, keep_recent=4, keep_tool_results=1)
    seen = []

    def hook(messages):
        out = compactor(messages)
        seen.append(out)
        return out

    run_agent(agent_client, "Review the repo", repo_tools(SAMPLE_REPO), hooks=Hooks(before_model=hook))
    assert compactor.compactions >= 1
    for messages in seen:
        assert _valid_alternation(messages)
        # every tool_result in the window has its tool_use in the previous message
        for i, m in enumerate(messages):
            if isinstance(m["content"], list) and m["content"] and isinstance(m["content"][0], dict) \
                    and m["content"][0].get("type") == "tool_result":
                assert messages[i - 1]["role"] == "assistant"
    assert "summary_of_earlier_work" in seen[-1][0]["content"]


def test_vector_search_finds_the_right_chunk(load):
    vs = load("ch11-retrieval/vector_search.py")
    chunks = vs.chunk_repo(SAMPLE_REPO)
    top = vs.search(chunks, "bulk discount tiers quantity", k=1)[0]
    assert top["source"].startswith("inventory/pricing.py")
    assert "Question:" in vs.build_prompt(chunks, "what is the mean?")


def test_retrieval_compare(load):
    cmp = load("ch11-retrieval/compare.py")
    client = FakeClient([text("rag answer"), tool("search_code", {"query": "bulk"}), text("agent answer")])
    rows = cmp.compare(client, questions=["What discount does 60 units get?"])
    assert rows[0]["rag"] == "rag answer" and rows[0]["agentic_turns"] == 2


def test_memory_store_commands(load, tmp_path):
    ch12 = load("ch12-memory/memory_tool.py")
    store = ch12.MemoryStore(tmp_path / "mem")
    assert "(empty)" in store.view()
    store.create("/memories/decisions.md", "- discounts capped at 50%\n")
    assert "decisions.md" in store.view()
    assert "Updated" in store.str_replace("/memories/decisions.md", "50%", "40%")
    assert "40%" in store.view("/memories/decisions.md")
    assert "must match exactly once" in store.str_replace("/memories/decisions.md", "zzz", "y")
    assert "unknown command" in store.run("_path", virtual="/memories")
    import pytest
    with pytest.raises(ValueError):
        store.view("/memories/../../etc")


def test_memory_persists_across_sessions(load, tmp_path):
    ch12 = load("ch12-memory/memory_tool.py")
    store = ch12.MemoryStore(tmp_path / "mem")
    s1 = FakeClient([tool("memory", {"command": "create", "path": "/memories/pricing.md",
                                     "file_text": "Discounts capped at 50%."}), text("saved")])
    ch12.run_session("remember", s1, store)
    s2 = FakeClient([tool("memory", {"command": "view", "path": "/memories/pricing.md"}), text("cap is 50%")])
    ch12.run_session("new session", s2, store)
    recalled = s2.messages.calls[-1]["messages"][-2]["content"][0]["content"]
    assert "capped at 50%" in recalled


def test_subagent_context_isolation(load):
    ch13 = load("ch13-subagents/subagents.py")
    client = FakeClient([
        tool("delegate", {"brief": "find callers of bulk_discount"}, input_tokens=300),
        tool("search_code", {"query": "bulk_discount"}, input_tokens=500),   # sub-agent turn 1
        text("order_total calls it at pricing.py:24", input_tokens=900),     # sub-agent turn 2
        text("One caller: order_total.", input_tokens=400),
    ])
    out = ch13.run("find callers", client)
    assert out["answer"] == "One caller: order_total."
    assert out["subagent_tokens"] == 1400 and out["main_window_tokens"] == 700
    orchestrator_messages = client.messages.calls[-1]["messages"]
    assert "pricing.py:24" in str(orchestrator_messages)          # report came back
    assert "def bulk_discount" not in str(orchestrator_messages)  # raw search output did not


def test_caching_breakpoints(load):
    ch14 = load("ch14-caching/caching.py")
    client = FakeClient([tool("list_files", cache_creation_input_tokens=2000),
                         text("done", cache_read_input_tokens=2000)])
    rows = ch14.run(client, cached=True)
    call = client.messages.calls[0]
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    assert rows[1]["cache_read"] == 2000
    assert ch14.relative_cost(rows) < sum(r["uncached_input"] + 2000 for r in rows)
