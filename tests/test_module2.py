import asyncio
from pathlib import Path

from fakes import FakeClient, text, tool

from course import SAMPLE_REPO, Hooks, run_agent


def test_good_tools_page_and_hint(load):
    good = load("ch05-tool-design/tools_good.py")
    out = good.search_code(SAMPLE_REPO, "def ", max_results=2)
    assert "offset=2" in out
    assert "Did you mean" in good.read_file(SAMPLE_REPO, "inventory/stat.py")
    assert "not a valid regular expression" in good.search_code(SAMPLE_REPO, "(")
    detailed = good.search_code(SAMPLE_REPO, "def mean", response_format="detailed")
    assert "Average of the values" in detailed  # context lines around the match


def test_bad_tools_dump_tracebacks(load):
    bad = load("ch05-tool-design/tools_bad.py")
    assert "Traceback" in bad.bad_tools(SAMPLE_REPO).call("get", {"p": "missing.py"})


def test_compare_runs_both_toolsets(load):
    cmp = load("ch05-tool-design/compare.py")
    client = FakeClient([tool("get", {"p": "inventory/pricing.py"}), text("10%"),
                         tool("search_code", {"query": "bulk"}), text("10%")])
    rows = cmp.compare(client)
    assert [r["tools"] for r in rows] == ["bad tools", "good tools"]


def test_mcp_server_lists_tools(load):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import sys

    server = Path(__file__).resolve().parents[1] / "ch06-mcp" / "server.py"

    async def go():
        params = StdioServerParameters(command=sys.executable, args=[str(server)])
        async with stdio_client(params) as (r, w):
            async with ClientSession(r, w) as session:
                await session.initialize()
                names = {t.name for t in (await session.list_tools()).tools}
                out = await session.call_tool("search_repo", {"query": "def mean"})
                return names, out.content[0].text

    names, found = asyncio.run(go())
    assert names == {"search_repo", "read_file"}
    assert "inventory/stats.py" in found


def test_instruction_layers(load, tmp_path):
    ch07 = load("ch07-instruction-files/instructions.py")
    prompt, sources = ch07.build_system_prompt(SAMPLE_REPO, user_file=tmp_path / "none.md")
    assert sources[0] == "harness base prompt"
    assert any("AGENTS.md" in s for s in sources)
    assert "pytest" in prompt


def test_nested_instruction_files_closest_last(load, sample_copy):
    ch07 = load("ch07-instruction-files/instructions.py")
    (sample_copy / "inventory" / "AGENTS.md").write_text("nested rules")
    files = ch07.find_project_files(sample_copy, sample_copy / "inventory")
    assert [f.parent.name for f in files] == ["sample-repo", "inventory"]


def test_skills_progressive_disclosure(load):
    ch08 = load("ch08-skills/skill_loader.py")
    skills = ch08.discover()
    assert "release-notes" in skills
    prompt = ch08.skills_prompt(skills)
    assert "Fixed" not in prompt  # body is not in the always-on prompt
    tools = {t.name: t for t in ch08.skill_tools(skills)}
    assert "**Fixed**" in tools["load_skill"].fn(name="release-notes")
    assert "vX.Y.Z" in tools["load_skill_file"].fn(name="release-notes", file="template.md")
    assert "not found" in tools["load_skill_file"].fn(name="release-notes", file="../../skill_loader.py")


def test_permission_hooks_and_modes(load, sample_copy):
    ch09 = load("ch09-permissions/permissions.py")
    toolbox, policy = ch09.build(sample_copy, mode="ask", approve=lambda n, a: False)
    assert "outside" in policy("write_file", {"path": "../evil.txt", "content": "x"})
    assert "secret" in policy("write_file", {"path": "a.txt", "content": "AKIAABCDEFGHIJKLMNOP"})
    assert "forbidden" in policy("run_command", {"command": "rm -rf /"})
    assert policy("read_file", {"path": "x"}) is None
    assert "Denied by the user" in policy("write_file", {"path": "a.txt", "content": "ok"})
    policy.mode = "auto"
    assert policy("write_file", {"path": "a.txt", "content": "ok"}) is None


def test_permission_policy_in_loop(load, sample_copy):
    ch09 = load("ch09-permissions/permissions.py")
    toolbox, policy = ch09.build(sample_copy, mode="allowlist")
    client = FakeClient([tool("write_file", {"path": "x.txt", "content": "hi"}), text("could not write")])
    run_agent(client, "write", toolbox, hooks=Hooks(before_tool=policy))
    assert not (sample_copy / "x.txt").exists()
