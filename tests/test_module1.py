from fakes import FakeClient, text, tool

from course import Hooks, SAMPLE_REPO, Toolbox, repo_tools, run_agent
from course.tools import read_file, safe_path


def test_bare_call_sends_no_tools(load):
    ch01 = load("ch01-what-is-a-harness/bare_call.py")
    client = FakeClient([text("I can't see your code.")])
    assert "can't see" in ch01.bare_call(client)
    assert "tools" not in client.messages.calls[0]


def test_ch02_loop_runs_tools_until_done(load):
    ch02 = load("ch02-agent-loop/loop.py")
    client = FakeClient([
        tool("list_files"),
        tool("read_file", {"path": "inventory/stats.py"}),
        text("mean() divides by len - 1."),
    ])
    assert ch02.agent("find the bug", client) == "mean() divides by len - 1."
    final_messages = client.messages.calls[-1]["messages"]
    tool_result = final_messages[-2]["content"][0]["content"]  # last item is the final assistant reply
    assert "len(values) - 1" in tool_result


def test_ch02_blocks_paths_outside_repo(load):
    ch02 = load("ch02-agent-loop/loop.py")
    assert "outside" in ch02.run_tool("read_file", {"path": "../README.md"})


def test_ch02_stops_at_max_turns(load):
    ch02 = load("ch02-agent-loop/loop.py")
    client = FakeClient([tool("list_files"), tool("list_files")])
    assert ch02.agent("loop forever", client, max_turns=2).startswith("Stopped")


def test_course_loop_and_hooks():
    seen = []
    client = FakeClient([tool("read_file", {"path": "inventory/stats.py"}), text("done")])
    result = run_agent(client, "task", repo_tools(SAMPLE_REPO), hooks=Hooks(after_turn=lambda t, r, m: seen.append(t)))
    assert result.text == "done" and result.turns == 2 and seen == [1, 2]
    assert result.input_tokens == 200


def test_before_tool_hook_blocks_call():
    client = FakeClient([tool("read_file", {"path": "inventory/stats.py"}), text("ok")])
    result = run_agent(client, "t", repo_tools(SAMPLE_REPO), hooks=Hooks(before_tool=lambda n, a: "Blocked by policy"))
    blocked = result.messages[2]["content"][0]
    assert blocked["is_error"] and blocked["content"] == "Blocked by policy"


def test_toolbox_reports_unknown_tool_and_paging():
    assert "unknown tool" in Toolbox().call("nope", {})
    out = read_file(SAMPLE_REPO, "inventory/stats.py", max_lines=3)
    assert "call again with start_line=4" in out


def test_safe_path_rejects_escape():
    import pytest

    with pytest.raises(ValueError):
        safe_path(SAMPLE_REPO, "../../etc/passwd")


def test_token_budget_report(load):
    ch03 = load("ch03-context-window/token_budget.py")
    client = FakeClient([tool("list_files", input_tokens=900), text("summary", input_tokens=1500)])
    rows = ch03.run("explain", client)
    assert [r["turn"] for r in rows] == [1, 2]
    assert rows[1]["conversation"] > rows[0]["conversation"]
    assert "Total input tokens" in ch03.report(rows)


def test_context_map_offline(load):
    ch04 = load("ch04-context-engineering/context_map.py")
    inputs = ch04.build_inputs()
    assert len(inputs) == 6
    out = ch04.render({k: ch04.estimate(v) for k, v in inputs.items()})
    assert "Total" in out
