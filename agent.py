# ==============================================================================
# SentinelOps: Autonomous SRE & DevOps Memory Agent API Backend
# Built for Google Cloud Gemini Platform + MongoDB Atlas Vector Search
# ==============================================================================

import os
import sys
import io
import re
import logging
from dotenv import load_dotenv

# Configure robust logging for monitoring
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SentinelOpsAgent")

# Setup memory-based logging capturer for UI traces
log_capture_string = io.StringIO()
ch = logging.StreamHandler(log_capture_string)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

# Load local environment variables if present
load_dotenv()

# ==============================================================================
# DEPENDENCY RESOLUTION & CLIENT INITIALIZATION
# ==============================================================================
try:
    from google import genai
    from google.genai import types
    from google.genai.types import HttpOptions
    from google.cloud import secretmanager
    from pymongo import MongoClient
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ImportError as e:
    logger.error(f"Missing dependency: {e}. Please run 'pip install -r requirements.txt'")
    sys.exit(1)

# ==============================================================================
# PHASE 4: STATE & SECRETS - SECRET MANAGER
# ==============================================================================
def get_mongodb_uri() -> str:
    """Retrieves the MongoDB Connection string dynamically from Secret Manager or environment."""
    use_sm = os.getenv("USE_SECRET_MANAGER", "false").lower() == "true"
    
    if not use_sm:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            logger.warning("MONGODB_URI not found in environment. Defaulting to local instance for testing.")
            return "mongodb://localhost:27017/"
        return uri

    logger.info("Phase 4 Rule: Loading MongoDB Atlas credentials securely from GCP Secret Manager...")
    try:
        project_id = os.getenv("GCP_PROJECT_ID")
        secret_id = os.getenv("SECRET_ID", "mongodb-atlas-uri")
        version_id = os.getenv("SECRET_VERSION", "latest")
        
        if not project_id:
            raise ValueError("GCP_PROJECT_ID is required to use Google Cloud Secret Manager.")
            
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to access Secret Manager: {e}. Falling back to MONGODB_URI environment variable.")
        return os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

# Initialize MongoDB Client & Database (Phase 3 Integration)
MONGO_URI = get_mongodb_uri()
try:
    mongo_client = MongoClient(MONGO_URI)
    # Check connection
    mongo_client.admin.command('ping')
    db = mongo_client["memnexus_db"]
    logger.info("Phase 3: Successfully established connection to MongoDB Atlas database!")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}. Running in simulation/fallback mode.")
    db = None

# ==============================================================================
# PHASE 1: INITIALIZE GOOGLE GEN AI SDK (VERTEX AI MODE)
# ==============================================================================
GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "avish-memnexus-2026")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

try:
    # Initialize the modern unified Gen AI client with Vertex AI parameters
    ai_client = genai.Client(
        http_options=HttpOptions(api_version="v1"),
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION
    )
    logger.info(f"Phase 1: Initialized Google Gen AI Client on project: {GCP_PROJECT} (Location: {GCP_LOCATION})")
except Exception as e:
    logger.error(f"Gen AI Client initialization failed: {e}. Ensure 'gcloud auth application-default login' is run.")
    sys.exit(1)

# ==============================================================================
# PHASE 2 & 3: ACTION MECHANISMS & DATA GROUNDING TOOLS
# ==============================================================================

def search_knowledge_base(query: str) -> str:
    """Searches the enterprise vector database for specific manuals, guides, or rules matching the query.
    
    Args:
        query: The semantic search query.
    """
    logger.info(f"Tool Triggered: search_knowledge_base('{query}')")
    if db is None:
        return "[Simulation Fallback] SRE manual: When a CPU usage spike occurs, the agent executes log analysis, writes a hotfix, and opens a GitLab Merge Request containing code changes."

    try:
        # Vector generation using standard Gen AI embeddings client
        emb_res = ai_client.models.embed_content(
            model="text-embedding-004",
            contents=query
        )
        query_vector = emb_res.embeddings[0].values
        
        # Perform MongoDB Atlas Vector Search aggregation stage
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",          # Configured on Atlas UI
                    "path": "embedding",              # Path of vector field
                    "queryVector": query_vector,
                    "numCandidates": 50,
                    "limit": 3
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "content": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        results = list(db.knowledge_vectors.aggregate(pipeline))
        if not results:
            logger.warning("RAG Vector search yielded no results in database.")
            return "No matching enterprise SRE runbooks were found in the database."
            
        formatted_results = []
        for i, r in enumerate(results):
            formatted_results.append(f"[{i+1}] Title: {r.get('title')}\nContent: {r.get('content')}\nRelevance: {r.get('score'):.4f}\n")
        logger.info(f"RAG search returning {len(results)} matching manuals.")
        return "\n---\n".join(formatted_results)
    except Exception as e:
        logger.error(f"Error querying vector search: {e}")
        return f"Error executing Atlas Vector Search: {str(e)}"

