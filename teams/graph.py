import os
import json
import httpx
import time
import msal
import sys
from config import TOKEN_PATH, CLIENT_ID, CLIENT_SECRET, TENANT_ID, DEMO_MODE

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

class GraphClient:
    def __init__(self):
        self.token = self._load_token()
        self.access_token = self.token.get("access_token") if self.token else None
        self.refresh_token = self.token.get("refresh_token") if self.token else None
        self.expires_at = self.token.get("expires_on", 0) if self.token else 0

    def _load_token(self):
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH) as f:
                return json.load(f)
        return None

    async def _refresh_token_if_needed(self):
        """Refresh the token if it's expired or about to expire (within 5 minutes)."""
        if DEMO_MODE == "true": # Check against string 'true'
            print("GraphClient: Demo mode, skipping token refresh.", file=sys.stderr)
            self.access_token = "demo_access_token" # Ensure access token exists in demo mode
            return True

        # Load token fresh each time to get latest refresh token if available
        self.token = self._load_token()
        if not self.token:
            raise RuntimeError("Token file not found. Please login using the CLI.")
            
        self.access_token = self.token.get("access_token")
        self.refresh_token = self.token.get("refresh_token")
        self.expires_at = self.token.get("expires_on", 0)

        current_time = int(time.time())
        # Refresh if token expires within 5 minutes (300 seconds) or is already expired
        if (current_time + 300 >= self.expires_at or not self.access_token) and self.refresh_token:
            print(f"GraphClient: Token expiring soon or invalid, attempting refresh (expires_at={self.expires_at}, current={current_time}).", file=sys.stderr) # Added logging

            if CLIENT_SECRET:
                # Use Confidential Client for service principals
                print("GraphClient: Using ConfidentialClientApplication for refresh.", file=sys.stderr) # Added logging
                app = msal.ConfidentialClientApplication(
                    CLIENT_ID,
                    authority=AUTHORITY,
                    client_credential=CLIENT_SECRET
                )
                result = app.acquire_token_by_refresh_token(
                    self.refresh_token,
                    scopes=SCOPES
                )
            else:
                # Use Public Client for user accounts (device flow likely used for initial login)
                print("GraphClient: Using PublicClientApplication for refresh.", file=sys.stderr) # Added logging
                app = msal.PublicClientApplication(
                    CLIENT_ID,
                    authority=AUTHORITY
                    # token_cache=msal.SerializableTokenCache() # Consider adding cache persistence if needed long term
                )
                # Public client uses acquire_token_by_refresh_token as well
                result = app.acquire_token_by_refresh_token(
                    self.refresh_token,
                    scopes=SCOPES
                )

            if "access_token" in result:
                print("GraphClient: Token refresh successful.", file=sys.stderr) # Added logging
                self.access_token = result["access_token"]
                # Update refresh token ONLY if a new one is provided in the result
                self.refresh_token = result.get("refresh_token", self.refresh_token)
                self.expires_at = result.get("expires_on", int(time.time()) + result.get("expires_in", 3600)) # Use expires_on or calculate from expires_in
                self.token = result # Update the whole token structure

                # Save the refreshed token
                try:
                    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
                    with open(TOKEN_PATH, "w") as f:
                        json.dump(result, f)
                    print(f"GraphClient: Refreshed token saved to {TOKEN_PATH}", file=sys.stderr) # Added logging
                except IOError as e:
                    print(f"GraphClient: Error saving refreshed token to {TOKEN_PATH}: {e}", file=sys.stderr) # Added logging
                    # Continue even if save fails, we have the token in memory
                return True
            else:
                error_desc = result.get('error_description', str(result))
                print(f"GraphClient: Token refresh failed: {error_desc}", file=sys.stderr) # Added logging
                # Optionally clear the token file if refresh fails permanently
                # try:
                #     if os.path.exists(TOKEN_PATH): os.remove(TOKEN_PATH)
                # except OSError: pass # Ignore error if removal fails
                raise RuntimeError(f"Token refresh failed: {error_desc}. Please try logging in again via CLI.")
        elif not self.access_token:
             raise RuntimeError("No access token found and no refresh token available. Please login using the CLI.")
             
        # Return True if we have a valid (or recently refreshed) access token
        return self.access_token is not None

    async def _get_headers(self):
        await self._refresh_token_if_needed()
        if not self.access_token:
            raise RuntimeError("No access token found. Please login using the CLI.")
        return {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}

    async def list_chats(self):
        """List all chats the user is a member of."""
        if DEMO_MODE:
            return [
                {"id": "demo-chat-1", "topic": "Demo Team Chat", "createdDateTime": "2023-05-15T10:00:00Z", "lastUpdatedDateTime": "2023-05-16T15:30:00Z"},
                {"id": "demo-chat-2", "topic": "One-on-One Chat", "createdDateTime": "2023-06-01T09:15:00Z", "lastUpdatedDateTime": "2023-06-02T14:20:00Z"}
            ]
            
        url = f"{GRAPH_API_BASE}/me/chats"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=await self._get_headers())
            resp.raise_for_status()
            return resp.json().get("value", [])

    async def get_messages(self, chat_id):
        """Get messages from a specific chat."""
        if DEMO_MODE:
            if chat_id == "demo-chat-1":
                return [
                    {"id": "msg1", "chatId": chat_id, "from": {"user": {"id": "user1", "displayName": "Demo User"}}, "body": {"content": "Hello team!"}, "createdDateTime": "2023-05-15T10:05:00Z"},
                    {"id": "msg2", "chatId": chat_id, "from": {"user": {"id": "user2", "displayName": "Demo Bot"}}, "body": {"content": "How can I help today?"}, "createdDateTime": "2023-05-15T10:06:00Z"}
                ]
            return []
            
        url = f"{GRAPH_API_BASE}/chats/{chat_id}/messages"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=await self._get_headers())
            resp.raise_for_status()
            return resp.json().get("value", [])

    async def send_message(self, chat_id, text):
        """Send a message to a specific chat."""
        if DEMO_MODE:
            return {"id": f"demo-msg-{int(time.time())}", "chatId": chat_id, "body": {"content": text}, "createdDateTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            
        url = f"{GRAPH_API_BASE}/chats/{chat_id}/messages"
        data = {"body": {"contentType": "text", "content": text}}
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=await self._get_headers(), json=data)
            resp.raise_for_status()
            return resp.json()

    async def create_chat(self, user_id_or_email):
        """Create a 1:1 chat with a user by email or user ID."""
        if DEMO_MODE:
            return {"id": f"demo-chat-{int(time.time())}", "topic": f"Chat with {user_id_or_email}", "createdDateTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            
        url = f"{GRAPH_API_BASE}/chats"
        # Accepts either user ID or email
        member = {
            "@odata.type": "#microsoft.graph.aadUserConversationMember",
            "roles": ["owner"],
            "user@odata.bind": f"https://graph.microsoft.com/v1.0/users('{user_id_or_email}')"
        }
        data = {
            "chatType": "oneOnOne",
            "members": [member]
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=await self._get_headers(), json=data)
            resp.raise_for_status()
            return resp.json() 