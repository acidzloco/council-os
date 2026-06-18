"""
Council Agent CLI
Tool-using brothers in your terminal.

Usage:
    python council_agent.py                        # interactive, default brother = byte
    python council_agent.py --brother deepseek     # pick brother
    python council_agent.py --task "review C:\\AI\\council_v3\\council_v3_bridge.py"
"""
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.markdown import Markdown
    from rich.rule import Rule
    from rich.text import Text
    _RICH = True
except ImportError:
    _RICH = False

from council_v3_bridge import _native_call, BROTHERS
from agent_loop import run_agent

console = Console() if _RICH else None

BROTHER_COLORS = {
    "byte":     "bold red",
    "deepseek": "bold cyan",
    "gemini":   "bold green",
}

BROTHER_TAGLINE = {
    "byte":     "Offensive security · systems · kernel · MQL5",
    "deepseek": "Research · algorithms · math · deep reasoning",
    "gemini":   "Integration · pipelines · architecture · systems",
}


def _print(msg: str, style: str = ""):
    if _RICH and console:
        console.print(msg, style=style)
    else:
        print(msg)


def _panel(content: str, title: str = "", border: str = "white"):
    if _RICH and console:
        try:
            console.print(Panel(Markdown(content), title=title, border_style=border))
        except Exception:
            console.print(Panel(content, title=title, border_style=border))
    else:
        print(f"\n--- {title} ---\n{content}\n")


def _rule(title: str = "", style: str = "dim"):
    if _RICH and console:
        console.print(Rule(title, style=style))
    else:
        print(f"\n{'='*40} {title} {'='*40}")


def run_session(name: str, task: str, cwd: str = "."):
    color = BROTHER_COLORS.get(name, "white")
    role  = BROTHERS[name]["role"]

    step_counts = {"tools": 0}

    def on_step(step_type: str, content: str):
        if step_type == "think":
            if content.strip():
                _print(f"[dim][{name.upper()} thinking][/dim] {content}", style="")
        elif step_type == "tool":
            step_counts["tools"] += 1
            if _RICH and console:
                console.print(f"  [yellow]⚙ tool call:[/yellow] {content}")
            else:
                print(f"  [tool] {content}")
        elif step_type == "result":
            if _RICH and console:
                console.print(f"  [dim]→ {content}[/dim]")
            else:
                print(f"  [result] {content}")
        elif step_type == "final":
            _rule(f"{name.upper()} RESULT ({step_counts['tools']} tool calls)", style=color.replace("bold ", ""))
            _panel(content, title=name.upper(), border=color.replace("bold ", ""))
        elif step_type == "error":
            if _RICH and console:
                console.print(f"[red][error][/red] {content}")
            else:
                print(f"[error] {content}")

    def call_fn(system: str, user: str, max_tokens: int) -> str:
        return _native_call(name, system, user, max_tokens)

    run_agent(
        brother_name  = name,
        task          = task,
        native_call_fn= call_fn,
        brother_role  = role,
        on_step       = on_step,
        cwd           = cwd,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Council Agent CLI — tool-using brothers in your terminal"
    )
    parser.add_argument(
        "--brother", "-b",
        default = "byte",
        choices = list(BROTHERS.keys()),
        help    = "Which brother handles this session (default: byte)",
    )
    parser.add_argument(
        "--task", "-t",
        help = "One-shot task string (skips interactive mode)",
    )
    parser.add_argument(
        "--cwd", "-d",
        default = str(Path.cwd()),
        help    = "Working directory context for the agent",
    )
    args = parser.parse_args()

    name  = args.brother
    color = BROTHER_COLORS.get(name, "white").replace("bold ", "")

    if _RICH and console:
        console.print(Panel(
            f"[{color}]{name.upper()}[/{color}] — [bold]AGENT MODE[/bold]\n"
            f"[dim]{BROTHER_TAGLINE.get(name, '')}[/dim]\n\n"
            f"[dim]cwd: {args.cwd}[/dim]\n"
            f"[dim]Type your task. 'exit' to quit.[/dim]",
            title="⚙  COUNCIL AGENT",
            border_style=color,
        ))
    else:
        print(f"\n=== COUNCIL AGENT — {name.upper()} ===")
        print(f"cwd: {args.cwd}")
        print("Type your task. 'exit' to quit.\n")

    # One-shot mode
    if args.task:
        run_session(name, args.task, args.cwd)
        return

    # Interactive REPL
    while True:
        try:
            if _RICH and console:
                task = Prompt.ask(f"\n[{color}]❯ {name.upper()}[/{color}]")
            else:
                task = input(f"\n{name.upper()} ❯ ").strip()
        except (KeyboardInterrupt, EOFError):
            _print("\n[dim]Shutting down.[/dim]")
            break

        task = task.strip()
        if not task:
            continue
        if task.lower() in ("exit", "quit", "q", ":q"):
            _print("[dim]Bye.[/dim]")
            break

        # Allow switching brother mid-session
        if task.lower().startswith("switch "):
            new_name = task.split()[1].lower()
            if new_name in BROTHERS:
                name  = new_name
                color = BROTHER_COLORS.get(name, "white").replace("bold ", "")
                _print(f"[dim]Switched to {name.upper()}[/dim]")
            else:
                _print(f"[red]Unknown brother: {new_name}[/red]")
            continue

        run_session(name, task, args.cwd)


if __name__ == "__main__":
    main()
