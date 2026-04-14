import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv('API_KEY'))

print("📡 Scanning Google Cloud for uploaded files...\n")

try:
    cloud_files = list(client.files.list())
    
    if not cloud_files:
        print("Google Cloud is completely empty.")
    else:
        for f in cloud_files:
            print(f"Found File: {f.display_name}")
            
            if "Wikipedia" in f.display_name:
                print(f"    ASSASSINATING GHOST FILE: {f.display_name}...")
                client.files.delete(name=f.name)
                print("    Target eliminated.")
                
    print("\n🧹 Scan complete!")

except Exception as e:
    print(f"❌ Error connecting to Gemini: {e}")