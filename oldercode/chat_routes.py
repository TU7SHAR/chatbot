from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from bot.chat import get_response_from_gemini
from models.models import Bot, db, User, Organization

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/')
def index():
    # If they are already logged in, skip the marketing page and send them to the app
    if session.get('user_id'): 
        return redirect(url_for('chat_bp.dashboard'))
    
    # Renders the new premium landing page
    return render_template('index.html')

@chat_bp.route('/dashboard')
def dashboard():
    if not session.get('user_id'): return redirect(url_for('auth.login'))
        
    my_bots = Bot.query.filter_by(created_by=session['user_id']).all()
    all_org_bots = Bot.query.filter(Bot.org_id == session['org_id'], Bot.created_by != session['user_id']).all()
    org_bots = []
    for bot in all_org_bots:
        if bot.visibility == 'public':
            org_bots.append(bot)
        elif bot.visibility == 'private' and session.get('role') == 'admin':
            org_bots.append(bot)
    return render_template('dashboard.html', my_bots=my_bots, org_bots=org_bots)

@chat_bp.route('/set_active_bot/<int:bot_id>')
def set_active_bot(bot_id):
    if not session.get('user_id'): return redirect(url_for('auth.login'))
        
    target_bot = Bot.query.get(bot_id)
    if target_bot and target_bot.org_id == session.get('org_id'):
        is_creator = target_bot.created_by == session.get('user_id')
        is_unlocked = target_bot.id in session.get('unlocked_bots', [])
        
        if target_bot.visibility == 'public' or is_creator or is_unlocked:
            session['active_bot_id'] = target_bot.id
            session['active_bot_name'] = target_bot.bot_name
        else:
            flash("Security Error: This Bot is classified. Decryption key required.", "error")
            
    # Redirect to dashboard instead of index
    return redirect(url_for('chat_bp.dashboard'))

@chat_bp.route('/unlock_bot/<int:bot_id>', methods=['POST'])
def unlock_bot(bot_id):
    if session.get('role') != 'admin':
        flash("Clearance Error: Administrator privileges required.", "error")
        return redirect(url_for('chat_bp.dashboard')) # Redirect to dashboard
    
    submitted_key = request.form.get('access_key', '').upper()
    target_bot = Bot.query.get(bot_id)
    
    if target_bot and target_bot.access_key == submitted_key:
        unlocked = session.get('unlocked_bots', [])
        if bot_id not in unlocked:
            unlocked.append(bot_id)
        session['unlocked_bots'] = unlocked
        
        session['active_bot_id'] = target_bot.id
        session['active_bot_name'] = target_bot.bot_name
        flash(f"Decrypted: Access granted to {target_bot.bot_name}", "success")
    else:
        flash("Encryption Error: Invalid Access Key.", "error")
    
    # Redirect to dashboard instead of index
    return redirect(url_for('chat_bp.dashboard'))

@chat_bp.route('/chat', methods=['POST'])
def chat():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized access. Please log in."}), 401
        
    if 'active_bot_id' not in session:
        return jsonify({"error": "No terminal connected. Please select a bot from the dashboard."}), 400

    data = request.get_json()
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    try:
        active_bot = Bot.query.get(session['active_bot_id'])
        if not active_bot:
            return jsonify({"error": "Active bot not found in database."}), 404
        bot_response = get_response_from_gemini(user_message, active_bot.store_id)
        return jsonify({"response": bot_response})
        
    except Exception as e:
        print(f"Gemini Error: {e}")
        return jsonify({"error": "Failed to communicate with the knowledge base."}), 500
    
@chat_bp.route('/embed/<int:bot_id>')
def embed_bot(bot_id):
    target_bot = Bot.query.get_or_404(bot_id)
    
    session['active_bot_id'] = target_bot.id
    session['active_bot_name'] = target_bot.bot_name
    
    return render_template('embed_chat.html')