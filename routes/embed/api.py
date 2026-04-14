from flask import Blueprint, request, jsonify, session
from bot.chat import get_response_from_gemini
from models.models import Bot
import logging 

api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    
    bot_id = data.get('bot_id') 
    if not bot_id and 'active_bot_id' in session:
        bot_id = session.get('active_bot_id')

    try:
        if bot_id:
            bot_record = Bot.query.get(bot_id)
            if bot_record:
                reply = get_response_from_gemini(
                    user_query=user_message, 
                    target_store_id=bot_record.store_id, 
                    custom_prompt=bot_record.system_prompt
                )
            else:
                return jsonify({"error": "Invalid Bot ID."})
                
        else:
            reply = get_response_from_gemini(
                user_query=user_message, 
                target_store_id=None, 
                custom_prompt=None
            )
            
        return jsonify({"response": reply})

    except Exception as e:
        logging.error(f"Gemini API Crash: {str(e)}")
        return jsonify({
            "error": "The AI is currently experiencing high demand. Please try again in a few seconds."
        })