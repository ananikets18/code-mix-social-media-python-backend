"""Migration Script for Preprocessing Modularization

This script helps migrate from the monolithic preprocessing.py to the modular structure.

Steps:
1. Backs up the original preprocessing.py
2. Replaces it with the new facade
3. Validates imports in key files
4. Runs basic smoke tests

Run this script to complete the migration:
    python migrate_preprocessing.py
"""

import os
import shutil
import sys

def migrate():
    """Perform the migration"""
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    print("=" * 70)
    print("PREPROCESSING MODULARIZATION MIGRATION")
    print("=" * 70)
    print()
    
    # Step 1: Verify new structure exists
    preprocessing_dir = os.path.join(base_path, "preprocessing")
    if not os.path.exists(preprocessing_dir):
        print("❌ ERROR: preprocessing/ directory not found!")
        print("   Please ensure the modular structure is created first.")
        return False
    
    print("✅ Step 1: Verified preprocessing/ package exists")
    
    # Step 2: Check if backup already exists
    backup_file = os.path.join(base_path, "preprocessing_original_backup.py")
    original_file = os.path.join(base_path, "preprocessing.py")
    new_facade = os.path.join(base_path, "preprocessing_new_facade.py")
    
    if not os.path.exists(backup_file):
        if os.path.exists(original_file):
            print(f"📦 Step 2: Creating backup of original preprocessing.py...")
            shutil.copy2(original_file, backup_file)
            print(f"   → Backup saved as: preprocessing_original_backup.py")
        else:
            print("⚠️  Warning: Original preprocessing.py not found")
    else:
        print("✅ Step 2: Backup already exists (preprocessing_original_backup.py)")
    
    # Step 3: Replace with facade
    if os.path.exists(new_facade):
        print(f"🔄 Step 3: Replacing preprocessing.py with facade...")
        shutil.copy2(new_facade, original_file)
        print(f"   → preprocessing.py is now a lightweight facade")
    else:
        print("❌ ERROR: preprocessing_new_facade.py not found!")
        return False
    
    # Step 4: Verify imports work
    print(f"🔍 Step 4: Verifying imports...")
    try:
        # Clear any cached imports
        if 'preprocessing' in sys.modules:
            del sys.modules['preprocessing']
        
        # Test importing
        from preprocessing import (
            detect_language,
            preprocess_text,
            detect_code_mixing,
            normalize_language_code,
            INDIAN_LANGUAGES
        )
        print("   ✅ Main imports working correctly")
        
        # Test a function call
        result = detect_language("Hello world", detailed=False)
        print(f"   ✅ Basic function call working (detected: {result})")
        
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False
    
    print()
    print("=" * 70)
    print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Run tests: pytest tests/")
    print("2. Check that your application still works")
    print("3. If issues arise, restore from: preprocessing_original_backup.py")
    print()
    print("The new modular structure:")
    print("  preprocessing/")
    print("  ├── __init__.py")
    print("  ├── language_constants.py")
    print("  ├── detection_config.py")
    print("  ├── script_detection.py")
    print("  ├── romanized_detection.py")
    print("  ├── code_mixing_detection.py")
    print("  ├── glotlid_detection.py")
    print("  ├── language_utils.py")
    print("  ├── language_detection.py")
    print("  └── text_preprocessing_core.py")
    print()
    
    return True


def rollback():
    """Rollback the migration"""
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    backup_file = os.path.join(base_path, "preprocessing_original_backup.py")
    original_file = os.path.join(base_path, "preprocessing.py")
    
    if not os.path.exists(backup_file):
        print("❌ ERROR: Backup file not found!")
        print("   Cannot rollback without preprocessing_original_backup.py")
        return False
    
    print("🔄 Rolling back to original preprocessing.py...")
    shutil.copy2(backup_file, original_file)
    print("✅ Rollback complete!")
    print(f"   Restored from: {backup_file}")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate preprocessing.py to modular structure")
    parser.add_argument("--rollback", action="store_true", help="Rollback to original preprocessing.py")
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback()
    else:
        success = migrate()
    
    sys.exit(0 if success else 1)
