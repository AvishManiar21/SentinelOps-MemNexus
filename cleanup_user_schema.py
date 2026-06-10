#!/usr/bin/env python3
"""
One-time cleanup script to fix user document schema inconsistencies.

Removes legacy fields:
- profile (entire object)
- ai_summary (old fake summary)
- preferences (entire object - was causing duplicate last_active timestamps)

Ensures all users have only:
- last_active (root level, current timestamp)
- ai_synthesis_summary (real Gemini-generated)
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB Atlas
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    print("ERROR: MONGODB_URI not found in environment")
    exit(1)

client = MongoClient(MONGODB_URI)
db = client.sre_knowledge_db

print("🔍 Checking user documents for legacy fields...")

# Find all users
users = list(db.users.find())
print(f"Found {len(users)} user documents\n")

for user in users:
    user_id = user.get('user_id', 'Unknown')
    changes = []

    # Check for legacy fields
    if 'profile' in user:
        changes.append('profile')
    if 'ai_summary' in user:
        changes.append('ai_summary')
    if 'preferences' in user:
        changes.append('preferences')

    if changes:
        print(f"📝 User: {user_id}")
        print(f"   Legacy fields found: {', '.join(changes)}")

        # Build $unset operation to remove legacy fields
        unset_fields = {}
        for field in changes:
            unset_fields[field] = ""

        # Update the document
        result = db.users.update_one(
            {"_id": user["_id"]},
            {"$unset": unset_fields}
        )

        if result.modified_count > 0:
            print(f"   ✅ Removed: {', '.join(changes)}")
        else:
            print(f"   ⚠️  Update failed")
    else:
        print(f"✅ User: {user_id} - Schema already clean")

print("\n" + "="*60)
print("✨ Cleanup complete!")
print("="*60)

# Verify clean schema
print("\n🔍 Verifying clean schema...")
users_after = list(db.users.find())

issues_found = False
for user in users_after:
    user_id = user.get('user_id', 'Unknown')
    problems = []

    if 'profile' in user:
        problems.append('profile still exists')
    if 'ai_summary' in user:
        problems.append('ai_summary still exists')
    if 'preferences' in user:
        problems.append('preferences still exists')
    if 'last_active' not in user:
        problems.append('missing last_active')
    if 'ai_synthesis_summary' not in user:
        problems.append('missing ai_synthesis_summary')

    if problems:
        print(f"⚠️  {user_id}: {', '.join(problems)}")
        issues_found = True

if not issues_found:
    print("✅ All user documents have clean schema!")
    print("\nExpected fields in each user:")
    print("  - user_id")
    print("  - username")
    print("  - project_role")
    print("  - memory_tags")
    print("  - last_active (root level)")
    print("  - ai_synthesis_summary (Gemini-generated)")

client.close()