def load_user_memory(user_id: str) -> str:
    """Retrieves persistent long-term memory, profile details, and identity notes for a user from MongoDB.
    
    Args:
        user_id: The unique identifier of the user (e.g. 'AvishManiar21').
    """
    logger.info(f"Tool Triggered: load_user_memory('{user_id}')")
    if db is None:
        return f"User Identity: {user_id}\nPreferences: {{'last_active': '2026-05-29'}}\nMemory Tags: NewParticipant, GCP_SRE_Agent\nAI Memory Synthesis: Lead SRE managing the avish-memnexus-2026 stack."

    try:
        user_record = db.users.find_one({"user_id": user_id})
        if not user_record:
            # Create a default record if none exists
            db.users.insert_one({
                "user_id": user_id,
                "username": user_id,
                "project_role": "Lead DevOps Engineer",
                "memory_tags": ["NewParticipant", "GCP_SRE_Agent"],
                "preferences": {
                    "framework": "Google_Gen_AI_SDK",
                    "active_region": GCP_LOCATION,
                    "last_active": "2026-05-29T22:45:30"
                },
                "ai_synthesis_summary": "Lead SRE Engineer managing the avish-memnexus-2026 stack."
            })
            user_record = db.users.find_one({"user_id": user_id})
        
        pref = user_record.get("preferences", {})
        tags = ", ".join(user_record.get("memory_tags", []))
        summary = user_record.get("ai_synthesis_summary", "Lead SRE Engineer.")
        
        return (
            f"User Identity: {user_id}\n"
            f"Preferences: {pref}\n"
            f"Memory Tags: {tags}\n"
            f"AI Memory Synthesis: {summary}"
        )
    except Exception as e:
        logger.error(f"Failed to load user memory: {e}")
        return f"Error reading database memory: {str(e)}"

def save_chat_history(user_id: str, user_message: str, agent_response: str) -> str:
    """Saves the conversation exchange to MongoDB and aggregates dynamic tags/memory context.
    
    Args:
        user_id: The identifier of the user.
        user_message: The query sent by the user.
        agent_response: The agent response.
    """
    logger.info(f"Tool Triggered: save_chat_history('{user_id}')")
    if db is None:
        return "[Simulation Fallback] Successfully logged chat exchange into memory simulation."

    try:
        from datetime import datetime
        # Append message to sessions log
        db.sessions.insert_one({
            "user_id": user_id,
            "user_message": user_message,
            "agent_response": agent_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update user summary context incrementally
        user_record = db.users.find_one({"user_id": user_id})
        if not user_record:
            db.users.insert_one({
                "user_id": user_id,
                "username": user_id,
                "project_role": "Lead DevOps Engineer",
                "memory_tags": ["NewParticipant", "GCP_SRE_Agent", "ActiveCommunicator"],
                "preferences": {
                    "framework": "Google_Gen_AI_SDK",
                    "active_region": GCP_LOCATION,
                    "last_active": "2026-05-29T22:45:30"
                },
                "ai_synthesis_summary": f"User actively querying about '{user_message[:30]}...'"
            })
        else:
            existing_tags = user_record.get("memory_tags", [])
            new_tag = "ActiveCommunicator"
            if new_tag not in existing_tags:
                existing_tags.append(new_tag)
                
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "memory_tags": existing_tags,
                        "ai_synthesis_summary": f"User is asking about '{user_message[:50]}'. Responses are context-grounded."
                    }
                }
            )
        return "Conversation exchange saved and memory index synthesized in MongoDB Atlas."
    except Exception as e:
        logger.error(f"Failed to write memory: {e}")
        return f"Error writing to MongoDB: {str(e)}"

# ==============================================================================
# PHASE 5: DEPLOYMENT & SAFETY (GUARDRAILS & MODEL SETUP)
# ==============================================================================
safety_settings = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    ),
]

# ==============================================================================
# FLASK WEB REST API BACKEND
# ==============================================================================
app = Flask(__name__)
CORS(app)

def get_captured_traces():
    """Extracts captured log lines from memory to stream dynamically to UI."""
    global log_capture_string
    traces = log_capture_string.getvalue().strip().split('\n')
    # Clear StringIO stream
    log_capture_string.truncate(0)
    log_capture_string.seek(0)
    return [t for t in traces if t.strip()]

