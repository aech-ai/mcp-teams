import click
import msal
import json
import os
import time
import sys

import dotenv
# dotenv.load_dotenv() # Moved to config.py to load before config variables are set

CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
print(f"DEBUG login.py: CLIENT_SECRET = {CLIENT_SECRET!r}", file=sys.stderr)
TENANT_ID = os.getenv("AZURE_TENANT_ID")
TOKEN_PATH = os.getenv("TOKEN_PATH")
DEMO_MODE = os.getenv("DEMO_MODE")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/.default"]

@click.group()
def cli():
    """Teams Messenger MCP CLI for authentication"""
    pass

@cli.command()
@click.option("--demo", is_flag=True, help="Enable demo mode with mock credentials")
def login(demo):
    """Login to Microsoft Teams (OAuth2) and store tokens."""
    if demo or DEMO_MODE == "true":
        # Create a mock token for demo mode
        mock_token = {
            "access_token": "demo_access_token",
            "refresh_token": "demo_refresh_token",
            "expires_on": int(time.time()) + 3600,
            "ext_expires_in": 3600,
            "token_type": "Bearer",
            "scope": " ".join(SCOPES),
            "is_demo": True
        }
        os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
        with open(TOKEN_PATH, "w") as f:
            json.dump(mock_token, f)
        click.echo("Demo mode enabled. Mock token saved.")
        return

    if not CLIENT_ID or not TENANT_ID:
        click.echo("Error: Missing CLIENT_ID or TENANT_ID in environment/config.")
        return
    
    try:
        print(f"DEBUG login.py: CLIENT_SECRET value check = {CLIENT_SECRET!r}", file=sys.stderr) # Keep check for info
        # Restore original logic checking for CLIENT_SECRET
        if CLIENT_SECRET:
            print("DEBUG: Using Confidential Client Flow (CLIENT_SECRET found)", file=sys.stderr)
            app = msal.ConfidentialClientApplication(
                CLIENT_ID,
                client_credential=CLIENT_SECRET,
                authority=AUTHORITY
            )
            result = app.acquire_token_for_client(scopes=SCOPES)
        else:
            # This branch will now likely not be used due to Azure requirement, but keep it for completeness
            print("DEBUG: Attempting Public Client Flow (CLIENT_SECRET *not* found)", file=sys.stderr)
            cache = msal.SerializableTokenCache()
            if os.path.exists(TOKEN_PATH):
                try:
                    cache.deserialize(open(TOKEN_PATH, "r").read())
                    print(f"DEBUG: Deserialized existing cache from {TOKEN_PATH}", file=sys.stderr)
                except Exception as cache_err:
                    print(f"DEBUG: Failed to deserialize cache from {TOKEN_PATH}, starting fresh: {cache_err}", file=sys.stderr)
                    
            app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)
            
            accounts = app.get_accounts()
            result = None
            if accounts:
                print(f"DEBUG: Found accounts in cache: {accounts}", file=sys.stderr)
                result = app.acquire_token_silent(scopes=SCOPES, account=accounts[0])
                if result:
                    print("DEBUG: Acquired token silently from cache.", file=sys.stderr)

            if not result:
                print("DEBUG: No suitable token in cache, initiating device flow.", file=sys.stderr)
                flow = app.initiate_device_flow(scopes=SCOPES)
                
                if "user_code" not in flow:
                    click.echo(f"Error: Failed to initiate device flow: {flow.get('error_description', '')}")
                    return
                    
                click.echo("DEBUG: Device flow initiated.", file=sys.stderr)
                click.echo(f"To sign in, use a web browser to open {flow['verification_uri']} and enter the code: {flow['user_code']}")
                result = app.acquire_token_by_device_flow(flow)
                print("DEBUG: acquire_token_by_device_flow completed.", file=sys.stderr)

            # Save the cache if it has changed
            if cache.has_state_changed:
                    print(f"DEBUG: Saving updated token cache to {TOKEN_PATH}", file=sys.stderr)
                    with open(TOKEN_PATH, "w") as f:
                        f.write(cache.serialize())

        # Common result handling
        if "access_token" in result:
            os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
            # Save raw result for GraphClient compatibility 
            # Use the original TOKEN_PATH for the raw dump needed by GraphClient
            raw_token_path = TOKEN_PATH 
            print(f"DEBUG: Saving token result to {raw_token_path}", file=sys.stderr)
            with open(raw_token_path, "w") as f: 
                json.dump(result, f)

            # If using public client flow, also save the MSAL cache (optional if GraphClient is adapted)
            if not CLIENT_SECRET and cache.has_state_changed:
                cache_path = TOKEN_PATH + ".mcache" # Use a different extension for MSAL cache
                print(f"DEBUG: Saving MSAL token cache to {cache_path}", file=sys.stderr)
                with open(cache_path, "w") as f:
                    f.write(cache.serialize())

            click.echo("Login successful. Token saved.")
        else:
            click.echo(f"Login failed: {result.get('error_description', str(result))}")
    except Exception as e:
        click.echo(f"Error during login process: {str(e)}")

@cli.command()
def status():
    """Show login status and token info."""
    if not os.path.exists(TOKEN_PATH):
        click.echo("Not logged in.")
        return
        
    try:
        with open(TOKEN_PATH) as f:
            token = json.load(f)
            
        # Check if it's a demo token
        if token.get("is_demo", False):
            click.echo("Demo mode active. Using mock credentials.")
            return
            
        expires_on = token.get("expires_on", 0)
        current_time = int(time.time())
        expires_in = expires_on - current_time
        
        if expires_in <= 0:
            click.echo("Token expired. Please refresh or login again.")
        else:
            click.echo(f"Logged in. Token expires in {expires_in} seconds (about {expires_in // 60} minutes).")
            
            # Alert if token will expire soon
            if expires_in < 300:  # Less than 5 minutes
                click.echo("Warning: Token will expire soon. Consider refreshing.")
                
    except Exception as e:
        click.echo(f"Error checking token status: {str(e)}")

@cli.command()
def refresh():
    """Refresh the access token."""
    if not os.path.exists(TOKEN_PATH):
        click.echo("Not logged in. Please login first.")
        return
        
    try:
        with open(TOKEN_PATH) as f:
            token = json.load(f)
            
        # Check if it's a demo token
        if token.get("is_demo", False):
            click.echo("Demo mode active. Token refreshed (simulated).")
            token["expires_on"] = int(time.time()) + 3600
            with open(TOKEN_PATH, "w") as f:
                json.dump(token, f)
            return
            
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            click.echo("No refresh token available. Please login again.")
            return
            
        if CLIENT_SECRET:
            # For service principal
            app = msal.ConfidentialClientApplication(
                CLIENT_ID,
                client_credential=CLIENT_SECRET,
                authority=AUTHORITY
            )
        else:
            # For user account
            app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
            
        result = app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=SCOPES
        )
        
        if "access_token" in result:
            with open(TOKEN_PATH, "w") as f:
                json.dump(result, f)
            click.echo("Token refreshed successfully.")
        else:
            click.echo(f"Token refresh failed: {result.get('error_description', str(result))}")
    except Exception as e:
        click.echo(f"Error refreshing token: {str(e)}")

@cli.command()
def logout():
    """Delete stored token and log out."""
    if not os.path.exists(TOKEN_PATH):
        click.echo("Not logged in.")
        return
        
    try:
        os.remove(TOKEN_PATH)
        click.echo("Logged out. Token deleted.")
    except Exception as e:
        click.echo(f"Error during logout: {str(e)}")

if __name__ == "__main__":
    cli() 