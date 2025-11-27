"""
CLI Commands for Suno API Client
"""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax
from rich import print as rprint
from pathlib import Path
import time
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_api_key, ensure_downloads_dir, AVAILABLE_MODELS, DEFAULT_MODEL
from src.api.client import SunoAPI
from src.api.models import Model, TaskStatusEnum, SeparationType, VocalGender
from src.api.exceptions import SunoAPIError, TaskTimeoutError, TaskFailedError

console = Console()


def get_api() -> SunoAPI:
    """Get configured API client"""
    try:
        api_key = get_api_key()
        return SunoAPI(api_key)
    except FileNotFoundError:
        console.print("[red]Error:[/red] API key file (key.txt) not found!")
        console.print("Please create key.txt in the project root with your API key.")
        raise click.Abort()
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


def format_duration(seconds: float) -> str:
    """Format duration in MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def wait_with_progress(api: SunoAPI, task_id: str, task_type: str = "Generation"):
    """Wait for task with progress display"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[cyan]{task.fields[status]}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"[yellow]{task_type}...",
            total=None,
            status="Starting..."
        )
        
        start_time = time.time()
        
        while True:
            status = api.get_task_status(task_id)
            elapsed = int(time.time() - start_time)
            
            progress.update(
                task,
                status=f"{status.status.value} ({elapsed}s)"
            )
            
            if status.is_complete:
                progress.update(task, description=f"[green]✓ {task_type} Complete!")
                return status
            elif status.is_failed:
                progress.update(task, description=f"[red]✗ {task_type} Failed!")
                raise TaskFailedError(status.error_message)
            
            time.sleep(10)  # Check every 10 seconds
            
            if elapsed > 600:  # 10 min timeout
                raise TaskTimeoutError(f"Task timed out after {elapsed}s")


@click.group()
@click.version_option(version="1.0.0", prog_name="Suno CLI")
def cli():
    """
    🎵 Suno API Client - AI Music Generation
    
    Generate music, lyrics, and more using Suno AI.
    """
    pass


# ==================== Credits ====================

@cli.command()
def credits():
    """Check remaining credits balance"""
    api = get_api()
    
    with console.status("[yellow]Checking credits..."):
        balance = api.get_credits()
    
    console.print(Panel(
        f"[bold green]{balance}[/bold green] credits remaining",
        title="💰 Account Balance",
        border_style="green"
    ))


# ==================== Generate Music ====================

@cli.command()
@click.argument("prompt")
@click.option("--model", "-m", type=click.Choice(AVAILABLE_MODELS), default=DEFAULT_MODEL,
              help="AI model version")
