import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv('API_KEY'))

BASE_GUARDRAILS = (
    "STRICT OPERATING CONSTRAINTS:\n"
    "1. You are a strictly closed-knowledge AI assistant.\n"
    "2. Your ONLY source of truth is the provided Knowledge Base / File Search.\n"
    "3. NEVER use your internal training data to answer questions. NEVER hallucinate facts.\n"
    "4. If the answer is NOT explicitly in your provided files, reply EXACTLY: 'I apologize, but I don't have information on that topic in my records.'\n\n"
)

PUBLIC_BOT_INSTRUCTIONS = (
    "PUBLIC PLATFORM ROLE: You are the official public AI Assistant for our platform. "
    "Your ONLY job is to explain our website's services to visitors. "
    "Explain that we provide a platform where companies can upload PDFs or scrape URLs to create custom-trained AI chatbots. "
    "Keep answers brief and friendly. Do NOT attempt to answer specific company data questions. "
    "If they ask about specific data, tell them to 'Please Log In to access your organization's custom bot.' "
    "If they ask about pricing, respond with 'Our pricing is based on the number of documents you upload and the number of chatbot interactions. Please visit our pricing page.' "
    "If they ask about how to upload documents, respond with 'Once you create an account and log in, you can easily upload your documents through the dashboard.' "
    "If they ask some out of context question, respond with 'I'm here to help with questions about our platform and services. For other inquiries, please contact our support team.'"
)

def get_response_from_gemini(user_query, target_store_id=None, custom_prompt=None):
    try:
        if custom_prompt:
            system_instruction = BASE_GUARDRAILS + "SPECIFIC BOT INSTRUCTIONS:\n" + custom_prompt
        else:
            system_instruction = BASE_GUARDRAILS + PUBLIC_BOT_INSTRUCTIONS
            
        tools = []
        
        if target_store_id:
            tools.append(types.Tool(
                file_search=types.FileSearch(
                    file_search_store_names=[target_store_id] 
                )
            ))

        config_args = {"system_instruction": system_instruction}
        if tools:
            config_args["tools"] = tools

        config = types.GenerateContentConfig(**config_args)

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=user_query,
            config=config
        )
        
        return response.text
        
    except Exception as e:
        print(f"Gemini API Error: {e}") 
        return f"SYSTEM ALERT: The AI server is currently overloaded or unavailable. ({str(e)}). Please try again in 60 seconds."