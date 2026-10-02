"""
Logging utility module with rich formatting support and Windows console safety.
"""

from rich.console import Console

console = Console(highlight=False)
console_err = Console(stderr=True, highlight=False)

def log_info(msg: str):
    console.print(f"[bold cyan][*][/bold cyan] {msg}")

def log_success(msg: str):
    console.print(f"[bold green][+][/bold green] {msg}")

def log_warning(msg: str):
    console.print(f"[bold yellow][!][/bold yellow] {msg}")

def log_error(msg: str):
    console_err.print(f"[bold red][ERROR][/bold red] {msg}")

def log_progress(step: int, total: int, msg: str):
    console.print(f"[bold blue][{step:02d}/{total:02d}][/bold blue] {msg}")
