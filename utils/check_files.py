import os
from dotenv import load_dotenv
from google import genai

# Load your API key from the .env file
load_dotenv()

def check_gemini_storage():
    try:
        client = genai.Client(api_key=os.getenv('API_KEY'))
        
        print("🔍 Scanning Gemini Cloud Storage...\n")
        
        # 1. Check all uploaded files
        print("--- ALL UPLOADED FILES ---")
        files = list(client.files.list())
        if not files:
            print("No files found in your Gemini storage.")
        else:
            for f in files:
                print(f"📄 Name: {f.display_name}")
                print(f"   ID: {f.name}")
                print(f"   State: {f.state.name}") # Will show ACTIVE, PROCESSING, or FAILED
                print(f"   Created: {f.create_time}\n")

        # 2. Check Vector Stores (File Search Stores)
        print("--- VECTOR STORES ---")
        stores = list(client.file_search_stores.list())
        if not stores:
            print("No vector stores found.")
        else:
            for store in stores:
                print(f"📦 Store Name: {store.display_name}")
                print(f"   ID: {store.name}\n")
                
    except Exception as e:
        print(f"❌ Error connecting to Gemini API: {e}")

if __name__ == "__main__":
    check_gemini_storage()