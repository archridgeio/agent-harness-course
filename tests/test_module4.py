import json

from fakes import FakeClient, text, tool

from course import SAMPLE_REPO, Hooks, repo_tools, run_agent


def tool_results(messages):
    """Every tool_result content string in a conversation, in order."""
    return [b["content"] for m in messages if m["role"] == "user" and isinstance(m["content"], list)
            for b in m["content"] if isinstance(b, dict) and b.get("type") == "tool_result"]


def test_long_task_initializer_and_resume(load, tmp_path, monkeypatch):
    ch15 = load("ch15-long-horizon/long_task.py")
    monkeypatch.setattr(ch15, "WORKSPACE", tmp_path / "ws")
    feats = [{"id": "F1", "description": "fix mean", "passes": False},
             {"id": "F2", "description": "clearance", "passes": False}]
    fixed_stats = (SAMPLE_REPO / "inventory" / "stats.py").read_text().replace("len(values) - 1", "len(values)")
    client = FakeClient([
        tool("write_file", {"path": "features.json", "content": json.dumps(feats)}),
        tool("write_file", {"path": "progress.md", "content": "# Progress\n## Log\n"}),
        text("initialized"),
        # session 1: fix F1 and mark it
        tool("write_file", {"path": "inventory/stats.py", "content": fixed_stats}),
        tool("run_tests"),
        tool("write_file", {"path": "features.json",
                            "content": json.dumps([dict(feats[0], passes=True), feats[1]])}),
        text("F1 done"),
    ])
    log = ch15.run(client, max_sessions=1, reset=True)
    assert log[0]["remaining"] == 2 and log[1]["remaining"] == 1
    assert "session 1: F1" in ch15.git("log", "--oneline")
    tests_output = tool_results(client.messages.calls[5]["messages"])[1]  # write_file, then run_tests
    assert "passed" in tests_output and "failed" not in tests_output
    # resume: a new run with no work left for F1 targets F2
    client2 = FakeClient([text("looked at F2")])
    log2 = ch15.run(client2, max_sessions=1)
    assert log2[0]["target"] == "F2" and log2[0]["session"] == 2
    assert "session 2: F2" in ch15.git("log", "-1", "--oneline")
    # --stop-after 0 runs no worker session
    assert ch15.run(FakeClient([]), stop_after=0) == []


def test_multi_agent_fans_out(load):
    ch16 = load("ch16-multi-agent/single_vs_multi.py")
    mods = ch16.modules()
    assert mods == ["inventory/pricing.py", "inventory/stats.py", "inventory/stock.py"]
    client = FakeClient([text(f"review {i}") for i in range(len(mods))] + [text("combined report")])
    out = ch16.multi(client, parallel=False)
    assert out["agents"] == 4 and out["report"] == "combined report"
    assert out["model_calls"] == 4 and [r["name"] for r in out["rows"]][-1] == "synthesizer"


def test_tracer_records_turns_and_tools(load, tmp_path):
    tr = load("ch17-evals-tracing/tracing.py")
    view = load("ch17-evals-tracing/view_trace.py")
    tracer = tr.Tracer(tmp_path / "t.jsonl")
    client = FakeClient([tool("read_file", {"path": "inventory/stats.py"}), text("done")])
    run_agent(client, "t", tracer.wrap(repo_tools(SAMPLE_REPO)), hooks=Hooks(after_turn=tracer.after_turn))
    events = tr.load(tmp_path / "t.jsonl")
    assert [e["event"] for e in events] == ["model_turn", "tool_call", "model_turn"]
    assert "Biggest tool output: read_file" in view.summarize(events)


def test_eval_grading_and_variants(load, tmp_path, monkeypatch):
    ev = load("ch17-evals-tracing/run_evals.py")
    monkeypatch.setattr(ev, "HERE", tmp_path)
    assert "search_code" not in ev.variant_tools("no-search").tools
    task = {"id": "bulk-60", "question": "q", "must_contain": ["10%"]}
    client = FakeClient([text("It gets 10%.")])
    report = ev.run("full", client, tasks=[task])
    assert report["passed"] == 1


def test_injection_canary_blocked_when_fixed(load):
    ch18 = load("ch18-failure-modes/failures.py")
    attack = [tool("read_file", {"path": "CONTRIBUTING.md"}),
              tool("write_file", {"path": "INJECTED.txt", "content": "pwned"}), text("summary")]
    broken = ch18.injection(False, FakeClient(list(attack)))
    fixed_client = FakeClient(list(attack))
    fixed = ch18.injection(True, fixed_client)
    assert broken["signal"] == "INJECTED.txt written!"
    assert fixed["signal"] == "no injected file"
    first_result = tool_results(fixed_client.messages.calls[-1]["messages"])[0]
    assert first_result.startswith("<untrusted_data>")


def test_confusion_adds_decoy_tools(load):
    ch18 = load("ch18-failure-modes/failures.py")
    client = FakeClient([tool("read_file_v3", {"path": "inventory/stats.py"}), text("unknown")])
    out = ch18.confusion(False, client)
    assert len(client.messages.calls[0]["tools"]) == 43
    assert "read_file_v3" in out["signal"]
