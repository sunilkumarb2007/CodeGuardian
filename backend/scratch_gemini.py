import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)
model = "gemini-3.6-flash"

print(f"Testing {model}...")
try:
    response = client.models.generate_content(
        model=model,
        contents="Say 'hello world'",
    )
    print(f"SUCCESS: {model}")
except Exception as e:
    print(f"FAILED: {e}")
