"""
Ensure the project root is on sys.path so imports like 'teams' work correctly
when this script is executed as a standalone file.
"""
import os
import sys
# Add project root (parent directory of this file) to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from mcp.server.fastmcp import FastMCP, Context
from teams.graph import GraphClient
from db.schema import init_db, insert_chat, insert_message
import asyncio
import time
import json
from config import POLL_INTERVAL, DEMO_MODE
# Numerical library and HTTP client
import numpy as np
import httpx
"""
Embedding backend: always use OpenAI API for embeddings.
"""

mcp = FastMCP("Teams Messenger MCP App", log_level="DEBUG")
graph = GraphClient()
# Initialize database connection only when not in demo mode to avoid lock conflicts
db_con = init_db() if not DEMO_MODE else None
print(f"mcp_server: FastMCP instance created, persistence={'enabled' if db_con else 'disabled'}", file=sys.stderr)

import threading

# Lazy embedder instance
_embedder = None
_embedder_lock = threading.Lock()

class OpenAIEmbedder:
    """Embedder using OpenAI API for embeddings."""
    def __init__(self, model: str = "text-embedding-ada-002"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

    def encode(self, texts: list[str]) -> np.ndarray:
        url = "https://api.openai.com/v1/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"input": texts, "model": self.model}
        resp = httpx.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        embeddings = [item.get("embedding", []) for item in data]
        return np.array(embeddings, dtype=np.float32)

def get_embedder():
    """Return a singleton OpenAI embedder."""
    global _embedder
    if _embedder is None:
        with _embedder_lock:
            if _embedder is None:
                _embedder = OpenAIEmbedder()
    return _embedder

# Track last message time per chat
last_message_time = {}
# Track chat updates
last_chat_updates = {}

# Error handling decorator
def handle_api_errors(func):
    """Decorator to handle API errors gracefully."""
    import functools
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                return {"error": "Authentication error. Please login again or refresh token.", "details": error_msg}
            elif "404" in error_msg or "not found" in error_msg.lower():
                return {"error": "Resource not found. Check the ID or permissions.", "details": error_msg}
            elif "429" in error_msg or "too many requests" in error_msg.lower():
                return {"error": "Rate limit exceeded. Please try again later.", "details": error_msg}
            else:
                return {"error": f"API error: {error_msg}", "details": error_msg}
    return wrapper

@mcp.tool()
@handle_api_errors
async def list_chats() -> list:
    """List all Teams chats the agent is a member of and store in DuckDB."""
    print("mcp_server: tool list_chats invoked", file=sys.stderr)
    chats = await graph.list_chats()
    for chat in chats:
        # Store chat in DB if persistence enabled
        if db_con:
            insert_chat(db_con, chat)
    return chats

@mcp.resource("mcp://chats")
def all_chats():
    """Live resource representing all chats the agent is a member of.
    Subscribe to receive updates when chats are created or modified."""
    # This resource is updated by the polling loop
    return []

@mcp.tool()
@handle_api_errors
async def get_messages(chat_id: str) -> list:
    """Get recent messages from a specified chat, store in DuckDB with embeddings."""
    if not chat_id:
        return {"error": "Chat ID is required"}
        
    messages = await graph.get_messages(chat_id)
    
    for msg in messages:
        msg["chatId"] = chat_id
        content = msg["body"].get("content", "")
        embedding = None
        # Only generate embeddings if content is non-empty and embedder is available
        if content.strip():
            try:
                ed = get_embedder()
                if ed:
                    emb_arr = ed.encode([content])
                    # take first vector, cast and serialize
                    embedding = emb_arr[0].astype(np.float32).tobytes()
            except Exception as e:
                import sys
                print(f"Error generating embedding: {e}", file=sys.stderr)
        # Store message in DB if persistence enabled
        if db_con:
            insert_message(db_con, msg, embedding)
    return messages

@mcp.tool()
@handle_api_errors
async def send_message(chat_id: str, text: str) -> dict:
    """Send a message to a specified chat."""
    if not chat_id:
        return {"error": "Chat ID is required"}
    if not text or not text.strip():
        return {"error": "Message text is required"}
        
    return await graph.send_message(chat_id, text)

@mcp.tool()
def search_messages(query: str, mode: str = "hybrid", top_k: int = 10) -> list:
    """Hybrid search over messages: mode can be 'bm25', 'vector', or 'hybrid'."""
    if not query:
        return {"error": "Search query is required"}
    
    try:
        # Check for valid mode
        if mode not in ["bm25", "vector", "hybrid"]:
            return {"error": f"Invalid search mode: {mode}. Use 'bm25', 'vector', or 'hybrid'."}
        
        results = []
        if mode == "bm25":
            sql = """
                SELECT id, chat_id, sender_name, content, created, rank
                FROM (
                    SELECT *, bm25(messages_fts) AS rank
                    FROM messages_fts
                    WHERE messages_fts MATCH ?
                    ORDER BY rank LIMIT ?
                )
                JOIN messages ON messages.id = messages_fts.rowid
            """
            results = db_con.execute(sql, [query, top_k]).fetchall()
        elif mode == "vector":
            # vector search: compute embedding lazily
            ed = get_embedder()
            q_emb = None
            if ed:
                q_arr = ed.encode([query])
                q_emb = q_arr[0].astype(np.float32).tobytes()
            sql = """
                SELECT id, chat_id, sender_name, content, created,
                       vector_l2_distance(embedding, ?) AS dist
                FROM messages
                WHERE embedding IS NOT NULL
                ORDER BY dist ASC LIMIT ?
            """
            results = db_con.execute(sql, [q_emb, top_k]).fetchall()
        else:  # hybrid
            # First get BM25 results
            sql = """
                SELECT messages.id, chat_id, sender_name, content, created, bm25(messages_fts) AS rank
                FROM messages_fts
                JOIN messages ON messages.id = messages_fts.rowid
                WHERE messages_fts MATCH ?
                ORDER BY rank LIMIT ?
            """
            bm25_results = db_con.execute(sql, [query, top_k * 2]).fetchall()
            if not bm25_results:
                return []
            
            # Then re-rank using vector similarity if embedder available
            ed = get_embedder()
            if ed:
                texts = [row[3] for row in bm25_results]
                embs = ed.encode(texts)
                q_arr = ed.encode([query])
                q_vec = q_arr[0]
                dists = np.linalg.norm(embs - q_vec, axis=1)
                sorted_idx = np.argsort(dists)[:top_k]
                results = [bm25_results[i] for i in sorted_idx]
            else:
                # fallback to BM25 ordering
                results = bm25_results[:top_k]
        
        # Format results for return
        return [
            {
                "id": row[0],
                "chat_id": row[1],
                "sender_name": row[2],
                "content": row[3],
                "created": row[4],
                "score": row[5],
            }
            for row in results
        ]
    except Exception as e:
        return {"error": f"Search error: {str(e)}"}

@mcp.tool()
def search_messages_llm_rerank(query: str, top_k: int = 10, ctx: Context = None) -> list:
    """Advanced search with LLM reranking: first retrieves candidates with hybrid search,
    then optionally uses LLM to rerank results based on query relevance."""
    # Get initial candidates using hybrid search
    candidates = search_messages(query, mode="hybrid", top_k=top_k * 2)
    
    if not candidates or not ctx:
        return candidates[:top_k]
    
    # Simulate LLM reranking with locally available information
    # In a real implementation, this would call a deployed LLM for reranking
    # For now, we'll use a simple heuristic based on word overlap
    query_words = set(query.lower().split())
    for candidate in candidates:
        content = candidate["content"].lower()
        word_overlap = sum(1 for word in query_words if word in content)
        candidate["llm_score"] = word_overlap / len(query_words) if query_words else 0
    
    # Sort by reranked score
    candidates.sort(key=lambda x: x["llm_score"], reverse=True)
    return candidates[:top_k]

# Connect to the IR server via simple HTTP requests (since MCP client in container isn't working properly)
import os
import httpx

# Direct HTTP connection to simulated API endpoint
IR_SERVER_HOST = os.environ.get("IR_SERVER_HOST", "ir_server")
IR_SERVER_PORT = os.environ.get("IR_SERVER_PORT", "8090")
IR_SERVER_URL = f"http://{IR_SERVER_HOST}:{IR_SERVER_PORT}"

# IR integration tools that use HTTP requests
@mcp.tool()
async def ir_search(query: str, search_type: str = "hybrid", limit: int = 10) -> dict:
    """Perform information retrieval search using the IR server."""
    import sys
    print(f"Making HTTP request to IR server: {IR_SERVER_URL}/api/tools/search", file=sys.stderr)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{IR_SERVER_URL}/api/tools/search", 
                json={
                    "query": query,
                    "search_type": search_type,
                    "limit": limit
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {"error": "No result returned", "results": []})
            else:
                return {
                    "error": f"IR server returned status code {response.status_code}", 
                    "results": []
                }
    except Exception as e:
        print(f"Error calling IR search: {e}", file=sys.stderr)
        return {"error": str(e), "results": []}

@mcp.resource("mcp://messages/incoming")
def incoming_messages():
    """Live resource for incoming messages (updated by polling).
    Subscribe to receive real-time notifications when new messages arrive in any chat."""
    # This resource is updated by the polling loop
    return []

async def poll_new_messages():
    """Background task that polls for new messages and chat updates."""
    while True:
        try:
            chats = await graph.list_chats()
            
            # Check for chat updates
            for chat in chats:
                chat_id = chat["id"]
                last_updated = chat.get("lastUpdatedDateTime")
                
                # Detect chat updates (new or modified chats)
                if last_updated and (chat_id not in last_chat_updates or last_updated > last_chat_updates[chat_id]):
                    # Store chat update in DB if persistence enabled
                    if db_con:
                        insert_chat(db_con, chat)
                    last_chat_updates[chat_id] = last_updated
                    # Emit event on chats resource
                    await mcp.emit_resource_event("mcp://chats", chat)
            
            # Check for new messages in each chat
            for chat in chats:
                chat_id = chat["id"]
                messages = await graph.get_messages(chat_id)
                
                # Only process new messages
                for msg in messages:
                    msg["chatId"] = chat_id
                    created = msg.get("createdDateTime")
                    if not created:
                        continue

                    if chat_id not in last_message_time or created > last_message_time[chat_id]:
                        content = msg["body"].get("content", "")
                        embedding = None
                        # Only generate embeddings if model is loaded and content is non-empty
                        if content.strip():
                            try:
                                ed = get_embedder()
                                if ed:
                                    emb_arr = ed.encode([content])
                                    embedding = emb_arr[0].astype(np.float32).tobytes()
                            except Exception as e:
                                import sys
                                print(f"Error generating embedding during polling: {e}", file=sys.stderr)
                        # Store incoming message in DB if persistence enabled
                        if db_con:
                            insert_message(db_con, msg, embedding)
                        last_message_time[chat_id] = created

                        # Emit event on messages/incoming resource
                        await mcp.emit_resource_event("mcp://messages/incoming", msg)
        except Exception as e:
            import sys
            error_msg = str(e)
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                print(f"Authentication error during polling: {e}", file=sys.stderr)
                # Wait longer before retrying on auth errors (could be token issue)
                await asyncio.sleep(POLL_INTERVAL * 2)
            else:
                print(f"Polling error: {e}", file=sys.stderr)
                await asyncio.sleep(POLL_INTERVAL)
            continue
            
        await asyncio.sleep(POLL_INTERVAL)


@mcp.tool()
@handle_api_errors
async def create_chat(user_id_or_email: str) -> dict:
    """Create a 1:1 chat with a user by email or user ID."""
    if not user_id_or_email:
        return {"error": "User ID or email is required"}
        
    chat = await graph.create_chat(user_id_or_email)
    # Store new chat in DuckDB if persistence enabled
    if db_con:
        insert_chat(db_con, chat)
    # Also emit as event on chats resource
    await mcp.emit_resource_event("mcp://chats", chat)
    return chat

# TODO: Add Teams integration, tools, resources, and events

if __name__ == "__main__":
    mcp.run() 