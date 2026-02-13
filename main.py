"""CLI entry point for Twitter Monitor Bot."""

import asyncio
import sys
from pathlib import Path

import click
from loguru import logger
from rich.console import Console
from rich.table import Table

from config import settings
from database import db
from ai_scheduler import run_ai_once as run_once, run_ai_scheduler as run_scheduler
from twitter_client import TwitterClient

# Configure logging
def setup_logging():
    """Configure loguru logging."""
    logger.remove()  # Remove default handler
    
    # Console output
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # File output
    logger.add(
        "logs/monitor.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        compression="zip"
    )


# Create logs directory
Path("logs").mkdir(exist_ok=True)
setup_logging()

# Rich console for pretty output
console = Console()


def normalize_username(username: str) -> str:
    """Normalize username: lowercase, remove @ prefix."""
    username = username.strip().lower()
    if username.startswith("@"):
        username = username[1:]
    return username


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Twitter Monitor Bot - Route tweets to Discord channels."""
    pass


@cli.command()
def init():
    """Initialize database and config."""
    try:
        # Ensure data directory exists
        settings.ensure_data_dir()
        
        # Initialize database
        db.init_database()
        
        # Check if .env file exists
        if not Path(".env").exists():
            # Copy example file
            example_path = Path(".env.example")
            if example_path.exists():
                Path(".env").write_text(example_path.read_text())
                console.print(
                    "[yellow]Created .env file from .env.example. "
                    "Please edit it with your credentials.[/yellow]"
                )
        
        console.print("[green]✓ Database initialized successfully[/green]")
        console.print(f"[dim]Database path: {settings.DATABASE_PATH}[/dim]")
    
    except Exception as e:
        console.print(f"[red]✗ Error initializing: {e}[/red]")
        sys.exit(1)


@cli.group()
def channel():
    """Manage Discord channels."""
    pass


@channel.command("create")
@click.argument("name")
@click.argument("webhook_url")
def channel_create(name: str, webhook_url: str):
    """Create a channel group with Discord webhook."""
    try:
        # Validate webhook URL format
        if not webhook_url.startswith("https://discord.com/api/webhooks/"):
            console.print(
                "[yellow]Warning: Webhook URL doesn't look like a standard Discord webhook[/yellow]"
            )
        
        channel_id = db.create_channel(name, webhook_url)
        console.print(f"[green]✓ Created channel '{name}' (ID: {channel_id})[/green]")
    
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            console.print(f"[red]✗ Channel '{name}' already exists[/red]")
        else:
            console.print(f"[red]✗ Error creating channel: {e}[/red]")
        sys.exit(1)


@channel.command("list")
def channel_list():
    """List all channels with user counts."""
    try:
        channels = db.list_channels()
        
        if not channels:
            console.print("[dim]No channels configured[/dim]")
            return
        
        table = Table(title="Channels")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Name", style="green")
        table.add_column("Webhook URL", style="blue")
        table.add_column("Users", style="magenta", justify="center")
        table.add_column("Created", style="dim")
        
        for ch in channels:
            # Truncate webhook URL for display
            webhook_display = ch["webhook_url"][:50] + "..." if len(ch["webhook_url"]) > 50 else ch["webhook_url"]
            
            table.add_row(
                str(ch["id"]),
                ch["name"],
                webhook_display,
                str(ch["user_count"]),
                ch["created_at"][:19] if ch["created_at"] else ""
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(channels)} channel(s)[/dim]")
    
    except Exception as e:
        console.print(f"[red]✗ Error listing channels: {e}[/red]")
        sys.exit(1)


@channel.command("delete")
@click.argument("name")
@click.confirmation_option(prompt=f"Are you sure you want to delete this channel and all its users?")
def channel_delete(name: str):
    """Remove a channel and its users."""
    try:
        deleted = db.delete_channel(name)
        
        if deleted:
            console.print(f"[green]✓ Deleted channel '{name}'[/green]")
        else:
            console.print(f"[yellow]Channel '{name}' not found[/yellow]")
    
    except Exception as e:
        console.print(f"[red]✗ Error deleting channel: {e}[/red]")
        sys.exit(1)


@cli.group()
def user():
    """Manage monitored Twitter users."""
    pass


@user.command("add")
@click.argument("username")
@click.argument("channel_name")
def user_add(username: str, channel_name: str):
    """Add Twitter user to specific channel."""
    try:
        # Normalize username
        normalized = normalize_username(username)
        
        # Validate API key
        if not settings.TWITTERAPI_KEY:
            console.print("[red]✗ TWITTERAPI_KEY not set in .env[/red]")
            sys.exit(1)
        
        # Get channel
        channel = db.get_channel_by_name(channel_name)
        if not channel:
            console.print(f"[red]✗ Channel '{channel_name}' not found[/red]")
            console.print(f"[dim]Create it with: python main.py channel create {channel_name} <webhook_url>[/dim]")
            sys.exit(1)
        
        # Fetch user's latest tweet to initialize last_tweet_id
        console.print(f"[dim]Fetching @{normalized} from Twitter...[/dim]")
        
        async def fetch_and_add():
            async with TwitterClient() as client:
                tweets = await client.get_last_tweets(normalized)
                
                last_tweet_id = None
                if tweets:
                    # Get the most recent tweet ID
                    last_tweet_id = max(tweets, key=lambda t: int(t.id)).id
                    console.print(f"[dim]Found {len(tweets)} tweet(s), initializing...[/dim]")
                else:
                    console.print(f"[yellow]Warning: No tweets found for @{normalized}[/yellow]")
                
                # Add user to database
                db.add_user(normalized, channel.id, last_tweet_id)
                
                return last_tweet_id
        
        last_tweet_id = asyncio.run(fetch_and_add())
        
        if last_tweet_id:
            console.print(
                f"[green]✓ Added @{normalized} to channel '{channel_name}' "
                f"(last_tweet_id: {last_tweet_id})[/green]"
            )
        else:
            console.print(
                f"[green]✓ Added @{normalized} to channel '{channel_name}' "
                f"(no tweets yet)[/green]"
            )
    
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            console.print(f"[red]✗ User @{normalized} is already being monitored[/red]")
        else:
            console.print(f"[red]✗ Error adding user: {e}[/red]")
        sys.exit(1)


@user.command("remove")
@click.argument("username")
def user_remove(username: str):
    """Remove user from monitoring."""
    try:
        normalized = normalize_username(username)
        deleted = db.remove_user(normalized)
        
        if deleted:
            console.print(f"[green]✓ Removed @{normalized} from monitoring[/green]")
        else:
            console.print(f"[yellow]User @{normalized} not found[/yellow]")
    
    except Exception as e:
        console.print(f"[red]✗ Error removing user: {e}[/red]")
        sys.exit(1)


@user.command("list")
@click.argument("channel_name", required=False)
def user_list(channel_name: str = None):
    """List monitored users, optionally filtered by channel."""
    try:
        users = db.list_users(channel_name)
        
        if not users:
            if channel_name:
                console.print(f"[dim]No users in channel '{channel_name}'[/dim]")
            else:
                console.print("[dim]No users configured[/dim]")
            return
        
        table = Table(title=f"Monitored Users" + (f" - {channel_name}" if channel_name else ""))
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Username", style="green")
        table.add_column("Channel", style="blue")
        table.add_column("Status", style="magenta")
        table.add_column("Last Tweet ID", style="dim")
        table.add_column("Added", style="dim")
        
        for u in users:
            status = "[green]active[/green]" if u["is_active"] else "[red]inactive[/red]"
            last_id = u["last_tweet_id"][:15] + "..." if u["last_tweet_id"] and len(u["last_tweet_id"]) > 15 else (u["last_tweet_id"] or "-")
            
            table.add_row(
                str(u["id"]),
                f"@{u['username']}",
                u["channel_name"],
                status,
                last_id,
                u["added_at"][:19] if u["added_at"] else ""
            )
        
        console.print(table)
        console.print(f"\n[dim]Total: {len(users)} user(s)[/dim]")
    
    except Exception as e:
        console.print(f"[red]✗ Error listing users: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option(
    "--interval",
    default=None,
    type=int,
    help="Check interval in seconds (default: 300)"
)
def run(interval: int):
    """Start monitoring loop (default 5 minutes)."""
    try:
        # Validate settings
        settings.validate()
        
        interval = interval or settings.CHECK_INTERVAL_SECONDS
        
        console.print(f"[green]Starting Twitter Monitor Bot[/green]")
        console.print(f"[dim]Interval: {interval}s[/dim]")
        console.print(f"[dim]Database: {settings.DATABASE_PATH}[/dim]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")
        
        asyncio.run(run_scheduler(interval))
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutdown complete[/yellow]")
    
    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def run_once_cmd():
    """Single execution for cron jobs."""
    try:
        settings.validate()
        
        console.print(f"[green]Running single check...[/green]")
        
        asyncio.run(run_once())
        
        console.print("[green]✓ Completed[/green]")
    
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
