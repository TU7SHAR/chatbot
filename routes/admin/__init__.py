from flask import Blueprint

from .. import profile
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')
from . import dashboard, bot_management, doc_management, scrape_managment, upload_text