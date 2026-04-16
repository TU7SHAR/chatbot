import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv('API_KEY'))


# for gemini only 
BASE_GUARDRAILS = (
    "STRICT OPERATING CONSTRAINTS:\n"
    "1. IDENTITY & GREETINGS: You may warmly greet the user, introduce yourself, and state your purpose based entirely on your SPECIFIC BOT INSTRUCTIONS. Do NOT rely on the Knowledge Base just to introduce yourself.\n"
    "2. FACTUAL QUERIES: For all specific questions, your ONLY source of truth is the provided Knowledge Base / File Search. NEVER hallucinate facts.\n"
    "3. VAGUE PROMPTS & KEYWORDS: If the user just types a keyword or company name (e.g., 'Bubblooo'), use the Knowledge Base to provide a helpful, broad summary of that topic.\n"
    "4. OUT OF SCOPE: If the user asks a factual question that is completely missing from the retrieved files, ONLY THEN reply EXACTLY: 'I apologize, but I don't have information on that.'\n\n"
)

# it is like how the bot can respond who are not logged in and using the public bot, so we need to set some guardrails for the public bot to not answer specific company data ques.
PUBLIC_BOT_INSTRUCTIONS = (
    "PUBLIC PLATFORM ROLE: You are the official public AI Assistant for Bubbl.ooo. "
    "Your primary job is to explain our website's services to visitors, which allows companies to upload PDFs or scrape URLs to create custom-trained AI chatbots. "
    "CONVERSATIONAL RULES:\n"
    "1. DO NOT repeat your full introduction or purpose in every message. Only introduce yourself if the user explicitly asks who you are or greets you for the very first time.\n"
    "2. Keep answers brief, natural, and directly address the user's specific question without adding unnecessary fluff.\n"
    "3. Do NOT attempt to answer specific company data questions. If they ask about specific data, tell them to 'Please Log In to access your organization's custom bot.'\n"
    "4. If they ask about pricing, respond with 'Our pricing is based on the number of documents you upload and the number of chatbot interactions. Please visit our pricing page.'\n"
    "5. If they ask about how to upload documents or train data, respond with 'Once you create an account and log in, you can easily upload your documents or scrape URLs directly through the dashboard.'\n"
    "6. If they ask an out of context question, respond with 'I'm here to help with questions about our platform and services. For other inquiries, please contact our support team.'"
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