@click.option("--custom", "-c", is_flag=True, help="Enable custom mode (requires --style and --title)")
@click.option("--instrumental", "-i", is_flag=True, help="Generate instrumental only (no vocals)")
@click.option("--style", "-s", default=None, help="Music style/genre (required in custom mode)")
@click.option("--title", "-t", default=None, help="Song title (required in custom mode)")
@click.option("--vocal", "-v", type=click.Choice(["m", "f"]), default=None, help="Vocal gender")
@click.option("--negative", "-n", default=None, help="Styles to exclude")
@click.option("--no-wait", is_flag=True, help="Don't wait for completion, just return task ID")
@click.option("--download", "-d", is_flag=True, help="Auto-download generated files")
def generate(prompt, model, custom, instrumental, style, title, vocal, negative, no_wait, download):
    """
    Generate music from text description.
    
    Examples:
    
      suno generate "upbeat jazz with piano"
      
      suno generate "love song" --custom --style "Pop Ballad" --title "Forever" 
      
      suno generate "ambient electronic" --instrumental --model V5
    """
    api = get_api()
    
    # Validate custom mode requirements
    if custom and not (style and title):
        console.print("[red]Error:[/red] Custom mode requires --style and --title")
        raise click.Abort()
    
    console.print(Panel(
        f"[cyan]Prompt:[/cyan] {prompt}\n"
        f"[cyan]Model:[/cyan] {model}\n"
        f"[cyan]Mode:[/cyan] {'Custom' if custom else 'Auto'}\n"
        f"[cyan]Instrumental:[/cyan] {'Yes' if instrumental else 'No'}",
        title="🎵 Generating Music",
        border_style="blue"
    ))
    
    try:
        with console.status("[yellow]Submitting generation request..."):
            task_id = api.generate_music(
                prompt=prompt,
                model=model,
                custom_mode=custom,
                instrumental=instrumental,
                style=style,
                title=title,
                vocal_gender=vocal,
                negative_tags=negative
            )
        
        console.print(f"[green]✓[/green] Task created: [cyan]{task_id}[/cyan]")
        
        if no_wait:
            console.print("\nUse [cyan]suno status {task_id}[/cyan] to check progress")
            return
        
        # Wait for completion
        status = wait_with_progress(api, task_id, "Music Generation")
        
        # Display results
        if status.tracks:
            table = Table(title="🎵 Generated Tracks", show_header=True)
            table.add_column("#", style="dim", width=3)
            table.add_column("Title", style="cyan")
            table.add_column("Duration", style="green")
            table.add_column("Audio ID", style="dim")
            
            downloads_dir = ensure_downloads_dir()
            
            for i, track in enumerate(status.tracks, 1):
                table.add_row(
                    str(i),
                    track.title or "Untitled",
                    format_duration(track.duration),
                    track.id[:20] + "..."
                )
                
                if download and track.audio_url:
                    filename = f"{track.title or 'track'}_{track.id[:8]}.mp3"
                    filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
                    output_path = downloads_dir / filename
                    
                    with console.status(f"[yellow]Downloading {filename}..."):
                        api.download_file(track.audio_url, output_path)
                    console.print(f"[green]✓[/green] Downloaded: {output_path}")
            
            console.print(table)
            
            # Show URLs
            console.print("\n[bold]Audio URLs:[/bold]")
            for track in status.tracks:
                if track.audio_url:
                    console.print(f"  • {track.audio_url}")
                    
    except SunoAPIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise click.Abort()


# ==================== Generate Lyrics ====================

@cli.command()
@click.argument("prompt")
@click.option("--no-wait", is_flag=True, help="Don't wait for completion")
def lyrics(prompt, no_wait):
    """
    Generate lyrics from text description.
    
    Example:
    
      suno lyrics "a song about adventure and discovery"
    """
    api = get_api()
    
    console.print(Panel(
        f"[cyan]Prompt:[/cyan] {prompt}",
        title="📝 Generating Lyrics",
        border_style="blue"
    ))
    
    try:
        with console.status("[yellow]Submitting lyrics request..."):
            task_id = api.generate_lyrics(prompt)
        
        console.print(f"[green]✓[/green] Task created: [cyan]{task_id}[/cyan]")
        
        if no_wait:
            return
        
        status = wait_with_progress(api, task_id, "Lyrics Generation")
        
        if status.lyrics:
            for i, lyric in enumerate(status.lyrics, 1):
                console.print(Panel(
                    lyric.text,
                    title=f"📝 Lyrics #{i}" + (f" - {lyric.title}" if lyric.title else ""),
                    border_style="green"
                ))
                
    except SunoAPIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise click.Abort()


# ==================== Extend Music ====================

@cli.command()
@click.argument("audio_id")
@click.option("--model", "-m", type=click.Choice(AVAILABLE_MODELS), default=DEFAULT_MODEL,
              help="Model (must match original)")
