import os
import uuid
from flask import request, redirect, url_for, flash, session, render_template, jsonify, current_app
from models.models import db, Bot, Document, BotUI, ScrapeJob
from bot.cloud import upload_to_gemini, delete_from_gemini, create_dynamic_store
from routes.auth.decorators import admin_required
from werkzeug.utils import secure_filename 
from . import admin_bp
import threading 
from .scrape_managment import async_scrape_task

@admin_bp.route('/create_pipeline', methods=['GET', 'POST'])
def create_pipeline():
    if request.method == 'GET':
        return render_template('create_pipeline.html')

    bot_name = request.form.get('bot_name')
    bot_type = request.form.get('bot_type')
    visibility = request.form.get('visibility')
    system_prompt = request.form.get('system_prompt')
    
    # Catch glassmorphism settings
    glass_opacity = request.form.get('glass_opacity', 35, type=int)
    glass_blur = request.form.get('glass_blur', 25, type=int)
    
    theme_color = request.form.get('theme_color', '#E8722A')
    header_color = request.form.get('header_color', '#FFFFFF')
    theme_mode = request.form.get('theme_mode', 'light')
    
    store_id = create_dynamic_store(bot_name)
    if not store_id:
        store_id = str(uuid.uuid4())

    access_key = None
    if visibility == 'private':
        access_key = uuid.uuid4().hex[:4].upper()

    new_bot = Bot(
        bot_name=bot_name,
        bot_type=bot_type,
        visibility=visibility,
        system_prompt=system_prompt,
        created_by=session.get('user_id'),
        org_id=session.get('org_id'), 
        store_id=store_id,
        access_key=access_key
    )
    db.session.add(new_bot)
    db.session.flush()

    avatar_file = request.files.get('bot_avatar')
    avatar_path = None
    
    if avatar_file and avatar_file.filename != '':
        avatar_dir = os.path.join(current_app.root_path, 'static', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        safe_avatar_name = f"avatar_{new_bot.id}_{secure_filename(avatar_file.filename)}"
        save_path = os.path.join(avatar_dir, safe_avatar_name)
        avatar_file.save(save_path)
        avatar_path = f'/static/avatars/{safe_avatar_name}'

    new_ui = BotUI(
        bot_id=new_bot.id,
        theme_color=theme_color,
        header_color=header_color,
        theme_mode=theme_mode,
        avatar_path=avatar_path,
        glass_opacity=glass_opacity, 
        glass_blur=glass_blur
    )
    db.session.add(new_ui)

    # 1. PROCESS UPLOADED FILES
    uploaded_files = request.files.getlist('file')
    for uploaded_file in uploaded_files:
        if uploaded_file and uploaded_file.filename != '':
            safe_name = secure_filename(uploaded_file.filename)
            filename = f"{uuid.uuid4().hex}_{safe_name}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            uploaded_file.save(filepath)

            new_doc = Document(bot_id=new_bot.id, filename=filename)
            db.session.add(new_doc)
            
            try:
                upload_to_gemini(filepath, new_bot.store_id)
            except Exception as e:
                print(f"Gemini Upload Error for {filename}: {e}")

    # 2. PROCESS RAW TEXT
    raw_text = request.form.get('raw_text')
    if raw_text and raw_text.strip():
        txt_filename = f"manual_knowledge_{uuid.uuid4().hex[:6]}.txt"
        txt_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], txt_filename)
        
        with open(txt_filepath, 'w', encoding='utf-8') as f:
            f.write(raw_text)

        new_doc = Document(bot_id=new_bot.id, filename=txt_filename)
        db.session.add(new_doc)
        
        try:
            upload_to_gemini(txt_filepath, new_bot.store_id)
        except Exception as e:
            print(f"Gemini Text Upload Error: {e}")

    # 3. PROCESS Q&A TEXT
    qa_text = request.form.get('qa_text')
    if qa_text and qa_text.strip():
        qa_filename = f"qa_knowledge_{uuid.uuid4().hex[:6]}.txt"
        qa_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], qa_filename)
        
        with open(qa_filepath, 'w', encoding='utf-8') as f:
            f.write("Q&A Knowledge Base:\n\n" + qa_text)

        new_doc_qa = Document(bot_id=new_bot.id, filename=qa_filename)
        db.session.add(new_doc_qa)
        
        try:
            upload_to_gemini(qa_filepath, new_bot.store_id)
        except Exception as e:
            print(f"Gemini Q&A Upload Error: {e}")

    # 4. PROCESS WEBSITE CRAWLER
    scrape_url = request.form.get('scrape_url')
    if scrape_url and scrape_url.strip():
        url_to_scrape = scrape_url.strip()
        use_spider = request.form.get('use_deep_crawl') == 'on' 
        max_urls = int(request.form.get('max_urls', 20))

        new_job = ScrapeJob(bot_id=new_bot.id, url=url_to_scrape, status='pending', limit=max_urls)
        db.session.add(new_job)
        db.session.flush() 

        app_obj = current_app._get_current_object()
        thread = threading.Thread(target=async_scrape_task, args=(app_obj, new_job.id, url_to_scrape, new_bot.id, use_spider))
        thread.start()

    db.session.commit()    
    
    session['active_bot_id'] = new_bot.id
    session['active_bot_name'] = new_bot.bot_name
    session['theme_color'] = new_ui.theme_color
    session['header_color'] = new_ui.header_color
    session['theme_mode'] = new_ui.theme_mode

    return jsonify({"success": True, "bot_id": new_bot.id})

