from flask import (
    Blueprint, render_template,
    session, request,
    flash, redirect, url_for, g
)

from kinventory.database import get_db
from kinventory.auth import signin_required

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route("/account", methods=('GET',))
@signin_required
def account():
    return render_template("inventory_views/account.html")