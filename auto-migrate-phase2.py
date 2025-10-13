#!/usr/bin/env python3
"""
Automatic Phase 2 Migration Script
Migrates all Python files to use security modules
"""

import os
import re
import shutil
from pathlib import Path

# Files to migrate
FILES_TO_MIGRATE = [
    "infoblox-rag-builder.py",
    "claude-chat-rag.py",
    "claude-chat-infoblox.py",
    "claude-chat-mcp.py",
    "claude-agent.py",
    "infoblox-explorer.py",
    "claude-chat.py",
    "claude-cli.py"
]

BASE_DIR = Path(__file__).parent

# Backup directory
BACKUP_DIR = BASE_DIR / "backups_phase2"
BACKUP_DIR.mkdir(exist_ok=True)

# Import template to add at top of files
SECURITY_IMPORTS = '''
# Import security modules
from config import get_settings
from logging_config import setup_logging, get_security_logger
from validators import InputValidator, ValidationError
import logging

# Load secure configuration
settings = get_settings()

# Setup logging
setup_logging(
    log_level=settings.log_level,
    enable_security_audit=True
)

logger = logging.getLogger(__name__)
security_logger = get_security_logger()

# Display SSL warning if disabled
settings.display_security_warning()
'''

def backup_file(filepath):
    """Backup original file"""
    shutil.copy2(filepath, BACKUP_DIR / filepath.name)
    print(f"✓ Backed up: {filepath.name}")

def remove_insecure_config(content):
    """Remove hardcoded credentials and SSL suppression"""
    # Remove SSL warning suppression
    content = re.sub(
        r'requests\.packages\.urllib3\.disable_warnings\([^)]+\)\s*\n',
        '',
        content
    )
    content = re.sub(
        r'from urllib3\.exceptions import InsecureRequestWarning\s*\n',
        '',
        content
    )

    # Remove hardcoded credentials
    content = re.sub(
        r'INFOBLOX_HOST\s*=\s*os\.getenv\(["\']INFOBLOX_HOST["\'],\s*["\'][^"\']+["\']\)',
        '# Configuration moved to config.py',
        content
    )
    content = re.sub(
        r'INFOBLOX_USER\s*=\s*os\.getenv\(["\']INFOBLOX_USER["\'],\s*["\'][^"\']+["\']\)',
        '',
        content
    )
    content = re.sub(
        r'INFOBLOX_PASSWORD\s*=\s*os\.getenv\(["\']INFOBLOX_PASSWORD["\'],\s*["\'][^"\']+["\']\)',
        '',
        content
    )
    content = re.sub(
        r'WAPI_VERSION\s*=\s*os\.getenv\(["\']WAPI_VERSION["\'],\s*["\'][^"\']+["\']\)',
        '',
        content
    )
    content = re.sub(
        r'ANTHROPIC_API_KEY\s*=\s*os\.getenv\(["\']ANTHROPIC_API_KEY["\'],\s*["\'][^"\']+["\']\)',
        '',
        content
    )

    # Remove verify=False
    content = re.sub(
        r'\.verify\s*=\s*False',
        '.verify = settings.get_ssl_verify()',
        content
    )
    content = re.sub(
        r'verify\s*=\s*False',
        'verify=settings.get_ssl_verify()',
        content
    )

    return content

def add_security_imports(content):
    """Add security imports after docstring"""
    # Find end of docstring
    if '"""' in content:
        parts = content.split('"""', 2)
        if len(parts) >= 3:
            return parts[0] + '"""' + parts[1] + '"""' + SECURITY_IMPORTS + parts[2]

    # If no docstring, add at beginning
    return SECURITY_IMPORTS + content

def replace_config_vars(content):
    """Replace config variables with settings"""
    replacements = {
        'INFOBLOX_HOST': 'settings.infoblox_host',
        'INFOBLOX_USER': 'settings.infoblox_user',
        'INFOBLOX_PASSWORD': 'settings.infoblox_password',
        'WAPI_VERSION': 'settings.wapi_version',
        'ANTHROPIC_API_KEY': 'settings.anthropic_api_key',
    }

    for old, new in replacements.items():
        # Replace only standalone variable references, not in assignments
        content = re.sub(
            rf'\b{old}\b(?!\s*=)',
            new,
            content
        )

    return content

def add_logging(content):
    """Add logging statements"""
    # Replace print statements with logging
    content = re.sub(
        r'print\(f?"([^"]+)"\)',
        r'logger.info("\1")\n    print("\1")  # Keep print for console output',
        content
    )

    return content

def migrate_file(filepath):
    """Migrate a single file"""
    print(f"\nMigrating: {filepath.name}")
    print("=" * 60)

    # Backup
    backup_file(filepath)

    # Read file
    with open(filepath, 'r') as f:
        content = f.read()

    # Apply migrations
    print("  • Removing insecure configuration...")
    content = remove_insecure_config(content)

    print("  • Adding security imports...")
    content = add_security_imports(content)

    print("  • Replacing config variables...")
    content = replace_config_vars(content)

    print("  • Adding logging...")
    content = add_logging(content)

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"✓ Migration complete: {filepath.name}")
    return True

def main():
    print("=" * 60)
    print("Phase 2 Automatic Migration Script")
    print("=" * 60)
    print()

    migrated = []
    failed = []

    for filename in FILES_TO_MIGRATE:
        filepath = BASE_DIR / filename

        if not filepath.exists():
            print(f"⚠ File not found: {filename}")
            failed.append(filename)
            continue

        try:
            if migrate_file(filepath):
                migrated.append(filename)
        except Exception as e:
            print(f"✗ Error migrating {filename}: {e}")
            failed.append(filename)

    # Summary
    print()
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"✓ Successfully migrated: {len(migrated)} files")
    for f in migrated:
        print(f"  • {f}")

    if failed:
        print(f"\n✗ Failed: {len(failed)} files")
        for f in failed:
            print(f"  • {f}")

    print()
    print(f"Backups saved to: {BACKUP_DIR}")
    print()
    print("Next steps:")
    print("  1. Review migrated files")
    print("  2. Test each script")
    print("  3. Run integration tests")
    print("  4. Commit changes")

if __name__ == "__main__":
    main()
