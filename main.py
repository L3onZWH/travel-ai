#!/usr/bin/env python3
"""Travel AI Agent — CLI 入口."""
from __future__ import annotations

import sys
from pathlib import Path

# 确保项目根目录在 sys.path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from agent.core import TravelAgent
from agent.rules import RulesEngine
from agent.session import SessionManager
from agent.workspace import WorkspaceManager
from config.settings import settings

console = Console()

# ────────────────────────────────────────────────────────────────────────── #
# Banner & styling                                                           #
# ────────────────────────────────────────────────────────────────────────── #
BANNER = """\
[bold cyan]
  🌍  Travel AI Agent  v0.4
  智能旅行规划助手
[/bold cyan]
[dim]  基于 Claude · 多模型支持 · Workspace 隔离[/dim]"""

HELP_TEXT = """\
## 可用命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/rules` | 查看当前规则（rule.md + soul.md）|
| `/save` | 显示当前会话保存路径 |
| `/history` | 列出当前 Workspace 历史对话 |
| `/load <id>` | 加载指定历史对话 |
| `/workspace` | 显示 / 切换 Workspace（`/workspace <名称>`）|
| `/session` | 显示当前 Session 信息 |
| `/clear` | 清空本次对话历史 |
| `/exit` | 退出（或 Ctrl+C）|
"""


# ────────────────────────────────────────────────────────────────────────── #
# Helpers                                                                    #
# ────────────────────────────────────────────────────────────────────────── #
def print_banner() -> None:
    console.print()
    console.print(Panel(BANNER, border_style="cyan", expand=False, padding=(0, 2)))
    console.print()


def print_assistant(text: str) -> None:
    console.print(Text("✦ 旅行家", style="bold green"))
    console.print(Markdown(text))
    console.print()


def make_prompt_label(ws_name: str) -> str:
    return f"[bold blue]You[/bold blue] [dim]({ws_name})[/dim]"


# ──────────────────────────────────────────────────────────────────────── #
# Command handlers                                                           #
# ──────────────────────────────────────────────────────────────────────── #
class State:
    """可变的 CLI 状态，贯穿命令循环。"""
    def __init__(self, agent: TravelAgent, workspace: WorkspaceManager) -> None:
        self.agent = agent
        self.workspace = workspace
        self.running = True
        self.reload: TravelAgent | None = None


def cmd_exit(state: State, _args: str) -> None:
    console.print("\n[dim]再见，祝您旅途愉快！🛫[/dim]\n")
    state.running = False


def cmd_help(_state: State, _args: str) -> None:
    console.print(Markdown(HELP_TEXT))


def cmd_clear(state: State, _args: str) -> None:
    state.agent.clear_history()
    console.print("[yellow]✓ 对话历史已清空[/yellow]")


def cmd_rules(_state: State, _args: str) -> None:
    engine = RulesEngine()
    rules = engine.load()
    soul = engine.load_soul()
    parts: list[str] = []
    if rules:
        parts.append(f"**rule.md**\n```\n{rules}\n```")
    if soul:
        parts.append(f"**soul.md**\n```\n{soul}\n```")
    if parts:
        console.print(Markdown("\n\n".join(parts)))
    else:
        console.print("[dim]配置文件为空（config/rule.md 和 config/soul.md）[/dim]")


def cmd_save(state: State, _args: str) -> None:
    path = state.agent.get_save_path()
    console.print(f"[green]✓ 已自动保存至:[/green]\n  [dim]{path}[/dim]")


def cmd_session(state: State, _args: str) -> None:
    agent = state.agent
    console.print(
        f"[bold]Workspace:[/bold]  {agent.workspace.name}\n"
        f"[bold]Session ID:[/bold] {agent.session_id}\n"
        f"[bold]保存路径:[/bold]   {agent.get_save_path()}"
    )


