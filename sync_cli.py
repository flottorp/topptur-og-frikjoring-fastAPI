#!/usr/bin/env python3
"""
CLI script for syncing members from JSON files
Usage: python sync_cli.py --tf tests/testdata/tf1.json --ntnui tests/testdata/ntnui1.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.database import SessionLocal
from app.services.sync_members import MemberSyncService


def load_json_file(filepath: str):
    """Load and parse JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Sync members from JSON files')
    parser.add_argument('--tf', type=str, help='Path to TF JSON file')
    parser.add_argument('--ntnui', type=str, help='Path to NTNUI JSON file')
    
    args = parser.parse_args()
    
    if not args.tf and not args.ntnui:
        print("Error: At least one of --tf or --ntnui must be provided")
        sys.exit(1)
    
    # Load data
    tf_data = load_json_file(args.tf) if args.tf else None
    ntnui_data = load_json_file(args.ntnui) if args.ntnui else None
    
    if tf_data is None and ntnui_data is None:
        print("Error: Could not load any data files")
        sys.exit(1)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Run sync
        print("Starting member sync...")
        service = MemberSyncService(db)
        result = service.sync_members_from_external(tf_data=tf_data, ntnui_data=ntnui_data)
        
        # Print results
        print(f"\nSync Status: {result['status']}")
        print(f"Members Synced: {result.get('synced_count', 0)}")
        print(f"Message: {result['message']}")
        
        if result['status'] == 'success':
            sys.exit(0)
        else:
            sys.exit(1)
            
    finally:
        db.close()


if __name__ == "__main__":
    main()
