# Gemini Enterprise Multi-Datastore Search with Stream Assist API

This sample project demonstrates how to build a production-grade, multi-source agent using the **Google Agent Development Kit (ADK)** and the **Gemini Enterprise v1alpha streamAssist REST API**.

By using custom `dataStoreSpecs` in the stream request, this agent can query and search across multiple enterprise Google Datastores (such as Google Drive and generic document datastores) dynamically, federating results back to the user.

---

## Getting Started

### 1. Prerequisites

- Python 3.10+
- Google Cloud SDK (`gcloud` CLI) installed and authenticated.

### 2. Installation

Install core dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configuration Setup

Open agent.py and update the following placeholder variables with your actual project resources:

```python
PROJECT_ID = "your-gcp-project-id"
ENGINE_ID = "your-gemini-enterprise-engine-id"
DRIVE_DATASTORE_ID = "your-google-drive-datastore-id"
DOCUMENTS_DATASTORE_ID = "your-documents-datastore-id"
```

---

## Running and Testing Locally

To run or test your agent logic locally:

1. **Authenticate with Google Cloud**:
   Run this command to acquire local application default credentials:

   ```bash
   gcloud auth application-default login
   ```

2. **Run the local agent server**:
   Execute ADK local hosting:
   ```bash
   python -m google.adk.tools.web agent:app
   ```

---

## Production Cloud Deployment

### Step 1: Deploy Reasoning Engine to Vertex AI

Run the deployment script to package your agent, resolve dependencies, and deploy the container to Vertex AI Agent Engines:

```bash
# Update variables in deploy_agent_engine.py first, then run:
python deploy_agent_engine.py
```

### Step 2: Register Agent with Gemini Enterprise

Register the newly deployed Reasoning Engine within your Gemini Enterprise (Agentspace) console using the registration script:

```bash
# Update reasoning engine ID and project numbers in publish_to_ge.py, then run:
python publish_to_ge.py
```