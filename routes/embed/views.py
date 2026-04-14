from flask import Blueprint, render_template, request, session, redirect, url_for, flash, make_response
from models.models import Bot, User, db

views_bp = Blueprint('views_bp', __name__)

@views_bp.route('/')
def index():
    # if session.get('user_id'): 
    #     return redirect(url_for('views_bp.dashboard'))
    return render_template('index.html')

@views_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@views_bp.route('/compare')
@views_bp.route('/compare/<competitor>')
def compare(competitor=None):
    # Protect against template injection by only allowing files we know exist
    valid_competitors = ['chatbase', 'tidio', 'intercom', 'gupshup']
    
    if competitor:
        # Clean up the URL just in case the frontend link says "chatbase.html" instead of just "chatbase"
        clean_name = competitor.replace('.html', '')
        
        # If the competitor matches one of our templates, render it
        if clean_name in valid_competitors:
            return render_template(f'compare_{clean_name}.html')
        else:
            # If a user types a random competitor URL, redirect them back to the main compare page safely
            return redirect(url_for('views_bp.compare'))
            
    # Default route for the main '/compare' directory page
    return render_template('compare.html')

@views_bp.route('/dashboard')
def dashboard():
    if not session.get('user_id'): return redirect(url_for('auth.login'))
        
    my_bots = Bot.query.filter_by(created_by=session['user_id']).all()
    all_org_bots = Bot.query.filter(Bot.org_id == session['org_id'], Bot.created_by != session['user_id']).all()
    member_count = User.query.filter_by(org_id=session.get('org_id')).count()

    org_bots = []
    for bot in all_org_bots:
        if bot.visibility == 'public':
            org_bots.append(bot)
        elif bot.visibility == 'private' and session.get('role') == 'admin':
            org_bots.append(bot)

    return render_template('dashboard.html', 
                           my_bots=my_bots, 
                           org_bots=org_bots, 
                           member_count=member_count)

@views_bp.route('/set_active_bot/<int:bot_id>')
def set_active_bot(bot_id):
    if not session.get('user_id'): return redirect(url_for('auth.login'))
        
    target_bot = Bot.query.get(bot_id)
    if target_bot and target_bot.org_id == session.get('org_id'):
        is_creator = target_bot.created_by == session.get('user_id')
        is_unlocked = target_bot.id in session.get('unlocked_bots', [])
        
        if target_bot.visibility == 'public' or is_creator or is_unlocked:
            # 1. Set standard identifiers
            session['active_bot_id'] = target_bot.id
            session['active_bot_name'] = target_bot.bot_name
            
            # 2. FETCH UI SETTINGS (The Missing Piece!)
            # Checks if you used the BotUI separate table, or put columns directly in Bot
            if hasattr(target_bot, 'ui_settings') and target_bot.ui_settings:
                session['theme_color'] = target_bot.ui_settings.theme_color
                session['header_color'] = target_bot.ui_settings.header_color
                session['theme_mode'] = target_bot.ui_settings.theme_mode
            else:
                session['theme_color'] = getattr(target_bot, 'theme_color', '#E8722A')
                session['header_color'] = getattr(target_bot, 'header_color', '#FFFFFF')
                session['theme_mode'] = getattr(target_bot, 'theme_mode', 'light')
                
        else:
            flash("Security Error: This Bot is classified. Decryption key required.", "error")
            
    return redirect(url_for('views_bp.dashboard'))

@views_bp.route('/unlock_bot/<int:bot_id>', methods=['POST'])
def unlock_bot(bot_id):
    if session.get('role') != 'admin':
        flash("Clearance Error: Administrator privileges required.", "error")
        return redirect(url_for('views_bp.dashboard'))
    
    submitted_key = request.form.get('access_key', '').upper()
    target_bot = Bot.query.get(bot_id)
    
    if target_bot and target_bot.access_key == submitted_key:
        unlocked = session.get('unlocked_bots', [])
        if bot_id not in unlocked:
            unlocked.append(bot_id)
        session['unlocked_bots'] = unlocked
        
        # 1. Set standard identifiers
        session['active_bot_id'] = target_bot.id
        session['active_bot_name'] = target_bot.bot_name
        
        # 2. FETCH UI SETTINGS (For newly unlocked bots)
        if hasattr(target_bot, 'ui_settings') and target_bot.ui_settings:
            session['theme_color'] = target_bot.ui_settings.theme_color
            session['header_color'] = target_bot.ui_settings.header_color
            session['theme_mode'] = target_bot.ui_settings.theme_mode
        else:
            session['theme_color'] = getattr(target_bot, 'theme_color', '#E8722A')
            session['header_color'] = getattr(target_bot, 'header_color', '#FFFFFF')
            session['theme_mode'] = getattr(target_bot, 'theme_mode', 'light')
            
        flash(f"Decrypted: Access granted to {target_bot.bot_name}", "success")
    else:
        flash("Encryption Error: Invalid Access Key.", "error")
    
    return redirect(url_for('views_bp.dashboard'))
@views_bp.route('/embed/<int:bot_id>')
def embed_bot(bot_id):
    target_bot = Bot.query.get_or_404(bot_id)
    
    response = make_response(render_template('embed_chat.html', bot=target_bot))
    
    if getattr(target_bot, 'allowed_domains', None):
        response.headers['Content-Security-Policy'] = f"frame-ancestors 'self' {target_bot.allowed_domains}"
    else:
        response.headers.pop('X-Frame-Options', None)
        
    return response

@views_bp.route('/bot/<int:bot_id>/integrate')
def integrate_bot(bot_id):
    if not session.get('user_id'): 
        return redirect(url_for('auth.login'))
        
    target_bot = Bot.query.get_or_404(bot_id)
    
    if target_bot.created_by != session.get('user_id') and session.get('role') != 'admin':
        flash("Access Denied.", "error")
        return redirect(url_for('views_bp.dashboard'))
        
    return render_template('integrate.html', bot=target_bot)

@views_bp.route('/bot/<int:bot_id>/update_security', methods=['POST'])
def update_bot_security(bot_id):
    if not session.get('user_id'): 
        return redirect(url_for('auth.login'))
        
    target_bot = Bot.query.get_or_404(bot_id)
    
    if target_bot.created_by != session.get('user_id') and session.get('role') != 'admin':
        flash("Access Denied.", "error")
        return redirect(url_for('views_bp.dashboard'))
        
    allowed_domains = request.form.get('allowed_domains', '').strip()
    
    target_bot.allowed_domains = allowed_domains
    db.session.commit()
    
    flash("Security settings updated.", "success")
    return redirect(url_for('views_bp.integrate_bot', bot_id=bot_id))