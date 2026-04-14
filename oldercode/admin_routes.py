import os
from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app, session
from werkzeug.utils import secure_filename
from bot.cloud import delete_from_gemini, upload_to_gemini, create_dynamic_store
from models.models import db, Bot, Document

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

def allowed_file(filename):
    allowed = {'txt', 'doc', 'docx', 'xls', 'xlsx', 'md', 'html', 'pdf'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

@admin_bp.route('/')
def admin_dashboard():
    if 'user_id' not in session:
        flash("Please log in to access the admin panel.", "error")
        return redirect(url_for('auth.login'))
        
    # --- UPDATED: Fetch all bots for the Organization ---
    all_user_bots = Bot.query.filter_by(org_id=session['org_id']).all()
    
    active_bot = None
    if 'active_bot_id' in session:
        active_bot = Bot.query.filter_by(id=session['active_bot_id']).first()
        
    if not active_bot and all_user_bots:
        active_bot = all_user_bots[0]
        session['active_bot_id'] = active_bot.id        
        
    files = []
    if active_bot:
        bot_docs = Document.query.filter_by(bot_id=active_bot.id).all()
        files = [doc.filename for doc in bot_docs]
        
    return render_template('admin.html', files=files, bots=all_user_bots, active_bot=active_bot)

@admin_bp.route('/create_bot', methods=['POST'])
def create_bot():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # --- UPDATED: Count bots in the Org ---
    bot_count = Bot.query.filter_by(org_id=session['org_id']).count()
    new_bot_name = f"Bot {bot_count + 1}"
    
    # --- UPDATED: Dynamic store ID using org_id ---
    new_store_id = create_dynamic_store(f"bot-org{session['org_id']}-{bot_count + 1}")
    
    if new_store_id:
        # --- UPDATED: Save org_id and created_by ---
        new_bot = Bot(
            org_id=session['org_id'], 
            created_by=session['user_id'], 
            bot_name=new_bot_name, 
            store_id=new_store_id
        )
        db.session.add(new_bot)
        db.session.commit()
        
        session['active_bot_id'] = new_bot.id
        session['active_bot_name'] = new_bot_name 
        
        flash(f"Success: '{new_bot_name}' initialized and set to active!", "success")
    else:
        flash("Error: Failed to connect to Google Cloud.", "error")
            
    return redirect(url_for('admin_bp.admin_dashboard'))

@admin_bp.route('/select_bot/<int:bot_id>')
def select_bot(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # --- UPDATED: Secure by org_id ---
    target_bot = Bot.query.filter_by(id=bot_id, org_id=session['org_id']).first()
    
    if target_bot:
        session['active_bot_id'] = target_bot.id
        session['active_bot_name'] = target_bot.bot_name 
        flash(f"Context Switched: Now managing '{target_bot.bot_name}'", "success")
    else:
        flash("Security Error: Bot not found.", "error")
        
    return redirect(url_for('admin_bp.admin_dashboard'))

@admin_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if 'file' not in request.files:
        flash('File not in requested Files')
        return redirect(url_for('admin_bp.admin_dashboard'))
    
    file = request.files['file']
    if file.filename == '':
        flash('file name is blank')
        return redirect(url_for('admin_bp.admin_dashboard'))
    
    if file and allowed_file(file.filename):
        file.seek(0, os.SEEK_END) 
        file_size = file.tell()    
        file.seek(0, os.SEEK_SET)  
        
        if file_size > 1000*1024*1024: 
            flash('Upload failed: File exceeds maximum limit.')
            return redirect(url_for('admin_bp.admin_dashboard'))
        
        active_bot_id = session.get('active_bot_id')
        if not active_bot_id:
            flash("Error: No active workspace selected.", "error")
            return redirect(url_for('admin_bp.admin_dashboard'))
            
        # --- UPDATED: Secure by org_id ---
        user_bot = Bot.query.filter_by(id=active_bot_id, org_id=session['org_id']).first()
        
        if not user_bot:
            flash("Error: Active bot not found in database.", "error")
            return redirect(url_for('admin_bp.admin_dashboard'))

        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        existing_doc = Document.query.filter_by(bot_id=user_bot.id, filename=filename).first()
        
        if existing_doc:
            delete_from_gemini(filename)
        else:
            new_doc = Document(bot_id=user_bot.id, filename=filename)
            db.session.add(new_doc)
            db.session.commit()

        upload_to_gemini(file_path, user_bot.store_id)
        flash(f"Uploaded File: {filename} to {user_bot.bot_name}")
        
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Server Storage Freed: Deleted {filename} from local uploads folder.")

    else:
        flash('Invalid File Path')

    return redirect(url_for('admin_bp.admin_dashboard'))


@admin_bp.route('/delete/<filename>')
def delete_file(filename):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    secure_name = secure_filename(filename)
    
    active_bot_id = session.get('active_bot_id')
    # --- UPDATED: Secure by org_id ---
    user_bot = Bot.query.filter_by(id=active_bot_id, org_id=session['org_id']).first()
    
    if user_bot:
        doc_to_delete = Document.query.filter_by(bot_id=user_bot.id, filename=secure_name).first()
        
        if doc_to_delete:
            db.session.delete(doc_to_delete)
            db.session.commit()
            
            delete_from_gemini(secure_name)
                
            flash(f"File Deleted: {secure_name} from {user_bot.bot_name}")
        else:
            flash("Security Error: File does not exist in this specific workspace.")
    else:
        flash("No active bot found.")

    return redirect(url_for('admin_bp.admin_dashboard'))

@admin_bp.route('/rename_bot/<int:bot_id>', methods=['POST'])
def rename_bot(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    new_name = request.form.get('new_bot_name')
    if not new_name or new_name.strip() == '':
        flash("Error: Workspace name cannot be empty.", "error")
        return redirect(url_for('admin_bp.admin_dashboard'))

    # --- UPDATED: Secure by org_id ---
    target_bot = Bot.query.filter_by(id=bot_id, org_id=session['org_id']).first()
    if target_bot:
        target_bot.bot_name = new_name.strip()
        db.session.commit()
        flash(f"Workspace renamed to '{target_bot.bot_name}'", "success")
    else:
        flash("Security Error: Bot not found.", "error")

    return redirect(url_for('admin_bp.admin_dashboard'))


@admin_bp.route('/delete_bot/<int:bot_id>', methods=['POST'])
def delete_bot(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # --- UPDATED: Secure by org_id ---
    target_bot = Bot.query.filter_by(id=bot_id, org_id=session['org_id']).first()
    if target_bot:
        docs = Document.query.filter_by(bot_id=target_bot.id).all()
        for doc in docs:
            delete_from_gemini(doc.filename)

        db.session.delete(target_bot)
        db.session.commit()

        if session.get('active_bot_id') == bot_id:
            session.pop('active_bot_id', None)

        flash(f"Workspace '{target_bot.bot_name}' permanently deleted.", "success")
    else:
        flash("Security Error: Bot not found.", "error")

    return redirect(url_for('admin_bp.admin_dashboard'))