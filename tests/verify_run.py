import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.handlers.process_alerts import lambda_handler

# Set Mock Env Vars
os.environ["DB_HOST"] = "mock_host"
os.environ["WHATSAPP_API_TOKEN"] = "mock_token"
# We rely on the adapters handling connection failures gracefully for this test

def test_run():
    print(">>> Starting Verification Run")
    result = lambda_handler({}, None)
    print(f">>> Result: {result}")
    
    if result['status'] == 'success':
        print(">>> SUCCESS: Handler executed correctly (likely using mocks/fallbacks).")
    else:
        print(">>> FAILURE: Handler returned error.")

if __name__ == "__main__":
    test_run()
