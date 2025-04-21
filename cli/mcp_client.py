import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box
import asyncio
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import os
# Ensure project root is on sys.path for local imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from teams.graph import GraphClient

console = Console()
# 'sys' import and path insertion done above

# Use the same Python interpreter that runs this client (e.g., the active venv)
MCP_SERVER_CMD = [sys.executable, "mcp_server/server.py"]

async def get_session():
    """Get an MCP client session connected to the server."""
    console.print("[blue]get_session: starting connection to MCP server[/blue]")
    try:
        # Prepare DEMO_MODE for server
        demo_env = os.environ.get('DEMO_MODE', 'false')
        env = os.environ.copy()
        env['DEMO_MODE'] = demo_env
        console.print(f"[blue]get_session: launching server {MCP_SERVER_CMD} with DEMO_MODE={demo_env}[/blue]")
        # Launch server via stdio
        server_params = StdioServerParameters(
            command=MCP_SERVER_CMD[0],
            args=MCP_SERVER_CMD[1:],
            env=env,
        )
        client = stdio_client(server_params)
        console.print("[blue]get_session: stdio_client created, entering context...[/blue]")
        # Enter stdio context
        read, write = await client.__aenter__()
        console.print("[blue]get_session: entered stdio_client context[/blue]")
        # Initialize MCP client session
        session = ClientSession(read, write)
        console.print("[blue]get_session: ClientSession initialized, calling initialize()[/blue]")
        await session.initialize()
        console.print("[blue]get_session: session.initialize() complete[/blue]")
        return session
    except KeyboardInterrupt:
        console.print("[yellow]Connection canceled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]Error connecting to MCP server:[/bold red] {str(e)}")
        console.print("[yellow]Make sure the server code exists and dependencies are installed.[/yellow]")
        raise

@click.group()
def cli():
    """Rich CLI MCP client for Teams Messenger MCP App (MCP stdio mode)."""
    pass

@cli.command()
def list_chats():
    """List all Teams chats."""
    async def _list():
        try:
            console.print("[blue]list_chats: retrieving chats via GraphClient[/blue]")
            graph = GraphClient()
            chats = await graph.list_chats()
            console.print(f"[blue]list_chats: retrieved {len(chats)} chats[/blue]")
            # Render table
            table = Table(title="Teams Chats", box=box.ROUNDED)
            table.add_column("ID", style="cyan")
            table.add_column("Topic", style="green")
            table.add_column("Last Updated", style="yellow")
            for chat in chats:
                table.add_row(
                    chat.get("id", "Unknown"),
                    chat.get("topic", "No topic"),
                    chat.get("lastUpdatedDateTime", "Unknown")
                )
            console.print(table)
        except Exception as e:
            console.print(f"[bold red]Error listing chats:[/bold red] {str(e)}")
    import sys
    try:
        asyncio.run(_list())
    except KeyboardInterrupt:
        console.print("[yellow]List chats canceled by user.[/yellow]")
        sys.exit(0)

@cli.command()
@click.argument("chat_id")
def get_messages(chat_id):
    """Get messages from a chat."""
    async def _get():
        try:
            session = await get_session()
            result = await session.call_tool("get_messages", arguments={"chat_id": chat_id})
            messages = result or []
            table = Table(title=f"Messages in {chat_id}", box=box.ROUNDED)
            table.add_column("Sender", style="cyan")
            table.add_column("Content", style="green")
            table.add_column("Created", style="yellow")
            for msg in messages:
                sender = msg.get("from", {}).get("user", {}).get("displayName", "Unknown")
                content = msg.get("body", {}).get("content", "")
                created = msg.get("createdDateTime", "Unknown")
                table.add_row(sender, content, created)
            console.print(table)
        except Exception as e:
            console.print(f"[bold red]Error getting messages:[/bold red] {str(e)}")
    asyncio.run(_get())

@cli.command()
@click.argument("chat_id")
@click.argument("text")
def send_message(chat_id, text):
    """Send a message to a chat."""
    async def _send():
        try:
            session = await get_session()
            result = await session.call_tool("send_message", arguments={"chat_id": chat_id, "text": text})
            console.print(Panel(f"[green]Message sent to {chat_id}[/green]", subtitle=f"ID: {result.get('id', 'unknown')}"))
        except Exception as e:
            console.print(f"[bold red]Error sending message:[/bold red] {str(e)}")
    asyncio.run(_send())

