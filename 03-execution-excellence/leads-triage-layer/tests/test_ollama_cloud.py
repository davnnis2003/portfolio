import ollama
import os
from utils.env_loader import init_env

init_env()

host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
api_key = os.getenv("OLLAMA_API_KEY")

print(f"Host: {host}")
print(f"API Key present: {api_key is not None}")

if api_key:
    # Test if Client accepts headers
    try:
        client = ollama.Client(host="https://ollama.com", headers={"Authorization": f"Bearer {api_key}"})
        print("Client initialized with headers successfully")
    except Exception as e:
        print(f"Error initializing client: {e}")
else:
    print("No API Key found in environment")
