import os
from dotenv import load_dotenv
from google import genai
load_dotenv()

def get_gemini_client():
    return genai.Client(api_key=os.getenv('API_KEY'))

def create_dynamic_store(bot_name):
    """Creates a new vector store on Google Cloud and returns its ID."""
    try:
        client = get_gemini_client()
        store_config = {'display_name': bot_name}
        
        vector_store = client.file_search_stores.create(config=store_config)
        store_id = vector_store.name 
        
        print(f"Successfully created new Vector Store: {store_id}")
        return store_id
        
    except Exception as error: 
        print(f"Error creating dynamic store: {error}") 
        return None

def upload_to_gemini(file_path, target_store_id):
    """for uploading file on genai store"""
    try:
        client = get_gemini_client()
        client.file_search_stores.upload_to_file_search_store(
            file=file_path,
            file_search_store_name=target_store_id
        )
        print(f"File Uploaded on Gemini Store: {file_path}")

    except Exception as e: 
        print(f"Error Uploading Gemini: {e}")

def delete_from_gemini(l_filename):
    """finds file from genaistore and deletes it"""
    try:
        client = get_gemini_client()
        print(f"Searching for filename: {l_filename}")
        for g_file in client.files.list():
            if g_file.display_name == l_filename:
                client.files.delete(name=g_file.name)
                print(f"File Deleted: {l_filename}")
    except Exception as e: 
          print(f"Error deleting from Gemini: {e}")