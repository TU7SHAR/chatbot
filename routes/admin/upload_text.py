import os
import uuid
from werkzeug.utils import secure_filename
from flask import request, redirect, url_for, flash, current_app, session
from models.models import db, Bot, Document
from bot.cloud import upload_to_gemini 
from . import admin_bp

@admin_bp.route('/upload_text', methods=['POST'])
def upload_text():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    bot_id = session.get('active_bot_id')
    if not bot_id:
        flash("No active bot selected.", "error")
        return redirect(url_for('admin_bp.admin_dashboard'))

    target_bot = Bot.query.get(bot_id)
    title = request.form.get('title', 'Untitled_Text')
    content = request.form.get('content', '')

    if not content.strip():
        flash("Content cannot be empty.", "error")
        return redirect(url_for('admin_bp.admin_dashboard'))

    safe_title = secure_filename(title)
    if not safe_title:
        safe_title = "Direct_Text"
    
    filename = f"{safe_title}_{uuid.uuid4().hex[:6]}.md"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        new_doc = Document(bot_id=bot_id, filename=filename)
        db.session.add(new_doc)
        db.session.commit()

        upload_to_gemini(filepath, target_bot.store_id)
        
        flash(f"Successfully ingested raw text: '{title}'", "success")
    except Exception as e:
        flash(f"Error processing text: {str(e)}", "error")

    return redirect(url_for('admin_bp.admin_dashboard'))