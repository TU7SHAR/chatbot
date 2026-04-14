import bcrypt
from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email
from sqlalchemy.exc import IntegrityError

from models.models import db, User, Organization

auth_bp = Blueprint('auth', __name__)

class RegistrationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    org_name = StringField("Organization", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            hashed_pwd = bcrypt.hashpw(
                form.password.data.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            org_name_input = form.org_name.data.strip()
            existing_org = Organization.query.filter(Organization.name.ilike(org_name_input)).first()
            
            if existing_org:
                org_to_use = existing_org
            else:
                org_to_use = Organization(name=org_name_input)
                db.session.add(org_to_use)
                db.session.commit()

            new_user = User(
                org_id=org_to_use.id,
                name=form.name.data, 
                email=form.email.data, 
                password_hash=hashed_pwd, 
                is_verified=True 
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            session['user_name'] = new_user.name
            session['org_name'] = org_to_use.name
            session['org_id'] = org_to_use.id
            
            flash("Workspace initialized successfully.", "success")
            return redirect(url_for('chat_bp.index'))
            
        except IntegrityError:
            db.session.rollback()
            flash("Email already registered.", "error")
            return redirect(url_for('auth.register'))
            
    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['org_name'] = user.organization.name
            session['org_id'] = user.org_id
            flash("Access granted.", "success")
            return redirect(url_for('chat_bp.index'))
        else:
            flash("Invalid credentials.", "error")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Session terminated.", "success")
    return redirect(url_for('auth.login'))