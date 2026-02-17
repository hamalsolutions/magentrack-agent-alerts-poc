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
