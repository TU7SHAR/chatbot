from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv('API_KEY'))

print("--- Current File Search Stores ---")
for store in client.file_search_stores.list():
    print(f"ID: {store.name} | Created: {store.create_time}")
    
print("\n--- Files currently in the Cloud ---")
for file in client.files.list():
    print(f"File: {file.display_name} | URI: {file.uri}")