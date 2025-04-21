import os
# Load .env file variables into environment BEFORE accessing them
import dotenv
dotenv.load_dotenv()

# Microsoft Azure AD / Graph API
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TENANT_ID = os.getenv("AZURE_TENANT_ID")

# DuckDB database file location
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "db/teams_mcp.duckdb")

# Token storage location
TOKEN_PATH = os.getenv("TOKEN_PATH", "db/token_cache.json")

# Polling interval (seconds)
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))

# Demo mode
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true" 