"""
OmniMedia CLI Interface.
Command-line tool to extract photos, audio, and videos from social media links.
"""

import os
import sys
import subprocess
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn

from media_extractor.core.models import MediaFilter, MediaQuality
from media_extractor.core.config import get_config, save_config
from media_extractor.core.ffmpeg_finder import find_ffmpeg, get_ffmpeg_version
from media_extractor.extractors.manager import ExtractorManager
from media_extractor.utils.logger import log_info, log_success, log_error, log_warning
from media_extractor.utils.file_utils import format_bytes


console = Console(highlight=False, legacy_windows=False)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("url", required=False)
@click.option("-o", "--output-dir", help="Destination folder to save media. Defaults to ~/Downloads/OmniMedia or last configured path.", type=click.Path(file_okay=False, dir_okay=True))
@click.option("-f", "--format", "media_filter", type=click.Choice(["all", "images", "videos", "audio"], case_sensitive=False), default="all", help="Media filter: all, images, videos, audio.")
@click.option("-q", "--quality", type=click.Choice(["best", "high", "medium"], case_sensitive=False), default="best", help="Quality tier (default: best).")
@click.option("--subfolder/--no-subfolder", default=None, help="Organize output into profile/author subfolders.")
@click.option("--open-folder", is_flag=True, help="Open destination folder in Explorer after completion.")
@click.option("--gui", is_flag=True, help="Launch Desktop Graphical User Interface (PySide6).")
@click.option("--status", is_flag=True, help="Display system diagnostics (FFmpeg status, default directories).")
@click.option("--history", is_flag=True, help="Display past extraction audit logs, successes, and failures.")
def main(url, output_dir, media_filter, quality, subfolder, open_folder, gui, status, history):
    """
    OmniMedia Extractor - Download high-quality media from social media links.

    Examples:\n
      omni-media "https://www.instagram.com/p/DdoWS1KCGwA/" -o "D:/MyPhotos"\n
      omni-media "https://youtu.be/dQw4w9WgXcQ" -f audio -o "D:/Music"\n
      omni-media --history\n
      omni-media --gui
    """
    config = get_config()

    if gui:
        from media_extractor.ui.gui_pyside import launch_gui
        launch_gui()
        return

    if status:
        show_status(config)
        return

    if history:
        show_history()
        return

    if not url:
        console.print(Panel.fit(
            "[bold cyan]OmniMedia - Universal Social Media Media Extractor[/bold cyan]\n"
            "[white]Paste any social media post URL to extract images, audio, and videos in high quality.[/white]\n\n"
            "[yellow]Usage:[/yellow] [green]omni-media <URL> [OPTIONS][/green]\n"
            "[yellow]GUI Mode:[/yellow] [green]omni-media --gui[/green]\n"
            "[yellow]Help:[/yellow]     [green]omni-media --help[/green]",
            border_style="cyan"
        ))
        url = click.prompt("\n[?] Enter social media post URL", type=str)
        if not url.strip():
            console.print("[red]No URL provided. Exiting.[/red]")
            return

    # Determine output folder
    if not output_dir:
        output_dir = config.default_output_dir
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    if subfolder is not None:
        config.create_author_subfolder = subfolder

    filter_enum = MediaFilter(media_filter.lower())
    quality_enum = MediaQuality(quality.lower())

    console.print(Panel(
        f"[bold]Target URL:[/bold] {url}\n"
        f"[bold]Output Folder:[/bold] {output_dir}\n"
        f"[bold]Media Filter:[/bold] {filter_enum.value.capitalize()}\n"
        f"[bold]Quality:[/bold] {quality_enum.value.capitalize()}",
        title="[bold green]Download Configuration[/bold green]",
        border_style="green"
    ))

    manager = ExtractorManager(config)

    with Progress(
        TextColumn("[cyan]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing link and extracting media...", total=100)

        def progress_cb(step: int, total: int, msg: str):
            progress.update(task, description=f"[cyan]{msg}", completed=step)

        result = manager.extract(
            url=url,
            output_dir=output_dir,
            media_filter=filter_enum,
            quality=quality_enum,
            progress_cb=progress_cb,
        )
        progress.update(task, completed=100, description="[bold green]Completed!")

    if result.success and result.downloaded_files:
        table = Table(title="Downloaded Media Files", show_header=True, header_style="bold magenta")
        table.add_column("File Name", style="white")
        table.add_column("File Size", justify="right", style="cyan")
        table.add_column("Location", style="dim")

        total_bytes = 0
        for fpath in result.downloaded_files:
            fname = os.path.basename(fpath)
            size_str = "Unknown"
            if os.path.exists(fpath):
                sb = os.path.getsize(fpath)
                total_bytes += sb
                size_str = format_bytes(sb)
            table.add_row(fname, size_str, os.path.dirname(fpath))

        console.print(table)
        console.print(f"\n[bold green]SUCCESS:[/bold green] Exported {len(result.downloaded_files)} file(s) ({format_bytes(total_bytes)}) to:")
        console.print(f"Directory: [bold underline]{result.target_dir}[/bold underline]")

        if result.metadata_file:
            console.print(f"Metadata: [dim]{result.metadata_file}[/dim]")

        if open_folder:
            open_in_explorer(result.target_dir)

    elif result.success and not result.downloaded_files:
        log_warning("Extraction finished successfully but no media matched the selected filter.")
    else:
        log_error(f"Extraction failed: {result.error_message or 'Unknown error'}")


def show_status(config):
    """Displays system diagnostics."""
    ffmpeg = find_ffmpeg()
    version = get_ffmpeg_version(ffmpeg) if ffmpeg else "Not installed"

    t = Table(title="OmniMedia System Status", show_header=True, header_style="bold cyan")
    t.add_column("Property", style="bold")
    t.add_column("Value", style="green")

    t.add_row("Default Save Directory", config.default_output_dir)
    t.add_row("Create Subfolder", str(config.create_author_subfolder))
    t.add_row("Convert WebP to JPG", str(config.convert_webp_to_jpg))
    t.add_row("FFmpeg Binary Path", ffmpeg or "Not found")
    t.add_row("FFmpeg Version", version or "Unknown")
    console.print(t)


def show_history():
    """Displays past extraction history, successes, and failures."""
    from media_extractor.core.history import get_history_tracker
    tracker = get_history_tracker()
    stats = tracker.get_stats()
    records = tracker.get_all()

    # KPI summary table
    summary = Table(title="OmniMedia Audit Summary", show_header=True, header_style="bold magenta")
    summary.add_column("Total Runs", justify="center")
    summary.add_column("Successes", justify="center", style="green")
    summary.add_column("Failures", justify="center", style="red")
    summary.add_column("Success Rate", justify="center", style="cyan")
    summary.add_column("Total Files", justify="center")
    summary.add_column("Total Data", justify="center", style="yellow")

    summary.add_row(
        str(stats["total_runs"]),
        str(stats["success_count"]),
        str(stats["failed_count"]),
        f"{stats['success_rate_percent']}%",
        str(stats["total_files_downloaded"]),
        format_bytes(stats["total_bytes_downloaded"]),
    )
    console.print(summary)
    console.print("")

    if not records:
        console.print("[dim]No extraction events logged yet.[/dim]")
        return

    hist_table = Table(title=f"Recent Extractions (Last {min(len(records), 25)})", show_header=True, header_style="bold cyan")
    hist_table.add_column("Status", justify="center")
    hist_table.add_column("Timestamp", style="dim")
    hist_table.add_column("Platform", style="bold")
    hist_table.add_column("Files", justify="right")
    hist_table.add_column("Duration", justify="right")
    hist_table.add_column("Details", style="white")

    for r in records[:25]:
        st_val = r.get("status", "UNKNOWN")
        st_styled = f"[green]SUCCESS[/green]" if st_val == "SUCCESS" else (f"[red]FAILED[/red]" if st_val == "FAILED" else f"[yellow]{st_val}[/yellow]")
        detail = r.get("error_message") or r.get("url", "")
        if len(detail) > 60:
            detail = detail[:57] + "..."
        hist_table.add_row(
            st_styled,
            r.get("timestamp", ""),
            r.get("platform", ""),
            str(r.get("total_files", 0)),
            f"{r.get('duration_seconds', 0)}s",
            detail,
        )
    console.print(hist_table)


def open_in_explorer(path: str):
    """Opens directory in native OS file explorer."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception as e:
        log_warning(f"Could not open explorer: {e}")


if __name__ == "__main__":
    main()
