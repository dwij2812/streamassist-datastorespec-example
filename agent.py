import os
import json
import re
import requests
import google.auth
import google.auth.transport.requests
from google.auth.transport.requests import Request
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.apps import App
from google.adk.agents import LlmAgent
from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin

# ==========================================
# Enterprise configuration
# Replace these configurations with your actual Gemini Enterprise credentials and parameters.
# ==========================================
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
LOCATION = "global"
COLLECTION = "default_collection"

# The Gemini Enterprise App / Engine identifier hosting your search engine
ENGINE_ID = "your-gemini-enterprise-engine-id"
ASSISTANT_ID = "default_assistant"

# Google Auth config identifier used inside Gemini Enterprise (Agentspace Console)
GE_AUTH_ID = "google-auth-token"

# Your enterprise document stores
DRIVE_DATASTORE_ID = "your-google-drive-datastore-id"
DOCUMENTS_DATASTORE_ID = "your-documents-datastore-id"


def get_access_token(tool_context: ToolContext) -> str:
    """
    Retrieves a valid Google Cloud OAuth2 access token for REST API authentication.
    
    This helper seamlessly handles two environments:
    1. Production Environment: When running within Gemini Enterprise, the token is managed
       and provided automatically by Gemini Enterprise under the ToolContext state.
    2. Local Development: Falls back to Application Default Credentials (ADC) when running
       locally. For local execution, ensure you run:
       `gcloud auth application-default login`
       
    Args:
        tool_context: The ADK tool context object that carries state credentials.
        
    Returns:
        str: A valid OAuth2 access token string.
    """
    # Define a regex pattern to retrieve the GE authorization token stored in tool state
    pattern = re.compile(f"^{GE_AUTH_ID}.*")
    
    state_dict = tool_context.state.to_dict()
    matched_auth = {key: value for key, value in state_dict.items() if pattern.match(key)}
    
    if matched_auth:
        # Token exists inside Gemini Enterprise State
        token_key = list(matched_auth.keys())[0]
        access_token = tool_context.state[token_key]
        print(f"[OAuth] Using cached token from Gemini Enterprise state (Key: {token_key})")
        return access_token
    
    # Local fallback: Use Application Default Credentials (ADC)
    print("[OAuth] No cached token found in state. Falling back to Application Default Credentials (ADC)...")
    credentials, project = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )

    # Automatically refresh credentials if expired
    if not credentials.valid:
        credentials.refresh(Request())
    
    print("[OAuth] Successfully acquired access token via Application Default Credentials.")
    return credentials.token


def invoke_agent_streamassist(query: str, tool_context: ToolContext) -> str:
    """
    Invokes the Gemini Enterprise agent using the v1alpha streamAssist REST API.
    
    This function dynamically passes custom dataStoreSpecs inside the toolsSpec block,
    allowing queries to be federated across multiple datastores (e.g., Google Drive and standard files).
    
    Args:
        query: The natural language question or prompt for the assistant.
        tool_context: The ADK tool context containing state and credential information.
        
    Returns:
        str: The raw JSON response content or error message.
    """
    # Format resource name: projects/{project}/locations/{location}/collections/{collection}/engines/{engine}/assistants/{assistant}
    assistant_name = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/"
        f"engines/{ENGINE_ID}/assistants/{ASSISTANT_ID}"
    )

    # Construct the v1alpha streamAssist endpoint URL
    url = f"https://{LOCATION}-discoveryengine.googleapis.com/v1alpha/{assistant_name}:streamAssist"

    print("=" * 80)
    print("GEMINI ENTERPRISE - AGENT STREAM ASSIST INVOCATION")
    print("=" * 80)
    print(f"URL:   {url}")
    print(f"Query: {query}")
    print("=" * 80)

    # 1. Acquire the OAuth2 access token
    token = get_access_token(tool_context)

    # 2. Configure request headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 3. Construct the streamAssist request body with custom datastore specifications
    # The dataStore specs follow the standard GCP resource layout:
    # 'projects/{project}/locations/{location}/collections/{collection}/dataStores/{datastore_id}'
    body = {
        "query": {
            "text": query
        },
        "answerGenerationMode": "ANSWER_GENERATION_MODE_UNSPECIFIED",
        "toolsSpec": {
            "vertexAiSearchSpec": {
                "dataStoreSpecs": [
                    {
                        "dataStore": f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/dataStores/{DRIVE_DATASTORE_ID}"
                    },
                    {
                        "dataStore": f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/{COLLECTION}/dataStores/{DOCUMENTS_DATASTORE_ID}"
                    }
                ]
            }
        }
    }

    print("\nRequest Payload:")
    print(json.dumps(body, indent=2))
    print("\nSending HTTP POST request...")

    # 4. Execute the streaming HTTP POST request
    try:
        response = requests.post(url, json=body, headers=headers, stream=True)
        print(f"Response Status Code: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"API Request failed with status {response.status_code}: {response.text}"
            print(f"[Error] {error_msg}")
            return f"Error: {error_msg}"

        # 5. Read and log the raw response contents
        response_text = response.text
        print("\n--- Raw Response Stream Output ---")
        print(response_text)
        print("----------------------------------\n")

        return response_text

    except Exception as e:
        print(f"[Error] Network request failed: {str(e)}")
        return f"Error during streamAssist API invocation: {str(e)}"


# Initialize the ADK FunctionTool around our stream_assist runner
stream_assist_tool = FunctionTool(
    func=invoke_agent_streamassist,
    description="Invokes Gemini Enterprise streamAssist API to query multiple datastores."
)

# Configure the primary orchestrating LLM Agent
root_agent = LlmAgent(
    name="StreamAssistOrchestratorAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a helpful assistant that searches multiple enterprise datastores. "
        "When the user asks a question, invoke the 'stream_assist_tool' to search the database."
    ),
    tools=[stream_assist_tool],
)

# Construct the ADK Application Container
app = App(
    name="streamassist-datastorespec-example",
    root_agent=root_agent,
    plugins=[SaveFilesAsArtifactsPlugin()],
)
