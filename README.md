# Magentrack Agent Alerts POC

An agentic chatbot system designed to process patient health alerts from an RDS database, generate empathetic responses using AWS Bedrock (Claude 3), and communicate via WhatsApp Business API.

## Architecture

1.  **Trigger**: `EventBridge Scheduler` triggers the Lambda function every minute (Polling).
2.  **Input**: Lambda queries `RDS` Postgres for status='PENDING' alerts.
3.  **Context**: Lambda fetches a "Guidance Document" from `S3`.
4.  **Intelligence**: Lambda sends Alert + Guidance to `AWS Bedrock` (Claude 3 Sonnet) to generate a response.
5.  **Output**: Response is sent to the patient via `WhatsApp Business API`.
6.  **State**: Alert status is updated to 'PROCESSED' in `RDS`.

## Project Structure

- `src/handlers/process_alerts.py`: Main Lambda entry point.
- `src/core/llm_agent.py`: Logic for interacting with AWS Bedrock.
- `src/connectivity/`: Adapters for Database, WhatsApp, and S3.
- `infra/template.yaml`: AWS SAM template for infrastructure.

## Local Development

### Prerequisites

- Python 3.11+
- AWS Credentials (if running with real services)
- `pip install -r requirements.txt`

### Configuration

Set environment variables in `.env` or export them:

```bash
export DB_HOST=localhost
export DB_NAME=test_db
export WHATSAPP_API_TOKEN=xyz
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### Running Locally

To test the flow with mock data (if DB is unreachable):

```bash
python3 src/handlers/process_alerts.py
```

## Deployment

Using AWS SAM:

```bash
sam build
sam deploy --guided
```

## Local Testing

You can use AWS SAM CLI to invoke functions locally using the provided event files in the `events/` folder.

### 1. Input Handler (API Gateway)

Simulate an API Gateway POST request:

```bash
sam local invoke InputFunction -e events/input_event.json
```

### 2. Stream Trigger (DynamoDB Stream)

Simulate a DynamoDB Stream event (new item insertion):

```bash
sam local invoke StreamTriggerFunction -e events/stream_event.json
```

### 3. Process Message (Step Function Step 1)

Test the first step of the State Machine:

```bash
sam local invoke ProcessMessageFunction -e events/process_event.json
```

### 4. Generate Response (Step Function Step 2)

Test the response generation (requires AWS credentials for Bedrock/S3):

```bash
sam local invoke GenerateResponseFunction -e events/generate_event.json
```

**Note**: For `GenerateResponseFunction`, ensure you have valid AWS credentials configured in your environment or passed to the container, as it interacts with real AWS services (Bedrock, S3).

# API Integration Walkthrough

This guide explains how to make authenticated requests to your production API Gateway endpoint.

## Prerequisites

To make a request, you need two pieces of information:

1.  **API Endpoint URL**: The URL of your deployed API.
    - Current: `https://zpfhwm1xji.execute-api.us-east-1.amazonaws.com/Prod/webhook`
2.  **API Key**: The secret key required to access the endpoint.
    - Current ID: `o55rk988tk`
    - Value: _(Retrieve this securely via AWS Console or CLI)_

## Authentication Mechanism

The API uses **API Key** authentication. You must include the API Key in the HTTP **Header** of your request.

- **Header Name:** `x-api-key`
- **Header Value:** `YOUR_API_KEY_VALUE`

## Request Examples

### 1. cURL (Command Line)

```bash
curl -X POST https://zpfhwm1xji.execute-api.us-east-1.amazonaws.com/Prod/webhook \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY_VALUE" \
  -d '{"message": "Hello from production", "phone_number": "+1234567890"}'
```

### 2. Python (using `requests`)

```python
import requests
import json

url = "https://zpfhwm1xji.execute-api.us-east-1.amazonaws.com/Prod/webhook"
api_key = "YOUR_API_KEY_VALUE"

headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key
}

payload = {
    "message": "Hello from Python",
    "phone_number": "+1234567890"
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Error:", response.status_code, response.text)
```

### 3. JavaScript / Node.js (using `fetch`)

```javascript
const url =
  "https://zpfhwm1xji.execute-api.us-east-1.amazonaws.com/Prod/webhook";
const apiKey = "YOUR_API_KEY_VALUE";

const payload = {
  message: "Hello from Node.js",
  phone_number: "+1234567890",
};

fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "x-api-key": apiKey,
  },
  body: JSON.stringify(payload),
})
  .then((response) => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then((data) => console.log("Success:", data))
  .catch((error) => console.error("Error:", error));
```

## Error Codes

- **403 Forbidden**: Invalid API Key, missing API Key, or the header is incorrect.
- **400 Bad Request**: Missing required fields in the request body (e.g., `message` or `phone_number`).
- **500 Internal Server Error**: Something went wrong on the server side.
