import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv('API_KEY'))

def investigate():
    print("🔍 Deep Scanning Vector Stores (V3)...")
    try:
        stores = list(client.file_search_stores.list())
        
        for store in stores:
            print(f"\n📦 STORE: {store.display_name} | ID: {store.name}")
            
            # THE FIX: Correct way to list files in a store in the new SDK
            try:
                # We use the list_files method directly on the store's resource path
                files = list(client.file_search_stores.files.list(file_search_store_name=store.name))
                
                if not files:
                    print("   (Empty Store)")
                else:
                    for f in files:
                        # In the new SDK, 'f' contains 'file' (the file name) and 'state'
                        print(f"   📄 File ID: {f.name}")
                        print(f"      State: {f.state}")
            except Exception as e:
                print(f"   ⚠️ Could not list files for this store: {e}")

    except Exception as e:
        print(f"🚨 Connection Error: {e}")

if __name__ == "__main__":
    investigate()