@click.option("--continue-at", "-c", type=float, required=True, help="Time in seconds to start extension")
@click.option("--prompt", "-p", default=None, help="Description of extension")
@click.option("--style", "-s", default=None, help="Music style")
@click.option("--title", "-t", default=None, help="Song title")
@click.option("--use-defaults", is_flag=True, help="Use original track's parameters")
@click.option("--no-wait", is_flag=True, help="Don't wait for completion")
def extend(audio_id, model, continue_at, prompt, style, title, use_defaults, no_wait):
    """
    Extend an existing music track.
    
    Example:
    
      suno extend abc123-audio-id --continue-at 120 --prompt "add guitar solo"
    """
    api = get_api()
    
    console.print(Panel(
        f"[cyan]Audio ID:[/cyan] {audio_id}\n"
        f"[cyan]Continue at:[/cyan] {continue_at}s\n"
        f"[cyan]Mode:[/cyan] {'Default params' if use_defaults else 'Custom params'}",
        title="🔄 Extending Music",
        border_style="blue"
    ))
    
    try:
        with console.status("[yellow]Submitting extend request..."):
            task_id = api.extend_music(
                audio_id=audio_id,
                model=model,
                default_param_flag=not use_defaults,
                continue_at=continue_at,
                prompt=prompt,
                style=style,
                title=title
            )
        
        console.print(f"[green]✓[/green] Task created: [cyan]{task_id}[/cyan]")
        
        if no_wait:
            return
        
        status = wait_with_progress(api, task_id, "Music Extension")
        
        if status.tracks:
            for track in status.tracks:
                console.print(f"\n[green]✓[/green] Extended track: {track.title}")
                console.print(f"  Duration: {format_duration(track.duration)}")
                console.print(f"  URL: {track.audio_url}")
                
    except SunoAPIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise click.Abort()


# ==================== Separate Vocals ====================

@cli.command()
@click.argument("task_id")
@click.argument("audio_id")
@click.option("--type", "-t", "sep_type", type=click.Choice(["vocal", "stem"]), default="vocal",
              help="Separation type: vocal (2 stems) or stem (12 stems)")
@click.option("--no-wait", is_flag=True, help="Don't wait for completion")
def separate(task_id, audio_id, sep_type, no_wait):
    """
    Separate vocals from music.
    
    Example:
    
      suno separate task123 audio456 --type vocal
    """
    api = get_api()
    
    separation_type = SeparationType.SPLIT_STEM if sep_type == "stem" else SeparationType.SEPARATE_VOCAL
    
    console.print(Panel(
        f"[cyan]Task ID:[/cyan] {task_id}\n"
        f"[cyan]Audio ID:[/cyan] {audio_id}\n"
        f"[cyan]Type:[/cyan] {sep_type} ({'12 stems' if sep_type == 'stem' else '2 stems'})",
        title="🎤 Separating Vocals",
        border_style="blue"
    ))
    
    try:
        with console.status("[yellow]Submitting separation request..."):
            new_task_id = api.separate_vocals(task_id, audio_id, separation_type)
        
        console.print(f"[green]✓[/green] Task created: [cyan]{new_task_id}[/cyan]")
        
        if no_wait:
            return
        
        status = wait_with_progress(api, new_task_id, "Vocal Separation")
        console.print("[green]✓[/green] Separation complete! Check task status for download URLs.")
        
    except SunoAPIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise click.Abort()


# ==================== Create Video ====================

@cli.command()
@click.argument("task_id")
@click.argument("audio_id")
@click.option("--author", "-a", default=None, help="Artist name (max 50 chars)")
@click.option("--domain", "-d", default=None, help="Website watermark (max 50 chars)")
@click.option("--no-wait", is_flag=True, help="Don't wait for completion")
def video(task_id, audio_id, author, domain, no_wait):
    """
    Create an MP4 music video with visualizations.
    
    Example:
    
      suno video task123 audio456 --author "My Name"
    """
    api = get_api()
    
    console.print(Panel(
        f"[cyan]Task ID:[/cyan] {task_id}\n"
        f"[cyan]Audio ID:[/cyan] {audio_id}\n"
        f"[cyan]Author:[/cyan] {author or 'Not set'}\n"
        f"[cyan]Domain:[/cyan] {domain or 'Not set'}",
        title="🎬 Creating Video",
        border_style="blue"
    ))
    
    try:
        with console.status("[yellow]Submitting video request..."):
            new_task_id = api.create_video(task_id, audio_id, author, domain)
        
        console.print(f"[green]✓[/green] Task created: [cyan]{new_task_id}[/cyan]")
        
        if no_wait:
            return
        
        status = wait_with_progress(api, new_task_id, "Video Generation")
        console.print("[green]✓[/green] Video created! Check task status for download URL.")
        
    except SunoAPIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise click.Abort()


