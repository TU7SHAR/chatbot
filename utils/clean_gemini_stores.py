import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def nuke_gemini_storage():
    client = genai.Client(api_key=os.getenv('API_KEY'))
    print("🗑️ Initializing Deep Gemini Cleanup...")

    # 1. Get all stores
    try:
        stores = list(client.file_search_stores.list())
        if not stores:
            print("No stores found.")
        else:
            for store in stores:
                print(f"\nProcessing Store: {store.display_name} ({store.name})")
                
                # 2. List and delete all files INSIDE this specific store
                # This is the step that was missing
                try:
                    files = list(client.file_search_stores.files.list(file_search_store_name=store.name))
                    if files:
                        print(f"  Found {len(files)} files. Deleting files first...")
                        for f in files:
                            # Note: We delete the association in the store
                            client.file_search_stores.files.delete(
                                file_search_store_name=store.name, 
                                name=f.name
                            )
                            print(f"    Deleted file: {f.name}")
                    else:
                        print("  Store is already empty of files.")
                except Exception as e:
                    print(f"  Error clearing files in store: {e}")

                # 3. Now delete the store itself
                try:
                    client.file_search_stores.delete(name=store.name)
                    print(f"✅ Successfully deleted store: {store.display_name}")
                except Exception as e:
                    print(f"❌ Failed to delete store {store.display_name}: {e}")

        # 4. Clean up any orphaned files in the general cloud storage
        print("\nChecking for orphaned files in general storage...")
        for lone_file in client.files.list():
            print(f"Deleting orphaned file: {lone_file.display_name}")
            client.files.delete(name=lone_file.name)

        print("\n✨ Gemini Cloud is now 100% Empty.")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    nuke_gemini_storage()