def cmd_history(state: State, _args: str) -> None:
    sm = SessionManager(state.workspace)
    sessions = sm.list_sessions(limit=15)
    if not sessions:
        console.print("[dim]当前 Workspace 下暂无历史对话[/dim]")
        return

    table = Table(
        title=f"Workspace [{state.workspace.name}] 历史对话",
        show_lines=False,
        header_style="bold",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Session ID", style="cyan", width=14)
    table.add_column("标题", style="white")
    table.add_column("消息数", justify="right", style="dim", width=6)
    table.add_column("创建时间", style="dim", width=19)

    for i, s in enumerate(sessions, 1):
        is_current = s.session_id == state.agent.session_id
        idx = f"[bold green]► {i}[/bold green]" if is_current else f"  {i}"
        table.add_row(
            idx,
            s.short_id,
            s.title or "[dim](无标题)[/dim]",
            str(s.message_count),
            s.created_at[:16] if s.created_at else "",
        )
    console.print(table)
    console.print("[dim]提示：/load <ID前12位> 加载对话[/dim]")


def cmd_load(state: State, args: str) -> None:
    prefix = args.strip()
    if not prefix:
        console.print("[red]用法：/load <session_id>[/red]")
        return

    sm = SessionManager(state.workspace)
    matched = [s for s in sm.list_sessions() if s.session_id.startswith(prefix)]

    if not matched:
        console.print(f"[red]未找到匹配的 Session：{prefix}[/red]")
        return
    if len(matched) > 1:
        console.print(f"[yellow]匹配到 {len(matched)} 个 Session，请提供更长的 ID[/yellow]")
        return

    target = matched[0]
    new_agent = TravelAgent(session_id=target.session_id, workspace=state.workspace)
    state.agent = new_agent
    state.reload = new_agent
    console.print(
        f"[green]✓ 已加载 Session [{target.short_id}][/green]"
        f"  消息数: {target.message_count}  标题: {target.display_name or '(无标题)'}"
    )


def cmd_workspace(state: State, args: str) -> None:
    name = args.strip()
    if not name:
        workspaces = WorkspaceManager.list_all() or [state.workspace.name]
        cur = state.workspace.name
        lines = [(f"[bold green]► {w}[/bold green]" if w == cur else f"  {w}") for w in workspaces]
        console.print(Panel("\n".join(lines), title="Workspaces", border_style="dim"))
        console.print("[dim]提示：/workspace <名称> 切换[/dim]")
        return

    new_ws = WorkspaceManager.create(name)
    if new_ws.name == state.workspace.name:
        console.print(f"[dim]已在 Workspace [{new_ws.name}] 中[/dim]")
        return

    state.workspace = new_ws
    new_agent = TravelAgent(workspace=new_ws)
    state.agent = new_agent
    state.reload = new_agent
    console.print(f"[green]✓ 已切换到 Workspace [{new_ws.name}]，开始新对话[/green]")


COMMANDS: dict = {
    "/exit": cmd_exit, "/quit": cmd_exit, "/q": cmd_exit,
    "/help": cmd_help, "/h": cmd_help,
    "/clear": cmd_clear,
    "/rules": cmd_rules,
    "/save": cmd_save,
    "/session": cmd_session,
    "/history": cmd_history,
    "/load": cmd_load,
    "/workspace": cmd_workspace,
}


def handle_command(raw: str, state: State) -> None:
    parts = raw.strip().split(maxsplit=1)
    token = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    handler = COMMANDS.get(token)
    if handler is None:
        console.print(f"[red]未知命令: {token}，输入 /help 查看帮助[/red]")
        return
    handler(state, args)


# ────────────────────────────────────────────────────────────────────────── #
# Chat loop                                                                  #
# ────────────────────────────────────────────────────────────────────────── #
def chat_loop(state: State) -> None:
    console.print(Rule(style="dim"))
    console.print("[dim]输入旅游问题开始对话 · /help 查看命令 · Ctrl+C 退出[/dim]\n")

    while state.running:
        if state.reload is not None:
            state.reload = None

        try:
            user_input = Prompt.ask(make_prompt_label(state.workspace.name)).strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]再见！🛫[/dim]\n")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            handle_command(user_input, state)
            continue

        console.print()
        console.print("[bold green]✦ 旅行家[/bold green] [dim]思考中…[/dim]")
        try:
            chunks: list[str] = []
            for chunk in state.agent.stream(user_input):
                chunks.append(chunk)
            console.print("\r", end="")
            print_assistant("".join(chunks))
        except KeyboardInterrupt:
            console.print("\n[yellow]已中断[/yellow]\n")
        except Exception as exc:  # noqa: BLE001
            console.print(f"\n[red]错误: {exc}[/red]\n")


# ────────────────────────────────────────────────────────────────────────── #
# Entry point                                                                #
# ────────────────────────────────────────────────────────────────────────── #
def main() -> None:
    settings.ensure_dirs()
    print_banner()

    if not settings.anthropic_api_key:
        console.print(
            Panel(
                "[red]⚠ 未设置 ANTHROPIC_API_KEY[/red]\n\n"
                "请将 [bold].env.example[/bold] 复制为 [bold].env[/bold]，填写 API Key 后重试。",
                title="配置错误", border_style="red", expand=False,
            )
        )
        sys.exit(1)

    workspace = WorkspaceManager.create(WorkspaceManager.DEFAULT)
    agent = TravelAgent(workspace=workspace)
    state = State(agent=agent, workspace=workspace)

    console.print(
        f"[dim]Workspace: {workspace.name}  ·  Session: {agent.session_id}[/dim]\n"
    )
    print_assistant(
        "你好！我是你的 AI 旅行顾问「旅行家」🌏\n\n"
        "请告诉我你想去哪里旅行？大概的预算和时间是？"
    )
    chat_loop(state)


if __name__ == "__main__":
    main()
