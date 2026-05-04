import os
import vertexai
from vertexai import agent_engines
from agent import root_agent

# ==========================================================
# Cloud Deployment Configuration
# Set your actual Google Cloud project, bucket name, and region.
# ==========================================================
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "your-gcp-project-id")
LOCATION = "us-central1"  # Region for Vertex AI Agent Engine hosting
STAGING_BUCKET = "gs://your-gcs-staging-bucket-name"
DISPLAY_NAME = "streamassist-datastorespec-agent"

# 1. Initialize Vertex AI Client
print(f">>> Initializing Vertex AI Client (Project: {PROJECT_ID}, Region: {LOCATION})...")
client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION,
)

# 2. Package the local ADK agent into an Agent Engine Application container
local_app = agent_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

# 3. Scan active reasoning engines to check if the agent is already deployed
print(">>> Scanning active Reasoning/Agent Engines...")
existing_engines = client.agent_engines.list()
existing_engine = None

for engine in existing_engines:
    if engine.api_resource.display_name == DISPLAY_NAME:
        existing_engine = engine
        break

# Packaging configuration for the deployment
deploy_config = {
    "display_name": DISPLAY_NAME,
    "staging_bucket": STAGING_BUCKET,
    "requirements": "requirements.txt",
    "extra_packages": ["agent.py"],
}

# 4. Deploy a new Reasoning Engine or update the existing instance
if existing_engine:
    print(f">>> Located active deployment: {existing_engine.api_resource.name}. Initiating update...")
    remote_app = client.agent_engines.update(
        name=existing_engine.api_resource.name,
        agent=local_app,
        config=deploy_config
    )
    print(">>> Agent Engine successfully updated.")
else:
    print(">>> Initiating a new Agent Engine deployment...")
    remote_app = client.agent_engines.create(
        agent=local_app,
        config=deploy_config
    )
    print(">>> Agent Engine successfully created.")

print("=" * 80)
print(f"Deployment Complete!")
print(f"Reasoning Engine Resource Name: {remote_app.api_resource.name}")
print("=" * 80)