# ==================== Convert to WAV ====================

@cli.command()
@click.argument("task_id")
@click.argument("audio_id")
@click.option("--no-wait", is_flag=True, help="Don't wait for completion")
def wav(task_id, audio_id, no_wait):
    """
    Convert track to high-quality WAV format.
    
    Example:
    
      suno wav task123 audio456
    """
    api = get_api()
    
    console.print(Panel(
        f"[cyan]Task ID:[/cyan] {task_id}\n"
        f"[cyan]Audio ID:[/cyan] {audio_id}",
        title="🔊 Converting to WAV",
        border_style="blue"
    ))
    
    try:
        with console.status("[yellow]Submitting WAV conversion request..."):
            new_task_id = api.convert_to_wav(task_id, audio_id)
        
        console.print(f"[green]✓[/green] Task created: [cyan]{new_task_id}[/cyan]")
        
        if no_wait:
            return
        
        status = wait_with_progress(api, new_task_id, "WAV Conversion")
        console.print("[green]✓[/green] Conversion complete! Check task status for download URL.")
        
    except SunoAPIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise click.Abort()


# ==================== Check Status ====================

@cli.command()
@click.argument("task_id")
def status(task_id):
    """
    Check the status of a generation task.
    
    Example:
    
      suno status abc123-task-id
    """
    api = get_api()
    
    with console.status("[yellow]Checking task status..."):
        task_status = api.get_task_status(task_id)
    
    status_colors = {
        TaskStatusEnum.PENDING: "yellow",
        TaskStatusEnum.GENERATING: "blue",
        TaskStatusEnum.SUCCESS: "green",
        TaskStatusEnum.FAILED: "red"
    }
    
    color = status_colors.get(task_status.status, "white")
    
    console.print(Panel(
        f"[cyan]Task ID:[/cyan] {task_id}\n"
        f"[cyan]Status:[/cyan] [{color}]{task_status.status.value}[/{color}]"
        + (f"\n[red]Error:[/red] {task_status.error_message}" if task_status.error_message else ""),
        title="📊 Task Status",
        border_style=color
    ))
    
    if task_status.tracks:
        table = Table(title="🎵 Generated Tracks", show_header=True)
        table.add_column("#", style="dim", width=3)
        table.add_column("Title", style="cyan")
        table.add_column("Duration", style="green")
        table.add_column("Audio ID", style="dim")
        
        for i, track in enumerate(task_status.tracks, 1):
            table.add_row(
                str(i),
                track.title or "Untitled",
                format_duration(track.duration),
                track.id
            )
        
        console.print(table)
        
        console.print("\n[bold]Audio URLs:[/bold]")
        for track in task_status.tracks:
            if track.audio_url:
                console.print(f"  • {track.audio_url}")
    
    if task_status.lyrics:
        for i, lyric in enumerate(task_status.lyrics, 1):
            console.print(Panel(
                lyric.text[:500] + ("..." if len(lyric.text) > 500 else ""),
                title=f"📝 Lyrics #{i}",
                border_style="green"
            ))


# ==================== Download ====================

