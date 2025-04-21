"""
Command-line interface for database migrations.
Provides commands for creating and running migrations.
"""

import os
import sys
import argparse
import logging
import subprocess
from alembic import command
from alembic.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("migration-cli")

# Get the absolute path to the migration directory
MIGRATIONS_DIR = os.path.dirname(os.path.abspath(__file__))
ALEMBIC_INI = os.path.join(MIGRATIONS_DIR, "alembic.ini")

def get_alembic_config():
    """Get the Alembic configuration."""
    if not os.path.exists(ALEMBIC_INI):
        logger.error(f"Alembic configuration file not found: {ALEMBIC_INI}")
        sys.exit(1)
    
    return Config(ALEMBIC_INI)

def check_db_connection():
    """Check if the database connection is working."""
    # We could add a more sophisticated check here
    # For now, we'll rely on Alembic's own connection checks
    logger.info("Database connection will be verified during migration")

def upgrade_command(args):
    """Run database migrations."""
    check_db_connection()
    
    config = get_alembic_config()
    
    if args.revision:
        logger.info(f"Upgrading database to revision {args.revision}")
        command.upgrade(config, args.revision)
    else:
        logger.info("Upgrading database to latest revision")
        command.upgrade(config, "head")
    
    logger.info("Database upgrade complete")

def downgrade_command(args):
    """Downgrade database to a previous revision."""
    check_db_connection()
    
    if not args.revision:
        logger.error("Revision is required for downgrade")
        sys.exit(1)
    
    config = get_alembic_config()
    
    logger.info(f"Downgrading database to revision {args.revision}")
    command.downgrade(config, args.revision)
    
    logger.info("Database downgrade complete")

def revision_command(args):
    """Create a new migration revision."""
    config = get_alembic_config()
    
    if args.message:
        logger.info(f"Creating new migration: {args.message}")
        command.revision(
            config,
            message=args.message,
            autogenerate=args.autogenerate
        )
    else:
        logger.error("Message is required for creating a revision")
        sys.exit(1)
    
    logger.info("Migration revision created")

def init_command(args):
    """Initialize a new Alembic environment."""
    if os.path.exists(os.path.join(MIGRATIONS_DIR, "versions")):
        logger.error("Migrations directory already exists")
        sys.exit(1)
    
    logger.info("Initializing new Alembic environment")
    command.init(get_alembic_config(), MIGRATIONS_DIR)
    logger.info("Alembic environment initialized")

def current_command(args):
    """Show current revision."""
    check_db_connection()
    config = get_alembic_config()
    command.current(config)

def history_command(args):
    """Show migration history."""
    config = get_alembic_config()
    command.history(config)

def main():
    """Main entry point for the migration CLI."""
    parser = argparse.ArgumentParser(description="IR Server Database Migration Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize a new Alembic environment")
    init_parser.set_defaults(func=init_command)
    
    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database to a later version")
    upgrade_parser.add_argument("--revision", "-r", help="Revision to upgrade to (default: head)")
    upgrade_parser.set_defaults(func=upgrade_command)
    
    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database to a previous version")
    downgrade_parser.add_argument("--revision", "-r", required=True, help="Revision to downgrade to")
    downgrade_parser.set_defaults(func=downgrade_command)
    
    # Revision command
    revision_parser = subparsers.add_parser("revision", help="Create a new revision")
    revision_parser.add_argument("--message", "-m", required=True, help="Revision message")
    revision_parser.add_argument("--autogenerate", "-a", action="store_true", help="Auto-generate migration")
    revision_parser.set_defaults(func=revision_command)
    
    # Current command
    current_parser = subparsers.add_parser("current", help="Show current revision")
    current_parser.set_defaults(func=current_command)
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show migration history")
    history_parser.set_defaults(func=history_command)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)

if __name__ == "__main__":
    main()