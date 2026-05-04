import json
import requests
import google.auth
import google.auth.transport.requests

# ==========================================================
# Gemini Enterprise Registration Configuration
# Update these parameters to match your enterprise console configurations.
# ==========================================================
PROJECT_NUMBER = "your-gcp-project-number"
LOCATION = "global"

# The Gemini Enterprise App / Engine hosting your assistant console
GE_APP_ID = "your-gemini-enterprise-app-id"
ASSISTANT_ID = "default_assistant"

# Reasoning Engine resource name output by deploy_agent_engine.py
REASONING_ENGINE_RESOURCE = (
    f"projects/{PROJECT_NUMBER}/locations/us-central1/reasoningEngines/your-reasoning-engine-id"
)

# The Google OAuth Configuration resource registered in your Discovery Engine console
GOOGLE_AUTH_AUTHORIZATION = (
    f"projects/{PROJECT_NUMBER}/locations/global/authorizations/google-auth-token"
)

# Display properties for the registered ADK Agent
AGENT_DISPLAY_NAME = "Multi-Datastore Stream Assist Agent"
AGENT_DESCRIPTION = "Searches and federates queries across multiple Google datastores."

# 1. Retrieve default credentials and refresh OAuth access token to call GCP APIs
print(">>> Refreshing Application Default Credentials...")
credentials, project = google.auth.default()
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)
access_token = credentials.token

# 2. Construct the Discovery Engine global assistant agent creation URL
api_url = (
    f"https://discoveryengine.googleapis.com/v1alpha/projects/{project}/locations/{LOCATION}/"
    f"collections/default_collection/engines/{GE_APP_ID}/assistants/{ASSISTANT_ID}/agents"
)

# 3. Construct the registration payload
# Links the reasoning engine deployment and configures the Google authorization credential scope
payload = {
    "displayName": AGENT_DISPLAY_NAME,
    "description": AGENT_DESCRIPTION,
    "adk_agent_definition": {
        "tool_settings": {
            "tool_description": "Federates queries across Google Drive and other search datastores."
        },
        "provisioned_reasoning_engine": {
            "reasoning_engine": REASONING_ENGINE_RESOURCE,
        },
    },
    "authorization_config": {
        "tool_authorizations": [
            GOOGLE_AUTH_AUTHORIZATION
        ]
    }
}

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "x-goog-user-project": project,
}

print("=" * 80)
print("REGISTERING AGENT IN GEMINI ENTERPRISE (AGENTSPACE)")
print("=" * 80)
print(f"Endpoint URL: {api_url}")
print("=" * 80)
print("Request Payload:")
print(json.dumps(payload, indent=2))
print("\nSubmitting registration request...")

# 4. Submit HTTP POST to register the agent
response = requests.post(api_url, headers=headers, data=json.dumps(payload))

print(f"\nResponse Status Code: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2))
except Exception:
    print(response.text)
print("=" * 80)