@cli.command()
@click.argument("url")
@click.option("--output", "-o", default=None, help="Output filename")
def download(url, output):
    """
    Download a file from URL.
    
    Example:
    
      suno download https://example.com/song.mp3 -o mysong.mp3
    """
    api = get_api()
    downloads_dir = ensure_downloads_dir()
    
    if not output:
        # Extract filename from URL
        output = url.split("/")[-1].split("?")[0]
        if not output:
            output = "download.mp3"
    
    output_path = downloads_dir / output
    
    console.print(f"[yellow]Downloading to:[/yellow] {output_path}")
    
    try:
        with console.status("[yellow]Downloading..."):
            api.download_file(url, output_path)
        
        console.print(f"[green]✓[/green] Downloaded: {output_path}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise click.Abort()


# ==================== Interactive Mode ====================

@cli.command()
def interactive():
    """
    Start interactive mode for guided music generation.
    """
    api = get_api()
    
    console.print(Panel(
        "[bold cyan]Welcome to Suno AI Interactive Mode![/bold cyan]\n\n"
        "I'll guide you through creating music step by step.",
        title="🎵 Interactive Mode",
        border_style="cyan"
    ))
    
    # Check credits first
    with console.status("[yellow]Checking credits..."):
        balance = api.get_credits()
    console.print(f"[green]✓[/green] You have [bold]{balance}[/bold] credits\n")
    
    # Choose generation type
    console.print("[bold]What would you like to create?[/bold]")
    console.print("  1. Generate Music")
    console.print("  2. Generate Lyrics")
    console.print("  3. Cancel")
    
    choice = click.prompt("Enter choice", type=int, default=1)
    
    if choice == 3:
        console.print("[yellow]Cancelled.[/yellow]")
        return
    
    if choice == 2:
        # Lyrics generation
        prompt = click.prompt("\nDescribe the lyrics you want")
        
        with console.status("[yellow]Generating lyrics..."):
            task_id = api.generate_lyrics(prompt)
        
        status = wait_with_progress(api, task_id, "Lyrics Generation")
        
        if status.lyrics:
            for lyric in status.lyrics:
                console.print(Panel(lyric.text, title="📝 Generated Lyrics", border_style="green"))
        return
    
    # Music generation
    prompt = click.prompt("\nDescribe the music you want")
    
    use_custom = click.confirm("Use custom mode (specify style & title)?", default=False)
    
    style = None
    title = None
    if use_custom:
        style = click.prompt("Music style (e.g., Jazz, Rock, Electronic)")
        title = click.prompt("Song title")
    
    instrumental = click.confirm("Instrumental only (no vocals)?", default=False)
    
    console.print("\n[bold]Available models:[/bold]")
    for i, m in enumerate(AVAILABLE_MODELS, 1):
        console.print(f"  {i}. {m}")
    
    model_choice = click.prompt("Choose model", type=int, default=3)
    model = AVAILABLE_MODELS[min(model_choice - 1, len(AVAILABLE_MODELS) - 1)]
    
    console.print(f"\n[yellow]Generating with {model}...[/yellow]")
    
    try:
        with console.status("[yellow]Submitting request..."):
            task_id = api.generate_music(
                prompt=prompt,
                model=model,
                custom_mode=use_custom,
                instrumental=instrumental,
                style=style,
                title=title
            )
        
        status = wait_with_progress(api, task_id, "Music Generation")
        
        if status.tracks:
            table = Table(title="🎵 Your Generated Tracks")
            table.add_column("#", width=3)
            table.add_column("Title", style="cyan")
            table.add_column("Duration", style="green")
            
            for i, track in enumerate(status.tracks, 1):
                table.add_row(str(i), track.title or "Untitled", format_duration(track.duration))
            
            console.print(table)
            
            if click.confirm("\nDownload tracks?", default=True):
                downloads_dir = ensure_downloads_dir()
                for track in status.tracks:
                    if track.audio_url:
                        filename = f"{track.title or 'track'}_{track.id[:8]}.mp3"
                        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
                        output_path = downloads_dir / filename
                        
                        with console.status(f"[yellow]Downloading {filename}..."):
                            api.download_file(track.audio_url, output_path)
                        console.print(f"[green]✓[/green] Saved: {output_path}")
            
            console.print("\n[bold green]Done![/bold green] 🎉")
            
    except SunoAPIError as e:
        console.print(f"[red]Error:[/red] {e.message}")
        raise click.Abort()


if __name__ == "__main__":
    cli()
