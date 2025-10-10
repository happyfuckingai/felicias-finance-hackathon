#!/usr/bin/env python3
"""
Fix import issues in the crypto module for local deployment.
This script systematically fixes relative import paths.
"""

import os
import re
import sys

def fix_import_patterns():
    """Fix common import patterns in crypto module."""

    # Define import fixes
    fixes = [
        # Fix core imports
        (r'from \.\.core\.contracts import', 'from ..core.integrations.contracts import'),
        (r'from \.\.core\.token_resolver import', 'from ..core.token.token_resolver import'),
        (r'from \.\.core\.model_persistence import', 'from ..core.trading.model_persistence import'),
        (r'from \.\.core\.backtester import', 'from ..core.trading.backtester import'),
        (r'from \.\.core\.feature_engineering import', 'from ..core.analytics.feature_engineering import'),
        (r'from \.\.core\.xgboost_trader import', 'from ..core.trading.xgboost_trader import'),

        # Fix relative imports within core
        (r'from \.contracts import', 'from .integrations.contracts import'),
        (r'from \.token_resolver import', 'from .token.token_resolver import'),
        (r'from \.model_persistence import', 'from .trading.model_persistence import'),
        (r'from \.backtester import', 'from .trading.backtester import'),
        (r'from \.feature_engineering import', 'from .analytics.feature_engineering import'),
        (r'from \.xgboost_trader import', 'from .trading.xgboost_trader import'),
    ]

    crypto_dir = 'crypto'
    if not os.path.exists(crypto_dir):
        print(f"Directory {crypto_dir} not found!")
        return

    fixed_files = []

    for root, dirs, files in os.walk(crypto_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)

                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content
                for pattern, replacement in fixes:
                    content = re.sub(pattern, replacement, content)

                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_files.append(filepath)
                    print(f"Fixed imports in: {filepath}")

    print(f"\nFixed {len(fixed_files)} files with import issues.")
    return fixed_files

def fix_remaining_issues():
    """Fix any remaining import issues."""

    # Specific fixes for files that need manual attention
    manual_fixes = [
        # Any specific fixes can go here
    ]

    for filepath, pattern, replacement in manual_fixes:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            content = re.sub(pattern, replacement, content)
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Manual fix applied to: {filepath}")

if __name__ == "__main__":
    print("🔧 Fixing import issues in crypto module...")

    fixed = fix_import_patterns()
    fix_remaining_issues()

    print("✅ Import fixes completed!")
    print(f"Fixed {len(fixed)} files.")

    # Test if we can import the main modules
    print("\n🧪 Testing imports...")
    try:
        sys.path.insert(0, '.')
        import crypto
        print("✅ Main crypto module imports successfully")
    except Exception as e:
        print(f"❌ Main module still has issues: {e}")

    try:
        import crypto.handlers
        print("✅ Handlers module imports successfully")
    except Exception as e:
        print(f"❌ Handlers module still has issues: {e}")