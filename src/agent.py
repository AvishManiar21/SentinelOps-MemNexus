# ==============================================================================
# SentinelOps: Autonomous SRE & DevOps Memory Agent API Backend
# Built for Google Cloud Gemini Platform + MongoDB Atlas Vector Search
# ==============================================================================

import os
import sys
import io
import re
import logging
import json
import subprocess
import threading
import atexit
from threading import local
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

# Thread-local storage for grounding sources (vector search results)
thread_local = local()

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
    from google.cloud import storage
    from google.cloud import logging as cloud_logging
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
# MONGODB MCP SERVER CLIENT (Hackathon Compliance Requirement)
# ==============================================================================
class MongoDBMCPClient:
    """
    MongoDB MCP Server Client - Hackathon Compliance Integration

    Manages communication with the official MongoDB MCP server (@mongodb-js/mongodb-mcp-server)
    using JSON-RPC 2.0 protocol over stdin/stdout pipes.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.process = None
        self.message_id = 0
        self.available_tools = []
        self.lock = threading.Lock()
        self.initialized = False

    def start(self, timeout: int = 30):
        """Launch the MongoDB MCP server as a subprocess with timeout"""
        try:
            logger.info("[MCP] Launching MongoDB MCP server via npx...")

            # Determine if we need shell=True for Windows compatibility
            is_windows = os.name == "nt"

            # Launch MCP server with connection string
            # On Windows, npx is npx.cmd and requires shell=True
            # Use direct command if globally installed, otherwise use npx with correct package name
            mcp_cmd = ["mongodb-mcp-server"] if not is_windows else ["npx", "-y", "mongodb-mcp-server"]

            self.process = subprocess.Popen(
                mcp_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr to log errors
                text=True,
                bufsize=1,
                shell=is_windows,
                env={
                    **os.environ,
                    "MONGODB_URI": self.connection_string,
                    "MDB_MCP_CONNECTION_STRING": self.connection_string
                }
            )

            # Log any stderr output for debugging
            if self.process.stderr:
                def log_stderr():
                    try:
                        for line in self.process.stderr:
                            if line.strip():
                                logger.warning(f"[MCP stderr] {line.strip()}")
                    except:
                        pass

                stderr_thread = threading.Thread(target=log_stderr, daemon=True)
                stderr_thread.start()

            # Perform MCP initialization handshake with timeout
            init_success = []
            init_error = []

            def initialize():
                try:
                    self._initialize_connection()
                    init_success.append(True)
                except Exception as e:
                    init_error.append(e)

            init_thread = threading.Thread(target=initialize, daemon=True)
            init_thread.start()
            init_thread.join(timeout=timeout)

            if init_thread.is_alive():
                logger.error(f"[MCP] Initialization timed out after {timeout}s")
                self.stop()
                return False

            if init_error:
                logger.error(f"[MCP] Initialization failed: {init_error[0]}")
                self.stop()
                return False

            if not init_success:
                logger.error("[MCP] Initialization completed but no success signal")
                self.stop()
                return False

            # Register cleanup on exit
            atexit.register(self.stop)

            logger.info(f"[MCP] MongoDB MCP server started successfully. Available tools: {len(self.available_tools)}")
            return True

        except FileNotFoundError as e:
            logger.error(f"[MCP] npx command not found. Please ensure Node.js and npm are installed: {e}")
            return False
        except Exception as e:
            logger.error(f"[MCP] Failed to start MongoDB MCP server: {e}")
            return False

    def _send_request(self, method: str, params: dict = None, timeout: int = 10) -> dict:
        """Send JSON-RPC 2.0 request to MCP server with timeout"""
        with self.lock:
            # Check if process is still alive
            if self.process and self.process.poll() is not None:
                logger.error("[MCP] MCP server process has terminated unexpectedly")
                return None

            self.message_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self.message_id,
                "method": method
            }
            if params:
                request["params"] = params

            try:
                request_json = json.dumps(request) + "\n"
                self.process.stdin.write(request_json)
                self.process.stdin.flush()

                # Read response with timeout using threading
                response_container = []
                error_container = []

                def read_response():
                    try:
                        while True:
                            line = self.process.stdout.readline()
                            if not line:
                                break
                            try:
                                data = json.loads(line)
                                if isinstance(data, dict) and data.get("id") == self.message_id:
                                    response_container.append(line)
                                    break
                                else:
                                    logger.info(f"[MCP Message/Notification] {line.strip()}")
                            except json.JSONDecodeError:
                                logger.warning(f"[MCP Raw Output] {line.strip()}")
                    except Exception as e:
                        error_container.append(e)

                reader_thread = threading.Thread(target=read_response, daemon=True)
                reader_thread.start()
                reader_thread.join(timeout=timeout)

                if reader_thread.is_alive():
                    logger.error(f"[MCP] Request '{method}' timed out after {timeout}s")
                    return None

                if error_container:
                    logger.error(f"[MCP] Read error: {error_container[0]}")
                    return None

                if not response_container or not response_container[0]:
                    logger.error("[MCP] Empty response from MCP server")
                    return None

                response = json.loads(response_container[0])

                if "error" in response:
                    logger.error(f"[MCP] Error response: {response['error']}")
                    return None

                return response.get("result")

            except BrokenPipeError:
                logger.error("[MCP] Connection to MCP server broken")
                return None
            except Exception as e:
                logger.error(f"[MCP] Request failed for {method}: {e}")
                return None

    def _send_notification(self, method: str, params: dict = None):
        """Send JSON-RPC 2.0 notification (no id, no response expected)"""
        with self.lock:
            if self.process and self.process.poll() is not None:
                return
            notification = {
                "jsonrpc": "2.0",
                "method": method
            }
            if params:
                notification["params"] = params
            try:
                self.process.stdin.write(json.dumps(notification) + "\n")
                self.process.stdin.flush()
            except Exception as e:
                logger.warning(f"[MCP] Failed to send notification {method}: {e}")

    def _initialize_connection(self):
        """Perform MCP initialization handshake"""
        try:
            # Step 1: Initialize
            init_result = self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "sentinelops-agent",
                    "version": "1.0.0"
                }
            })

            if not init_result:
                raise Exception("Initialize request failed")

            # Step 2: Initialized notification
            self._send_notification("notifications/initialized")

            # Step 3: List available tools
            tools_result = self._send_request("tools/list")
            if tools_result and "tools" in tools_result:
                self.available_tools = tools_result["tools"]
                logger.info(f"[MCP] Discovered {len(self.available_tools)} tools from MCP server")

            self.initialized = True

        except Exception as e:
            logger.error(f"[MCP] Initialization failed: {e}")
            raise

    def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool and return the result"""
        if not self.initialized:
            return "MCP server not initialized"

        try:
            logger.info(f"[MCP] Calling tool: {tool_name} with args: {arguments}")

            result = self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })

            if result and "content" in result:
                # Extract text content from response
                content_items = result["content"]
                if isinstance(content_items, list) and len(content_items) > 0:
                    return content_items[0].get("text", str(result))
                return str(result)

            return str(result) if result else "No result from MCP server"

        except Exception as e:
            logger.error(f"[MCP] Tool call failed: {e}")
            return f"Error: {str(e)}"

    def list_tools(self) -> list:
        """Return list of available tools"""
        return self.available_tools

    def stop(self):
        """Stop the MCP server subprocess"""
        if self.process:
            try:
                # Close stdin if still open
                if self.process.stdin and not self.process.stdin.closed:
                    self.process.stdin.close()

                # Terminate gracefully
                self.process.terminate()

                try:
                    self.process.wait(timeout=5)
                    logger.info("[MCP] MongoDB MCP server stopped gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning("[MCP] MCP server did not terminate gracefully, forcing kill")
                    self.process.kill()
                    self.process.wait()
                    logger.info("[MCP] MongoDB MCP server killed")

            except Exception as e:
                logger.error(f"[MCP] Error stopping MCP server: {e}")
                try:
                    self.process.kill()
                except:
                    pass

# Initialize MongoDB MCP Client (with timeout for Cloud Run)
mcp_client = None
if db is not None and MONGO_URI:
    try:
        logger.info("[MCP] Attempting MCP server initialization with 30s timeout")
        mcp_client = MongoDBMCPClient(MONGO_URI)
        if mcp_client.start(timeout=30):
            logger.info("[MCP] MongoDB MCP integration active for hackathon compliance")
        else:
            logger.warning("[MCP] MCP server failed to start, continuing without MCP features")
            mcp_client = None
    except Exception as e:
        logger.warning(f"[MCP] Could not initialize MCP client: {e}")
        mcp_client = None

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
# GOOGLE CLOUD LOGGING: ENTERPRISE AUDIT TRAILS
# ==============================================================================
cloud_logger = None

try:
    logging_client = cloud_logging.Client(project=GCP_PROJECT)
    cloud_logger = logging_client.logger("sentinelops-agent")
    logger.info(f"Google Cloud Logging initialized for project: {GCP_PROJECT}")
except Exception as e:
    logger.warning(f"Failed to initialize Cloud Logging: {e}. Audit trails will use local logging only.")

def log_to_cloud(event_type: str, message: str, severity: str = "INFO", **metadata):
    """Logs structured events to Google Cloud Logging for enterprise audit trails.

    Args:
        event_type: Type of event (e.g., "chat_request", "vector_search", "diagnosis")
        message: Human-readable log message
        severity: Log severity (DEFAULT, INFO, WARNING, ERROR, CRITICAL)
        **metadata: Additional structured data to log
    """
    if cloud_logger is None:
        return

    try:
        struct_data = {
            "event_type": event_type,
            "message": message,
            **metadata
        }
        cloud_logger.log_struct(struct_data, severity=severity)
    except Exception as e:
        logger.warning(f"Failed to write to Cloud Logging: {e}")

# ==============================================================================
# GOOGLE CLOUD STORAGE: RUNBOOK BACKUP & PERSISTENCE
# ==============================================================================
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", f"{GCP_PROJECT}-runbooks")
gcs_client = None

try:
    gcs_client = storage.Client(project=GCP_PROJECT)
    logger.info(f"Google Cloud Storage client initialized for project: {GCP_PROJECT}")
except Exception as e:
    logger.warning(f"Failed to initialize GCS client: {e}. Runbook backups will be disabled.")

def upload_to_gcs(title: str, content: str) -> str:
    """Uploads runbook content to Google Cloud Storage for backup and persistence.

    Args:
        title: The title/filename of the runbook
        content: The text content to store

    Returns:
        The public GCS URL or error message
    """
    if gcs_client is None:
        return "GCS not available"

    try:
        # Get or create bucket
        bucket = gcs_client.bucket(GCS_BUCKET_NAME)
        if not bucket.exists():
            bucket = gcs_client.create_bucket(GCS_BUCKET_NAME, location=GCP_LOCATION)
            logger.info(f"Created new GCS bucket: {GCS_BUCKET_NAME}")

        # Create blob with timestamp
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_title = title.replace(" ", "_").replace("/", "-")
        blob_name = f"runbooks/{timestamp}_{safe_title}.txt"

        blob = bucket.blob(blob_name)
        blob.upload_from_string(content, content_type='text/plain')

        gcs_url = f"gs://{GCS_BUCKET_NAME}/{blob_name}"
        logger.info(f"Successfully uploaded runbook to GCS: {gcs_url}")
        return gcs_url
    except Exception as e:
        logger.error(f"Failed to upload to GCS: {e}")
        return f"GCS upload failed: {str(e)}"

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

        # Store grounding sources in thread-local storage for UI display
        grounding_sources = []
        for r in results:
            grounding_sources.append({
                "title": r.get('title'),
                "score": round(r.get('score', 0), 4)
            })
        thread_local.grounding_sources = grounding_sources

        formatted_results = []
        for i, r in enumerate(results):
            formatted_results.append(f"[{i+1}] Title: {r.get('title')}\nContent: {r.get('content')}\nRelevance: {r.get('score'):.4f}\n")
        logger.info(f"RAG search returning {len(results)} matching manuals.")

        # Log vector search to Cloud Logging
        log_to_cloud(
            event_type="vector_search",
            message=f"Vector search executed for query",
            severity="INFO",
            query_preview=query[:100],
            results_count=len(results),
            top_score=results[0].get('score', 0) if results else 0
        )

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

def _generate_ai_memory_summary(user_id: str, recent_messages: list, conversation_count: int) -> str:
    """Uses Gemini to generate an intelligent memory summary for a user based on conversation history.

    Args:
        user_id: The user identifier
        recent_messages: List of recent conversation messages
        conversation_count: Total number of conversations

    Returns:
        AI-generated summary string
    """
    try:
        # Build context from recent messages
        conversation_context = "\n".join([
            f"User: {msg.get('user_message', '')[:100]}\nAgent: {msg.get('agent_response', '')[:100]}"
            for msg in recent_messages[-3:]  # Last 3 conversations
        ])

        prompt = f"""Analyze this user's conversation history and create a concise 1-sentence memory summary (max 80 chars).

User ID: {user_id}
Total Conversations: {conversation_count}

Recent exchanges:
{conversation_context}

Generate a brief, factual summary of their interests/needs. Examples:
- "SRE engineer troubleshooting MongoDB connection issues"
- "DevOps lead implementing observability for production systems"
- "Developer exploring vector search and AI agent patterns"

Summary:"""

        # Use Gemini Flash for quick summarization
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        summary = response.text.strip().strip('"').strip("'")

        # Truncate to 100 chars max
        if len(summary) > 100:
            summary = summary[:97] + "..."

        return summary
    except Exception as e:
        logger.error(f"AI synthesis failed: {e}")
        return f"Active user with {conversation_count} conversation(s)"

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

        # Get recent conversation history for AI synthesis
        recent_sessions = list(db.sessions.find({"user_id": user_id}).sort("timestamp", -1).limit(5))
        conversation_count = db.sessions.count_documents({"user_id": user_id})

        # Generate AI-powered memory summary
        ai_summary = _generate_ai_memory_summary(user_id, recent_sessions, conversation_count)

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
                    "last_active": datetime.utcnow().isoformat()
                },
                "ai_synthesis_summary": ai_summary
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
                        "ai_synthesis_summary": ai_summary,
                        "last_active": datetime.utcnow().isoformat()
                    }
                }
            )
        return "Conversation exchange saved and AI memory synthesis completed in MongoDB Atlas."
    except Exception as e:
        logger.error(f"Failed to write memory: {e}")
        return f"Error writing to MongoDB: {str(e)}"

