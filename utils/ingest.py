import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv('API_KEY'))

def run_knowledge_ingestion():
    """
    Creates a new File Search Store and uploads project documentation 
    to the vector database for RAG-based retrieval.
    """
    try:
        store_config = {'display_name': 'Drish_Internal_Knowledge_Base'}
        vector_store = client.file_search_stores.create(config=store_config)
        
        store_id = vector_store.name
        print(f"Vector Store Initialized: {store_id}")

        knowledge_base_files = [os.path.join('bot', 'instructions.txt')]

        for document in knowledge_base_files:
            print(f"Uploading and indexing: {document}")
            
            upload_op = client.file_search_stores.upload_to_file_search_store(
                file=document,
                file_search_store_name=store_id
            )

            while not upload_op.done:
                print(f"Indexing in progress for {document}...")
                time.sleep(10)  # Standard polling interval
                upload_op = client.operations.get(upload_op)

            print(f"Indexing complete: {document}")

        print(f"ACTIVE STORE_ID: {store_id}")
        print("Update the .env file with this ID for deployment.")

    except Exception as error:
        print(f"Critical error during ingestion: {error}")

if __name__ == "__main__":
    run_knowledge_ingestion()