def serialize_mongo_doc(doc):
    """Encodes MongoDB ObjectIds and format vectors to visually represent dimensions cleanly."""
    if doc is None:
        return None
    doc_copy = dict(doc)
    if '_id' in doc_copy:
        doc_copy['_id'] = str(doc_copy['_id'])
    if 'embedding' in doc_copy and isinstance(doc_copy['embedding'], list):
        emb = doc_copy['embedding']
        if len(emb) > 6:
            doc_copy['embedding'] = [float(f"{x:.4f}") for x in emb[:6]] + [f"... ({len(emb)} dimensions)"]
    return doc_copy

# User active chat session tracking cache
user_chats = {}

def get_user_chat(user_id):
    """Establishes or fetches the continuous chat session for an SRE user."""
    if user_id not in user_chats:
        mem_init = load_user_memory(user_id)
        logger.info(f"Instantiating model session {GEMINI_MODEL} for {user_id} with grounding tools...")
        user_chats[user_id] = ai_client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                tools=[search_knowledge_base, load_user_memory, save_chat_history],
                safety_settings=safety_settings,
                system_instruction=(
                    f"You are SentinelOps, the autonomous AI SRE agent. "
                    f"You have direct MongoDB Atlas tools. Below is the user context from database:\n{mem_init}\n"
                    f"Respond professionally to diagnostics, vector searches, and operations prompts."
                )
            )
        )
    return user_chats[user_id]

@app.route('/', methods=['GET'])
def api_status():
    return jsonify({
        "status": "online",
        "service": "SentinelOps Agent Backend API",
        "vertex_ai": "connected",
        "mongodb": "connected" if db is not None else "simulation"
    })

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json() or {}
        message = data.get("message")
        user_id = data.get("user_id", "AvishManiar21")
        
        if not message:
            return jsonify({"error": "Message is required."}), 400
            
        logger.info(f"API Request: POST /api/chat from '{user_id}': '{message[:40]}'")
        
        # Clear log capturer string so we only get logs from this single call
        get_captured_traces()
        
        # Query the active Gemini chat session
        chat = get_user_chat(user_id)
        response = chat.send_message(message)
        
        # Persist memory metrics
        save_chat_history(user_id, message, response.text)
        
        # Capture operations logs
        traces = get_captured_traces()
        
        return jsonify({
            "response": response.text,
            "traces": traces
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "error": str(e),
            "traces": get_captured_traces()
        }), 500

@app.route('/api/diagnose', methods=['POST'])
def api_diagnose():
    try:
        data = request.get_json() or {}
        incident_id = data.get("incident_id", "spike")
        description = data.get("description", "Server Latency Spike — us-central1 CPU Usage 98.4%")
        user_id = data.get("user_id", "AvishManiar21")
        
        logger.info(f"API Request: POST /api/diagnose for incident '{incident_id}'")
        
        # Clear log capturer string
        get_captured_traces()
        
        # Build specific instructions for automated incident root cause and code diff generation
        system_prompt = (
            f"You are SentinelOps AI SRE Agent, an autonomous operations specialist. "
            f"Your job is to diagnose the following infrastructure incident:\n'{description}'\n\n"
            f"CRITICAL: You MUST immediately search MongoDB Atlas Vector Search for relevant SRE protocols "
            f"by using the search_knowledge_base tool with a search query like 'SRE protocols' or 'incident response'.\n\n"
            f"Once you fetch the manual, perform root cause analysis, write down your diagnostic trace report, "
            f"and write a precise Git diff patch (hotfix.diff) that resolves the latency regression. "
            f"The patch MUST be enclosed within a standard markdown ```diff ... ``` block. "
            f"Keep the file name in the diff as 'hotfix.py' or 'server.py'."
        )
        
        logger.info("Executing Vertex AI Gemini generateContent for incident diagnosis...")
        response = ai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"Please diagnose incident: {description}. Use tools to find appropriate runbook protocols.",
            config=types.GenerateContentConfig(
                tools=[search_knowledge_base],
                safety_settings=safety_settings,
                system_instruction=system_prompt
            )
        )
        
        diagnosis_text = response.text
        logger.info("Diagnosis generation complete!")
        
        # Extract git diff
        diff_match = re.search(r'```diff\n(.*?)\n```', diagnosis_text, re.DOTALL)
        git_diff = diff_match.group(1) if diff_match else (
            "# SentinelOps AI SRE Agent Diagnostics\n"
            "# Incident: " + description + "\n"
            "# Resolution: No manual code changes required. Restart service."
        )
        
        traces = get_captured_traces()
        return jsonify({
            "diagnosis": diagnosis_text,
            "git_diff": git_diff,
            "traces": traces
        })
    except Exception as e:
        logger.error(f"Error during API diagnosis: {e}")
        return jsonify({
            "error": str(e),
            "traces": get_captured_traces()
        }), 500