def execute_mongodb_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Execute MongoDB MCP server tools for advanced database operations.

    This tool provides direct access to the official MongoDB MCP server for:
    - Database queries and aggregation pipelines
    - Schema inspection and collection management
    - Index operations and performance analysis

    Args:
        tool_name: Name of the MCP tool to execute (e.g., 'find', 'aggregate', 'listCollections')
        arguments: Dictionary of tool arguments specific to the chosen tool

    Returns:
        Result string from the MCP server execution
    """
    logger.info(f"[MCP Tool] Triggered: execute_mongodb_mcp_tool('{tool_name}')")

    if not mcp_client or not mcp_client.initialized:
        logger.warning("[MCP Tool] MCP server not available for this request")
        return "MCP server not available. Please ensure MongoDB MCP server is running."

    try:
        logger.info(f"[MCP Tool] Delegating to MongoDB MCP server: {tool_name} with args: {arguments}")
        result = mcp_client.call_tool(tool_name, arguments)
        logger.info(f"[MCP Tool] Result received: {result[:200]}..." if len(result) > 200 else f"[MCP Tool] Result: {result}")
        return result
    except Exception as e:
        logger.error(f"[MCP Tool] Execution failed: {e}")
        return f"Error executing MCP tool '{tool_name}': {str(e)}"

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

def get_user_chat(user_id, model=None):
    """Establishes or fetches the continuous chat session for an SRE user.

    Args:
        user_id: User identifier
        model: Gemini model to use (gemini-2.5-flash or gemini-2.5-pro). If None, uses default.
    """
    # Use default model if not specified
    if model is None:
        model = GEMINI_MODEL

    # Validate model
    valid_models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-exp"]
    if model not in valid_models:
        logger.warning(f"Invalid model '{model}' requested. Falling back to {GEMINI_MODEL}")
        model = GEMINI_MODEL

    # Create unique cache key for user + model combination
    cache_key = f"{user_id}:{model}"

    if cache_key not in user_chats:
        mem_init = load_user_memory(user_id)
        logger.info(f"Instantiating model session {model} for {user_id} with grounding tools...")

        # Build tools list - include MCP tool if available
        tools_list = [search_knowledge_base, load_user_memory, save_chat_history]
        if mcp_client and mcp_client.initialized:
            tools_list.append(execute_mongodb_mcp_tool)
            logger.info(f"[MCP] MongoDB MCP tool registered with Gemini for {user_id}")

        user_chats[cache_key] = ai_client.chats.create(
            model=model,
            config=types.GenerateContentConfig(
                tools=tools_list,
                safety_settings=safety_settings,
                system_instruction=(
                    f"You are SentinelOps, the autonomous AI SRE agent. "
                    f"You have direct MongoDB Atlas tools. Below is the user context from database:\n{mem_init}\n"
                    f"Respond professionally to diagnostics, vector searches, and operations prompts."
                )
            )
        )
    return user_chats[cache_key]

@app.route('/', methods=['GET'])
def api_status():
    return jsonify({
        "status": "online",
        "service": "SentinelOps Agent Backend API",
        "vertex_ai": "connected",
        "mongodb": "connected" if db is not None else "simulation"
    })

@app.route('/api/health', methods=['GET'])
def api_health():
    """Comprehensive system health check endpoint for status monitoring."""
    try:
        health_status = {
            "timestamp": None,
            "overall_status": "online",
            "services": {
                "backend": {"status": "online", "message": "Flask API operational"},
                "vertex_ai": {"status": "unknown", "message": "Not tested"},
                "mongodb": {"status": "unknown", "message": "Not tested"},
                "mcp_server": {"status": "unknown", "message": "Not tested"}
            }
        }

        from datetime import datetime
        health_status["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Check MongoDB connection
        if db is not None:
            try:
                mongo_client.admin.command('ping')
                health_status["services"]["mongodb"]["status"] = "online"
                health_status["services"]["mongodb"]["message"] = "MongoDB Atlas connected"
            except Exception as e:
                health_status["services"]["mongodb"]["status"] = "offline"
                health_status["services"]["mongodb"]["message"] = f"Connection failed: {str(e)[:50]}"
                health_status["overall_status"] = "degraded"
        else:
            health_status["services"]["mongodb"]["status"] = "offline"
            health_status["services"]["mongodb"]["message"] = "No MongoDB connection configured"
            health_status["overall_status"] = "degraded"

        # Check Vertex AI connection
        try:
            # Quick test to verify AI client is initialized
            if ai_client:
                health_status["services"]["vertex_ai"]["status"] = "online"
                health_status["services"]["vertex_ai"]["message"] = f"Gemini {GEMINI_MODEL} ready"
            else:
                health_status["services"]["vertex_ai"]["status"] = "offline"
                health_status["services"]["vertex_ai"]["message"] = "AI client not initialized"
                health_status["overall_status"] = "degraded"
        except Exception as e:
            health_status["services"]["vertex_ai"]["status"] = "offline"
            health_status["services"]["vertex_ai"]["message"] = f"Error: {str(e)[:50]}"
            health_status["overall_status"] = "degraded"

        # Check MCP server status
        if mcp_client and mcp_client.initialized:
            try:
                # Check if process is still running
                if mcp_client.process and mcp_client.process.poll() is None:
                    health_status["services"]["mcp_server"]["status"] = "online"
                    health_status["services"]["mcp_server"]["message"] = f"MongoDB MCP active ({len(mcp_client.available_tools)} tools)"
                else:
                    health_status["services"]["mcp_server"]["status"] = "offline"
                    health_status["services"]["mcp_server"]["message"] = "MCP process terminated"
                    health_status["overall_status"] = "degraded"
            except Exception as e:
                health_status["services"]["mcp_server"]["status"] = "offline"
                health_status["services"]["mcp_server"]["message"] = f"Status check failed: {str(e)[:50]}"
                health_status["overall_status"] = "degraded"
        else:
            health_status["services"]["mcp_server"]["status"] = "offline"
            health_status["services"]["mcp_server"]["message"] = "MCP server not initialized"

        # Determine overall status
        statuses = [service["status"] for service in health_status["services"].values()]
        if all(s == "online" for s in statuses):
            health_status["overall_status"] = "online"
        elif all(s == "offline" for s in statuses):
            health_status["overall_status"] = "offline"
        else:
            health_status["overall_status"] = "degraded"

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overall_status": "offline",
            "error": str(e)
        }), 500

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json() or {}
        message = data.get("message")
        user_id = data.get("user_id", "AvishManiar21")
        model = data.get("model", GEMINI_MODEL)  # Support model selection

        if not message:
            return jsonify({"error": "Message is required."}), 400

        logger.info(f"API Request: POST /api/chat from '{user_id}' using {model}: '{message[:40]}'")

        # Clear log capturer string and grounding sources for this request
        get_captured_traces()
        thread_local.grounding_sources = []

        # Query the active Gemini chat session with selected model
        chat = get_user_chat(user_id, model)
        response = chat.send_message(message)

        # Persist memory metrics
        save_chat_history(user_id, message, response.text)

        # Log to Cloud Logging for audit trail
        log_to_cloud(
            event_type="chat_request",
            message=f"User {user_id} sent chat message",
            severity="INFO",
            user_id=user_id,
            model=model,
            query_preview=message[:100],
            response_length=len(response.text)
        )

        # Capture operations logs and grounding sources
        traces = get_captured_traces()
        grounding_sources = getattr(thread_local, 'grounding_sources', [])

        return jsonify({
            "response": response.text,
            "model_used": model,
            "traces": traces,
            "grounding_sources": grounding_sources
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
        model = data.get("model", GEMINI_MODEL)  # Support model selection for diagnostics

        logger.info(f"API Request: POST /api/diagnose for incident '{incident_id}' using {model}")
        
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
        
        logger.info(f"Executing Vertex AI Gemini generateContent for incident diagnosis with {model}...")
        response = ai_client.models.generate_content(
            model=model,
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

        # Log incident diagnosis to Cloud Logging
        log_to_cloud(
            event_type="incident_diagnosis",
            message=f"Generated diagnosis for incident: {incident_id}",
            severity="WARNING",
            user_id=user_id,
            model=model,
            incident_id=incident_id,
            incident_description=description,
            has_hotfix=diff_match is not None
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

@app.route('/api/webhook/alert', methods=['POST'])
def api_webhook_alert():
    """Webhook endpoint for receiving observability alerts (requires authentication).

    Accepts JSON payloads from monitoring systems (Dynatrace, Datadog, etc.)
    and triggers autonomous incident diagnosis.

    Authentication: Requires X-Webhook-Secret header matching WEBHOOK_SECRET env var.
    """
    try:
        # Authentication check to prevent abuse and quota drain
        webhook_secret = os.getenv("WEBHOOK_SECRET")
        if webhook_secret:
            provided_secret = request.headers.get("X-Webhook-Secret")
            if not provided_secret or provided_secret != webhook_secret:
                logger.warning(f"Webhook authentication failed from {request.remote_addr}")
                return jsonify({
                    "status": "error",
                    "error": "Unauthorized: Invalid or missing X-Webhook-Secret header"
                }), 401

        data = request.get_json() or {}

        # Extract alert details (supports various monitoring tool formats)
        alert_name = data.get("alert_name") or data.get("title") or data.get("name") or "Unknown Alert"
        severity = data.get("severity") or data.get("priority") or "WARNING"
        description = data.get("description") or data.get("message") or data.get("details") or "No description provided"
        source = data.get("source") or data.get("origin") or "webhook"
        timestamp = data.get("timestamp") or data.get("time") or None

        logger.info(f"Webhook Alert Received: {alert_name} from {source}")

        # Log webhook to Cloud Logging
        log_to_cloud(
            event_type="webhook_alert_received",
            message=f"Alert webhook received: {alert_name}",
            severity=severity,
            alert_name=alert_name,
            source=source,
            description=description,
            timestamp=timestamp,
            raw_payload=data
        )

        # Trigger autonomous diagnosis
        logger.info("Triggering autonomous incident diagnosis...")
        get_captured_traces()

        system_prompt = (
            f"You are SentinelOps AI SRE Agent. An observability alert has been triggered:\n"
            f"Alert: {alert_name}\n"
            f"Severity: {severity}\n"
            f"Description: {description}\n\n"
            f"Search the knowledge base for relevant runbooks and provide a diagnosis."
        )

        response = ai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=f"Alert: {alert_name}. {description}. Diagnose this issue.",
            config=types.GenerateContentConfig(
                tools=[search_knowledge_base],
                safety_settings=safety_settings,
                system_instruction=system_prompt
            )
        )

        diagnosis = response.text
        traces = get_captured_traces()

        # Log diagnosis result
        log_to_cloud(
            event_type="webhook_diagnosis_completed",
            message=f"Completed diagnosis for alert: {alert_name}",
            severity="INFO",
            alert_name=alert_name,
            diagnosis_length=len(diagnosis)
        )

        return jsonify({
            "status": "processed",
            "alert_name": alert_name,
            "diagnosis": diagnosis,
            "traces": traces
        })

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        log_to_cloud(
            event_type="webhook_error",
            message=f"Webhook processing failed: {str(e)}",
            severity="ERROR",
            error=str(e)
        )
        return jsonify({
            "status": "error",
            "error": str(e)
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

        # Step 1: Backup to Google Cloud Storage first
        logger.info("Backing up runbook to Google Cloud Storage...")
        gcs_url = upload_to_gcs(title, content)

        # Step 2: Embed runbook text using text-embedding-004
        logger.info("Generating 768-dimension semantic vector via Google text-embedding-004...")
        emb_res = ai_client.models.embed_content(
            model="text-embedding-004",
            contents=content
        )
        vector = emb_res.embeddings[0].values

        # Step 3: Insert document chunk with GCS reference
        payload = {
            "title": title,
            "content": content,
            "embedding": vector,
            "gcs_backup_url": gcs_url
        }
        res = db.knowledge_vectors.insert_one(payload)
        logger.info(f"MongoDB Document indexed successfully! Collection: knowledge_vectors, Doc ID: {res.inserted_id}")
        logger.info(f"GCS Backup URL: {gcs_url}")

        # Log runbook ingestion to Cloud Logging
        log_to_cloud(
            event_type="runbook_ingestion",
            message=f"Runbook '{title}' ingested successfully",
            severity="INFO",
            runbook_title=title,
            doc_id=str(res.inserted_id),
            gcs_url=gcs_url,
            content_length=len(content),
            vector_dimensions=len(vector)
        )

        traces = get_captured_traces()
        return jsonify({
            "success": True,
            "doc_id": str(res.inserted_id),
            "gcs_url": gcs_url,
            "traces": traces
        })
    except Exception as e:
        logger.error(f"Failed to ingest manual: {e}")
        return jsonify({
            "error": str(e),
            "traces": get_captured_traces()
        }), 500

@app.route('/api/runbook/ingest-library', methods=['POST'])
def api_ingest_sre_library():
    """Batch ingestion endpoint for the SRE runbook library.

    Ingests 10 pre-defined SRE runbooks into the knowledge_vectors collection.
    This is useful for initializing the database with sample data.
    """
    try:
        logger.info("Starting batch ingestion of SRE runbook library...")
        get_captured_traces()  # Clear previous traces

        if db is None:
            raise ValueError("MongoDB cluster connection is offline. Ingestion unavailable.")

        # Define the SRE runbook library
        sre_library = [
            {
                "title": "MongoDB Connection Fault & Pooling Guide",
                "content": "SRE Incident Guide: When database timeouts or 'connection refused' errors occur on auth-service, SREs must inspect active pooling variables. To optimize throughput, increase connection pool size to 50 in config.json and implement a reconnect retry logic of 3 attempts with exponential backoff."
            },
            {
                "title": "Node.js Out of Memory (OOM) Heap Leak Guide",
                "content": "SRE Incident Guide: If memory usage on a Node.js API container climbs exponentially to 100%, a heap memory leak is occurring. Inspect the server garbage collection allocation, and modify ecosystem.config.js to include '--max-old-space-size=4096' to increase V8 memory limit to 4GB, then restart PM2."
            },
            {
                "title": "Nginx Reverse Proxy Rate Limiting & DDoS Prevention",
                "content": "SRE Incident Guide: When server load spikes due to sudden high request volumes or DDoS, configure Nginx limit_req zone to restrict incoming traffic. Edit nginx.conf to add 'limit_req_zone $binary_remote_addr zone=one:10m rate=10r/s;' and apply 'limit_req zone=one burst=5 nodelay;' to protect microservices."
            },
            {
                "title": "Kubernetes Disk Space Exhaustion & Log Rotation",
                "content": "SRE Incident Guide: When a Kubernetes node status changes to 'DiskPressure' and pod scheduling halts, clean docker system files. Execute 'docker system prune -af' and adjust the log-rotate configuration inside /etc/logrotate.d/docker to limit standard out logs to 10MB per file."
            },
            {
                "title": "Redis Cache Key Eviction & Connection Exhaustion",
                "content": "SRE Incident Guide: If redis cache hit rates drop below 70% and latency regressions spike, the memory limit is reached. Edit redis.conf to set 'maxmemory 2gb' and set the key eviction policy to 'maxmemory-policy allkeys-lru' to automatically evict least recently used keys."
            },
            {
                "title": "DNS Resolution Failure in Kubernetes Cluster",
                "content": "SRE Incident Guide: When pods fail to communicate with external APIs with 'Could not resolve host' errors, CoreDNS is failing. Check the CoreDNS pods using 'kubectl get pods -n kube-system -l k8s-app=kube-dns' and execute a roll restart of the coredns deployment to clear cached locks."
            },
            {
                "title": "SSL/TLS Certificate Expiry & Auto-Renewal Failure",
                "content": "SRE Incident Guide: When browsers display 'Your connection is not private' and HTTPS requests fail, the SSL certificate has expired. Run 'certbot renew' manually on the ingress gateway node and verify that a cron job is configured under crontab to execute certificate checks weekly."
            },
            {
                "title": "Database Replication Lag & Read/Write Splitting",
                "content": "SRE Incident Guide: If replication lag between primary and secondary database nodes exceeds 5 seconds, read queries will fetch stale data. Implement read/write splitting in your database client, routing all INSERT/UPDATE statements to the primary and SELECT queries to the read-replicas."
            },
            {
                "title": "Dynatrace Server Latency Spike — CPU 98.4% Recovery",
                "content": "SRE Incident Guide: If an observability alert is received indicating a latency spike of +1200ms and CPU is pegged at 98.4%, SREs must modify server.py (or hotfix.py) to set the request rate-limiting timeout to 5 seconds (5000ms) on connections, preventing the CPU from locks."
            },
            {
                "title": "GCP IAM Access Denied on Cloud Storage Buckets",
                "content": "SRE Incident Guide: If Cloud Run containers log 'AccessDenied' when writing files to GCS buckets, the Compute Engine Service Account is missing roles. Grant 'roles/storage.admin' to the service account '782741881130-compute@developer.gserviceaccount.com' at the project level."
            }
        ]

        ingested_count = 0
        ingested_ids = []

        for doc in sre_library:
            logger.info(f"Vectorizing: '{doc['title']}'...")

            try:
                # Generate embedding
                emb_res = ai_client.models.embed_content(
                    model="text-embedding-004",
                    contents=doc['content']
                )
                vector = emb_res.embeddings[0].values

                # Create payload
                payload = {
                    "title": doc['title'],
                    "content": doc['content'],
                    "embedding": vector
                }

                # Insert into MongoDB
                result = db.knowledge_vectors.insert_one(payload)
                ingested_count += 1
                ingested_ids.append(str(result.inserted_id))
                logger.info(f"Successfully indexed: {doc['title']}")

            except Exception as e:
                logger.error(f"Failed to ingest '{doc['title']}': {e}")

        logger.info(f"Batch ingestion complete! {ingested_count}/{len(sre_library)} runbooks successfully indexed.")

        # Log to Cloud Logging
        log_to_cloud(
            event_type="sre_library_ingestion",
            message=f"SRE library batch ingestion completed: {ingested_count} runbooks",
            count=ingested_count,
            total=len(sre_library)
        )

        traces = get_captured_traces()
        return jsonify({
            "success": True,
            "ingested_count": ingested_count,
            "total": len(sre_library),
            "document_ids": ingested_ids,
            "traces": traces
        })

    except Exception as e:
        logger.error(f"Batch ingestion failed: {e}")
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

        # Build tools list - include MCP tool if available
        tools_list = [search_knowledge_base, load_user_memory, save_chat_history]
        if mcp_client and mcp_client.initialized:
            tools_list.append(execute_mongodb_mcp_tool)
            logger.info(f"[MCP] MongoDB MCP tool registered with Gemini CLI mode")

        chat = ai_client.chats.create(
            model=GEMINI_MODEL,
            config=types.GenerateContentConfig(
                tools=tools_list,
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
        # Default mode: Start dynamic Flask server with container compatibility
        print("\n" + "="*80)
        print("              SentinelOps SRE Agent API Server is launching...              ")
        print("="*80)
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Starting Flask web server on port {port} (binding 0.0.0.0)...")
        app.run(host="0.0.0.0", port=port, debug=False)


