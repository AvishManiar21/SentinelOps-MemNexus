#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Delete test users from MongoDB, keeping only AvishManiar21 for demo.
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

print("[*] Deleting test users from MongoDB...")
print("="*60)

# List of test user IDs to delete
test_users = [
    "sre_AvishManiar21",  # Duplicate
    "judge_test",
    "video_check",
    "demo",
    "test_grounding",
    "grounding_check",
    "model_test_gemini-2.5-pro",
    "model_test_gemini-2.5-flash",
    "recheck_user",
    "deploy_check_3"
]

# Keep only AvishManiar21
keep_user = "AvishManiar21"

print(f"\n[*] Users to DELETE: {len(test_users)}")
for user_id in test_users:
    print(f"    - {user_id}")

print(f"\n[*] User to KEEP: {keep_user}")
print("\n" + "="*60)

# Delete test users
deleted_count = 0
for user_id in test_users:
    result = db.users.delete_one({"user_id": user_id})
    if result.deleted_count > 0:
        print(f"[OK] Deleted: {user_id}")
        deleted_count += 1
    else:
        print(f"[!] Not found: {user_id}")

print("\n" + "="*60)
print(f"[*] Summary: Deleted {deleted_count}/{len(test_users)} test users")
print("="*60)

# Verify final state
remaining_users = list(db.users.find())
print(f"\n[*] Remaining users: {len(remaining_users)}")
for user in remaining_users:
    user_id = user.get('user_id', 'Unknown')
    summary = user.get('ai_synthesis_summary', 'No summary')[:80]
    print(f"    - {user_id}: {summary}...")

client.close()
