#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean up duplicate users and keep only AvishManiar21 for demo.
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Connect to MongoDB Atlas
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    print("ERROR: MONGODB_URI not found in environment")
    exit(1)

client = MongoClient(MONGODB_URI)
db = client.memnexus_db

print("[*] Cleaning up duplicate users...")
print("="*60)

# Delete specific duplicates
duplicates = [
    "sre_AvishManiar21",  # Duplicate/empty user
    "AvishManiar"  # Duplicate without "21"
]

# Keep only AvishManiar21
keep_user = "AvishManiar21"

print(f"\n[*] Users to DELETE: {len(duplicates)}")
for user_id in duplicates:
    print(f"    - {user_id}")

print(f"\n[*] User to KEEP: {keep_user}")
print("\n" + "="*60)

# Delete duplicates
deleted_count = 0
for user_id in duplicates:
    result = db.users.delete_one({"user_id": user_id})
    if result.deleted_count > 0:
        print(f"[OK] Deleted: {user_id}")
        deleted_count += 1
    else:
        print(f"[!] Not found: {user_id}")

print("\n" + "="*60)
print(f"[*] Summary: Deleted {deleted_count}/{len(duplicates)} duplicate users")
print("="*60)

# Verify final state
remaining_users = list(db.users.find())
print(f"\n[*] Remaining users: {len(remaining_users)}")
for user in remaining_users:
    user_id = user.get('user_id', 'Unknown')
    summary = user.get('ai_synthesis_summary', 'No summary')[:80]
    last_active = user.get('last_active', 'Unknown')
    print(f"    - {user_id}")
    print(f"      Summary: {summary}...")
    print(f"      Last active: {last_active}")

client.close()