@admin_bp.route('/rename_bot/<int:bot_id>', methods=['POST'])
def rename_bot(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    new_name = request.form.get('new_bot_name')
    if not new_name or new_name.strip() == '':
        flash("Error: Bot name cannot be empty.", "error")
        return redirect(url_for('admin_bp.admin_dashboard'))

    target_bot = Bot.query.filter_by(id=bot_id, org_id=session['org_id']).first()
    if target_bot:
        target_bot.bot_name = new_name.strip()
        db.session.commit()

        if session.get('active_bot_id') == bot_id:
            session['active_bot_name'] = target_bot.bot_name

        flash(f"Bot renamed to '{target_bot.bot_name}'", "success")
    else:
        flash("Security Error: Bot not found.", "error")

    return redirect(request.referrer or url_for('views_bp.admin_dashboard'))

@admin_bp.route('/edit_bot/<int:bot_id>', methods=['GET'])
@admin_required
def edit_bot(bot_id):
    target_bot = Bot.query.filter_by(id=bot_id, org_id=session['org_id']).first()    
    if not target_bot:
        flash("Bot not found.", "error")
        return redirect(url_for('views_bp.dashboard'))
    ingested_docs = Document.query.filter_by(bot_id=bot_id).all()
    
    return render_template('edit_bot.html', bot=target_bot, docs=ingested_docs)

@admin_bp.route('/delete_bot/<int:bot_id>', methods=['POST'])
def delete_bot(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    target_bot = Bot.query.filter_by(id=bot_id, org_id=session['org_id']).first()
    if target_bot:
        docs = Document.query.filter_by(bot_id=target_bot.id).all()
        for doc in docs:
            delete_from_gemini(doc.filename)

        db.session.delete(target_bot)
        db.session.commit()
       
        fallback = Bot.query.filter_by(org_id=session.get('org_id')).first()
        if fallback:
            session['active_bot_id'] = fallback.id
            session['active_bot_name'] = fallback.bot_name
            
            if fallback.ui_settings:
                session['theme_color'] = fallback.ui_settings.theme_color
                session['header_color'] = fallback.ui_settings.header_color
                session['theme_mode'] = fallback.ui_settings.theme_mode
        else:
            session.pop('active_bot_id', None)
            session.pop('active_bot_name', None)
            session.pop('theme_color', None)
            session.pop('header_color', None)
            session.pop('theme_mode', None)

        flash(f"Bot: '{target_bot.bot_name}' permanently deleted.", "success")
    else:
        flash("Security Error: Bot not found.", "error")

    return redirect(request.referrer or url_for('admin_bp.admin_dashboard'))

@admin_bp.route('/update_bot/<int:bot_id>', methods=['POST'])
def update_bot(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    bot = Bot.query.filter_by(id=bot_id, org_id=session['org_id']).first()
    if not bot:
        flash("Error: Bot not found.", "error")
        return redirect(url_for('views_bp.dashboard'))

    bot.bot_name = request.form.get('bot_name', bot.bot_name)
    bot.bot_type = request.form.get('bot_type', bot.bot_type)
    bot.visibility = request.form.get('visibility', bot.visibility)
    bot.system_prompt = request.form.get('system_prompt', bot.system_prompt)
    bot.access_key = request.form.get('access_key', bot.access_key)

    if not bot.ui_settings:
        bot.ui_settings = BotUI(bot_id=bot.id)

    bot.ui_settings.theme_color = request.form.get('theme_color', bot.ui_settings.theme_color)
    bot.ui_settings.header_color = request.form.get('header_color', bot.ui_settings.header_color)
    bot.ui_settings.theme_mode = request.form.get('theme_mode', bot.ui_settings.theme_mode)
    
    # --- THIS IS THE FIX FOR THE EDIT ROUTE ---
    bot.ui_settings.glass_opacity = request.form.get('glass_opacity', bot.ui_settings.glass_opacity, type=int)
    bot.ui_settings.glass_blur = request.form.get('glass_blur', bot.ui_settings.glass_blur, type=int)

    avatar_file = request.files.get('bot_avatar')
    if avatar_file and avatar_file.filename != '':
        avatar_dir = os.path.join(current_app.root_path, 'static', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        safe_avatar_name = f"avatar_{bot.id}_{secure_filename(avatar_file.filename)}"
        save_path = os.path.join(avatar_dir, safe_avatar_name)
        avatar_file.save(save_path)
        bot.ui_settings.avatar_path = f'/static/avatars/{safe_avatar_name}'

    db.session.commit()
    
    if session.get('active_bot_id') == bot.id:
        session['active_bot_name'] = bot.bot_name
        session['theme_color'] = bot.ui_settings.theme_color
        session['header_color'] = bot.ui_settings.header_color
        session['theme_mode'] = bot.ui_settings.theme_mode

    flash("Bot configurations updated successfully!", "success")
    return redirect(url_for('admin_bp.edit_bot', bot_id=bot.id))

@admin_bp.route('/add_knowledge/<int:bot_id>', methods=['POST'])
def add_knowledge(bot_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    bot = Bot.query.filter_by(id=bot_id, org_id=session['org_id']).first()
    if not bot:
        flash("Error: Bot not found.", "error")
        return redirect(url_for('views_bp.dashboard'))

    file = request.files.get('file')
    if file and file.filename != '':
        filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_doc = Document(bot_id=bot.id, filename=filename)
        db.session.add(new_doc)
        db.session.commit()

        try:
            upload_to_gemini(filepath, bot.store_id)
            flash(f"Success: '{file.filename}' added to knowledge base.", "success")
        except Exception as e:
            flash(f"Gemini Upload Error: {str(e)}", "error")
    else:
        flash("Error: No file selected.", "error")

    return redirect(url_for('admin_bp.edit_bot', bot_id=bot.id))

@admin_bp.route('/delete_doc/<int:doc_id>', methods=['POST'])
def delete_doc(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    doc = Document.query.get_or_404(doc_id)
    
    bot = Bot.query.filter_by(id=doc.bot_id, org_id=session['org_id']).first()
    if bot:
        try:
            delete_from_gemini(doc.filename)
        except Exception as e:
            print(f"Gemini Delete Error: {e}")
            
        db.session.delete(doc)
        db.session.commit()
        flash("Document deleted from Vector Store.", "success")
    else:
        flash("Security Error: Unauthorized to delete this document.", "error")

    return redirect(url_for('admin_bp.edit_bot', bot_id=bot.id))