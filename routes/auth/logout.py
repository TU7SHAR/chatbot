from flask import redirect, url_for, session, flash
from . import auth_bp  

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "error")
    return redirect(url_for('auth.login'))