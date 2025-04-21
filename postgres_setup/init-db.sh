#!/bin/bash
set -e

# This script initializes the PostgreSQL database for the IR server
# It will be executed when the PostgreSQL container starts for the first time

# Create the vector extension
echo "Creating pgvector extension..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
EOSQL

echo "PostgreSQL initialization completed"