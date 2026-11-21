from fakes import FakeClient, text, tool


def _harness(load, sample_copy, tmp_path, script, auto=True, approve=None):
    mh = load("ch19-mini-harness/mini_harness.py")
    cfg = mh.Config(repo=sample_copy, state_dir=tmp_path / "state", auto_approve=auto)
    client = FakeClient(script)
    return mh, mh.Harness(cfg, client=client, approve=approve), client


def test_mini_harness_fixes_bug_end_to_end(load, sample_copy, tmp_path):
    fixed = (sample_copy / "inventory" / "stats.py").read_text().replace("len(values) - 1", "len(values)")
    mh, h, client = _harness(load, sample_copy, tmp_path, [
        tool("memory_view"),
        tool("search_code", {"query": "def mean"}),
        tool("write_file", {"path": "inventory/stats.py", "content": fixed}),
        tool("run_tests"),
        text("Fixed mean(); 5 passed."),
    ])
    assert h.run("Fix the failing test") == "Fixed mean(); 5 passed."
    assert "len(values))" in (sample_copy / "inventory" / "stats.py").read_text()
    call = client.messages.calls[0]
    assert "AGENTS.md" in call["system"][0]["text"] and call["system"][0]["cache_control"]
    assert call["tools"][-1]["cache_control"] == {"type": "ephemeral"}
    assert "5 passed" in (tmp_path / "state" / "progress.md").read_text() or "Fixed" in \
        (tmp_path / "state" / "progress.md").read_text()
    events = [line for line in h.trace_path.read_text().splitlines()]
    assert len(events) == 9  # 5 turns + 4 tool calls
    assert h.stats["turns"] == 5 and h.stats["tools"]["write_file"] == 1 and h.stats["asked"] == 2
    assert "permissions: 2 asked" in mh.summary(h)


def test_mini_harness_permission_denied(load, sample_copy, tmp_path):
    mh, h, client = _harness(load, sample_copy, tmp_path, [
        tool("write_file", {"path": "new.txt", "content": "x"}), text("ok")], auto=False,
        approve=lambda n, a: False)
    h.run("write a file")
    assert not (sample_copy / "new.txt").exists()


def test_mini_harness_blocks_escape_and_secrets(load, sample_copy, tmp_path):
    mh, h, _ = _harness(load, sample_copy, tmp_path, [])
    assert "outside" in h.tools.call("write_file", {"path": "../x.txt", "content": "x"})
    assert "secret" in h.permit("write_file", {"path": "a", "content": "key AKIAABCDEFGHIJKLMNOP"})


def test_mini_harness_subagent_is_read_only(load, sample_copy, tmp_path):
    mh, h, client = _harness(load, sample_copy, tmp_path, [
        tool("delegate", {"brief": "summarise pricing.py"}),
        tool("read_file", {"path": "inventory/pricing.py"}),   # sub-agent
        text("pricing has tiers"),                              # sub-agent report
        text("Pricing uses tiers."),
    ])
    assert h.run("explain pricing") == "Pricing uses tiers."
    sub_tools = {t["name"] for t in client.messages.calls[1]["tools"]}
    assert "write_file" not in sub_tools and "delegate" not in sub_tools


def test_mini_harness_compacts(load, sample_copy, tmp_path):
    script = [tool("read_file", {"path": "inventory/stock.py"}) for _ in range(8)] + [text("done")]
    mh, h, client = _harness(load, sample_copy, tmp_path, script)
    agent_create = client.messages.create

    def routed(**kwargs):  # summary requests carry no tools; answer them separately
        if "tools" not in kwargs:
            return text("summary of work")
        return agent_create(**kwargs)

    client.messages.create = routed
    h.cfg.budget_tokens = 600
    h.cfg.keep_tool_results = 1
    assert h.run("read a lot") == "done"
    assert "compaction" in h.trace_path.read_text()


def test_checklist_exists():
    from pathlib import Path

    text_ = (Path(__file__).resolve().parents[1] / "ch20-design-review" / "harness-design-checklist.md").read_text()
    assert text_.count("- [ ]") >= 25
