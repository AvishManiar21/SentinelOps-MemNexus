# ==============================================================================
# MemNexus: Grounding Knowledge Base Ingestion Script
# Built for the Google Cloud Rapid Agent Hackathon (MongoDB Atlas Track)
# ==============================================================================
# Generates dense vectors using Google Gen AI Embeddings and uploads them to
# your live MongoDB Atlas Cluster to enable real RAG search!
# ==============================================================================

import os
import sys
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient

# Load configuration
load_dotenv()

GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "avish-memnexus-2026")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    print("[ERROR] MONGODB_URI not found in your .env file! Please set it first.")
    sys.exit(1)

print("\n" + "="*80)
print("             MemNexus Live Grounding Database Ingestion Tool            ")
print("="*80)

# Initialize live clients
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["memnexus_db"]
    # Check connection
    mongo_client.admin.command('ping')
    print("[*] Successfully connected to live MongoDB Atlas cluster!")
except Exception as e:
    print(f"[ERROR] Failed to connect to MongoDB: {e}")
    sys.exit(1)

try:
    ai_client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION
    )
    print("[*] Successfully initialized Google Gen AI Embeddings API!")
except Exception as e:
    print(f"[ERROR] Failed to initialize Gen AI SDK: {e}")
    sys.exit(1)

def ingest_document(title: str, content: str):
    """Embeds the text document and inserts it into the MongoDB Vector search collection."""
    print(f"\n[*] Processing document: '{title}'...")
    print("  -> Generating 768-dimension semantic vector via Google text-embedding-004...")
    
    try:
        # Generate semantic vector using standard Gen AI embeddings
        res = ai_client.models.embed_content(
            model="text-embedding-004",
            contents=content
        )
        vector = res.embeddings[0].values
        
        # Insert document chunk and embedding payload
        payload = {
            "title": title,
            "content": content,
            "embedding": vector
        }
        
        result = db.knowledge_vectors.insert_one(payload)
        print(f"  [+] Document successfully indexed! Collection: 'knowledge_vectors'")
        print(f"  [+] MongoDB Document ID: {result.inserted_id}")
        
    except Exception as e:
        print(f"  [ERROR] Ingestion failed: {e}")

# ==============================================================================
# HACKATHON SAMPLE DOCUMENTS INGESTION
# ==============================================================================
if __name__ == "__main__":
    # Sample 1: SRE Incident Protocols
    sre_manual = (
        "SRE Incident Response Protocol - Phase 4. "
        "When an observability tool (such as Dynatrace) triggers a webhook alert indicating "
        "high server latency or an active CPU spike, the SRE Incident Agent must immediately "
        "execute log analysis, identify the breaking commit in the codebase, write a hotfix, "
        "and automatically open a GitLab Merge Request containing the code resolution."
    )
    
    # Sample 2: Gemini Safety Filter Settings
    safety_manual = (
        "Gemini Safety Filter Configuration Guide - Phase 5. "
        "Configure safety block thresholds inside your application configurations using HarmCategory "
        "definitions. The standard categories include HARM_CATEGORY_HARASSMENT, HARM_CATEGORY_HATE_SPEECH, "
        "and HARM_CATEGORY_DANGEROUS_CONTENT. Set the block threshold to BLOCK_LOW_AND_ABOVE to enforce "
        "strict corporate regulatory and security compliance policies."
    )

    print("\n[*] Ingesting sample grounding documents into your database...")
    ingest_document("SRE Incident Response Protocol", sre_manual)
    ingest_document("Gemini Safety Filter Configuration Guide", safety_manual)
    
    print("\n" + "="*80)
    print("Ingestion complete! Go ahead and test 'agent.py' to search these documents!")
    print("="*80 + "\n")