@cli.command()
@click.argument("query")
@click.option("--mode", default="hybrid", help="Search mode: bm25, vector, hybrid, or llm.")
@click.option("--top_k", default=10, help="Number of results.")
def search_messages(query, mode, top_k):
    """Search messages with hybrid, BM25, vector, or LLM reranking."""
    async def _search():
        try:
            session = await get_session()
            tool_name = "search_messages" if mode != "llm" else "search_messages_llm_rerank"
            result = await session.call_tool(tool_name, arguments={
                "query": query, 
                "mode": mode if mode != "llm" else "hybrid", 
                "top_k": top_k
            })
            results = result or []
            
            table = Table(title=f"Search Results: '{query}' (mode: {mode})", box=box.ROUNDED)
            table.add_column("Sender", style="cyan")
            table.add_column("Content", style="green")
            table.add_column("Score", style="yellow")
            for row in results:
                score = row.get("score", "") if mode != "llm" else row.get("llm_score", "")
                table.add_row(row.get("sender_name", "Unknown"), row.get("content", ""), f"{score:.4f}" if isinstance(score, float) else str(score))
            console.print(table)
        except Exception as e:
            console.print(f"[bold red]Error searching messages:[/bold red] {str(e)}")
    asyncio.run(_search())

@cli.command()
@click.option("--resource", default="messages/incoming", help="Resource to stream (messages/incoming or chats).")
def stream(resource):
    """Stream new events in real time (subscribe to a live resource)."""
    async def _stream():
        try:
            session = await get_session()
            console.print(f"[bold blue]Streaming events from [green]{resource}[/green] resource (press CTRL+C to stop)[/bold blue]")
            
            async for event in session.subscribe_resource(resource):
                if resource == "messages/incoming":
                    msg = event.data
                    sender = msg.get("from", {}).get("user", {}).get("displayName", "Unknown")
                    content = msg.get("body", {}).get("content", "")
                    created = msg.get("createdDateTime", "Unknown")
                    console.print(
                        Panel(
                            f"[green]{content}[/green]",
                            title=f"[cyan]{sender}[/cyan]",
                            subtitle=f"[yellow]{created}[/yellow]",
                            box=box.ROUNDED
                        )
                    )
                elif resource == "chats":
                    chat = event.data
                    chat_id = chat.get("id", "Unknown")
                    topic = chat.get("topic", "No topic")
                    updated = chat.get("lastUpdatedDateTime", "Unknown")
                    console.print(
                        Panel(
                            f"[green]Chat: {topic}[/green]\n[yellow]Last updated: {updated}[/yellow]",
                            title=f"[cyan]Chat ID: {chat_id}[/cyan]",
                            box=box.ROUNDED
                        )
                    )
                else:
                    console.print(f"Event from {resource}: {event.data}")
        except asyncio.CancelledError:
            console.print("[yellow]Stream canceled.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error streaming events:[/bold red] {str(e)}")
    try:
        asyncio.run(_stream())
    except KeyboardInterrupt:
        console.print("[yellow]Stream stopped by user.[/yellow]")

@cli.command()
@click.argument("user_id_or_email")
def create_chat(user_id_or_email):
    """Create a 1:1 chat with a user by email or user ID."""
    async def _create():
        try:
            session = await get_session()
            result = await session.call_tool("create_chat", arguments={"user_id_or_email": user_id_or_email})
            console.print(Panel(f"[green]Chat created with {user_id_or_email}[/green]", subtitle=f"ID: {result.get('id', 'unknown')}"))
        except Exception as e:
            console.print(f"[bold red]Error creating chat:[/bold red] {str(e)}")
    asyncio.run(_create())

@cli.command()
def dashboard():
    """Interactive dashboard with real-time chat and message updates (coming soon)."""
    console.print(Panel(
        "[yellow]This feature is under development.[/yellow]\n"
        "In the future, this will display an interactive dashboard with:\n"
        "- Real-time chat updates\n"
        "- Message streaming\n"
        "- Interactive search\n"
        "- Chat selection and management",
        title="[bold cyan]Teams MCP Dashboard[/bold cyan]",
        box=box.ROUNDED
    ))

if __name__ == "__main__":
    cli() 