#!/usr/bin/env python
"""
R2Storage Fix Script - Removes R2Storage references from Darkbot
"""

import os
import sys
import shutil
import re
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("R2StorageFix")

def backup_file(file_path):
    """Create a backup of the given file."""
    backup_path = f"{file_path}.bak"
    if os.path.exists(backup_path):
        logger.info(f"Backup already exists: {backup_path}")
        return
    
    try:
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    except Exception as e:
        logger.error(f"Failed to create backup of {file_path}: {e}")
        sys.exit(1)

def fix_storage_init():
    """Fix storage/__init__.py to remove R2Storage references."""
    file_path = 'storage/__init__.py'
    
    # Backup the file first
    backup_file(file_path)
    
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if R2Storage is imported
        if 'R2Storage' not in content:
            logger.info(f"No R2Storage references found in {file_path}")
            return
        
        # Remove R2Storage references
        content = re.sub(r'from\s+storage\.r2\s+import\s+R2Storage\s*\n', '', content)
        content = re.sub(r',\s*R2Storage', '', content)
        content = re.sub(r'R2Storage,\s*', '', content)
        content = re.sub(r'R2Storage', '', content)
        
        # Write the updated content back
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Fixed {file_path} - Removed R2Storage references")
    
    except Exception as e:
        logger.error(f"Failed to fix {file_path}: {e}")
        sys.exit(1)

def fix_main_py():
    """Fix main.py to remove R2Storage references."""
    file_path = 'main.py'
    
    # Backup the file first
    backup_file(file_path)
    
    try:
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if R2Storage is imported
        if 'R2Storage' not in content:
            logger.info(f"No R2Storage references found in {file_path}")
            return
        
        # Replace storage import statement
        content = re.sub(
            r'from\s+storage\s+import\s+DealStorage,\s*R2Storage,\s*MongoDBStorage',
            'from storage import DealStorage, MongoDBStorage',
            content
        )
        
        # Remove R2Storage initialization
        content = re.sub(
            r'r2_storage\s*=\s*R2Storage\([^)]*\)\s*\n',
            '',
            content
        )
        
        # Remove R2Storage upload code blocks
        content = re.sub(
            r'if r2_storage is not None and [^:]+:[^}]+r2_storage\.upload_deals\([^)]*\)[^}]+}',
            '',
            content,
            flags=re.DOTALL
        )
        
        # Remove any remaining R2Storage references
        content = re.sub(r'r2_storage\s*=\s*None\s*\n', '', content)
        content = re.sub(r'r2_enabled\s*=\s*[^#\n]+', 'r2_enabled = False', content)
        
        # Write the updated content back
        with open(file_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Fixed {file_path} - Removed R2Storage references")
    
    except Exception as e:
        logger.error(f"Failed to fix {file_path}: {e}")
        sys.exit(1)

def create_healthcheck_script():
    """Create or update the Docker healthcheck script."""
    file_path = 'docker-healthcheck.sh'
    
    # Don't overwrite if it already exists
    if os.path.exists(file_path):
        logger.info(f"{file_path} already exists, skipping creation")
        return
    
    try:
        # Create a simple healthcheck script
        content = """#!/bin/bash
# Docker healthcheck script for Darkbot

# Simple check to see if Python is working properly
python -c "
import sys
import os
import time

# Check that the storage module exists and can be imported
try:
    from storage import DealStorage, MongoDBStorage
    print('Storage modules imported successfully')
    sys.exit(0)
except ImportError as e:
    print(f'Error importing storage modules: {e}')
    sys.exit(1)
except Exception as e:
    print(f'Unexpected error: {e}')
    sys.exit(1)
"
"""
        
        # Write the script
        with open(file_path, 'w') as f:
            f.write(content)
        
        # Make it executable
        os.chmod(file_path, 0o755)
        
        logger.info(f"Created {file_path} - Docker healthcheck script")
    
    except Exception as e:
        logger.error(f"Failed to create {file_path}: {e}")
        sys.exit(1)

def main():
    """Run the fix script."""
    print("=== R2Storage Fix Script ===")
    print("This script will fix R2Storage import errors in Darkbot")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        logger.error("main.py not found - please run this script from the Darkbot directory")
        sys.exit(1)
    
    # Step 1: Fix storage/__init__.py
    print("Step 1: Fixing storage/__init__.py...")
    fix_storage_init()
    
    # Step 2: Fix main.py
    print("\nStep 2: Fixing main.py...")
    fix_main_py()
    
    # Step 3: Create healthcheck script
    print("\nStep 3: Creating Docker healthcheck script...")
    create_healthcheck_script()
    
    # Done
    print("\n=== Fix Complete ===")
    print("The R2Storage references have been removed.")
    print("You can now deploy this version to Railway.")

if __name__ == "__main__":
    main()