@app.route('/api/db/collections', methods=['GET'])
def api_db_collections():
    try:
        if db is None:
            return jsonify({
                "users": [],
                "sessions": [],
                "knowledge_vectors": []
            })
            
        users = list(db.users.find().limit(10))
        sessions = list(db.sessions.find().sort("timestamp", -1).limit(15))
        vectors = list(db.knowledge_vectors.find().limit(10))
        
        serialized_users = [serialize_mongo_doc(u) for u in users]
        serialized_sessions = [serialize_mongo_doc(s) for s in sessions]
        serialized_vectors = [serialize_mongo_doc(v) for v in vectors]
        
        return jsonify({
            "users": serialized_users,
            "sessions": serialized_sessions,
            "knowledge_vectors": serialized_vectors
        })
    except Exception as e:
        logger.error(f"Failed to fetch db collections: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/runbook/ingest', methods=['POST'])
def api_runbook_ingest():
    try:
        data = request.get_json() or {}
        title = data.get("title")
        content = data.get("content")
        
        if not title or not content:
            return jsonify({"error": "Title and Content are required fields."}), 400
            
        logger.info(f"API Ingestion: Uploading runbook '{title}'...")
        
        # Clear log capturer string
        get_captured_traces()
        
        if db is None:
            raise ValueError("MongoDB cluster connection is offline. Ingestion unavailable.")
            
        # Embed runbook text using text-embedding-004
        logger.info("Generating 768-dimension semantic vector via Google text-embedding-004...")
        emb_res = ai_client.models.embed_content(
            model="text-embedding-004",
            contents=content
        )
        vector = emb_res.embeddings[0].values
        
        # Insert document chunk
        payload = {
            "title": title,
            "content": content,
            "embedding": vector
        }
        res = db.knowledge_vectors.insert_one(payload)
        logger.info(f"MongoDB Document indexed successfully! Collection: knowledge_vectors, Doc ID: {res.inserted_id}")
        
        traces = get_captured_traces()
        return jsonify({
            "success": True,
            "doc_id": str(res.inserted_id),
            "traces": traces
        })
    except Exception as e:
        logger.error(f"Failed to ingest manual: {e}")
        return jsonify({
            "error": str(e),
            "traces": get_captured_traces()
        }), 500

# ==============================================================================
# MAIN EXECUTION ROUTINE
# ==============================================================================
if __name__ == "__main__":
    # Check if CLI mode is requested via command line parameter
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        print("\n" + "="*80)
        print("      SentinelOps: Google Cloud Gemini + MongoDB Atlas Memory Agent Terminal      ")
        print("="*80)
        print("Welcome! The SRE Agent is active. Type 'exit' to quit.\n")
        
        user_id = "AvishManiar21"
        print(f"[*] Simulating session for User ID: {user_id}")
        print("[*] Retrieving long-term memory...")
        mem_init = load_user_memory(user_id)
        print(f"[Database Memory Retrieved]:\n{mem_init}\n" + "-"*80 + "\n")
        
        # Establish dynamic Gen AI chat session using the modern client
        logger.info(f"Instantiating model: {GEMINI_MODEL} with safety settings and MongoDB tools...")
        chat = ai_client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                tools=[search_knowledge_base, load_user_memory, save_chat_history],
                safety_settings=safety_settings,
                system_instruction=(
                    f"You are SentinelOps SRE Agent, an advanced enterprise operations assistant. "
                    f"You have tools to access MongoDB Atlas. Below is the user context:\n{mem_init}\n"
                    f"Use tools to fetch manual info or save details if they share important context."
                )
            )
        )
        
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.strip().lower() == "exit":
                    break
                    
                if not user_input.strip():
                    continue
                    
                print("\nThinking (evaluating MongoDB vector indexes and prompt context)...")
                response = chat.send_message(user_input)
                
                print(f"\nSentinelOps: {response.text}")
                
                # Post-chat memory logging
                save_chat_history(user_id, user_input, response.text)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Execution Error: {e}")
                
        print("\nSession logged. Thank you for using SentinelOps!")
    else:
        # Default mode: Start dynamic Flask server on port 5000
        print("\n" + "="*80)
        print("              SentinelOps SRE Agent API Server is launching...              ")
        print("="*80)
        logger.info("Starting Flask web server on http://127.0.0.1:5000/ ...")
        app.run(host="127.0.0.1", port=5000, debug=False)
