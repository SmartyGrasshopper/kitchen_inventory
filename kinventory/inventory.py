from flask import (
    Blueprint, render_template,
    session, request,
    flash, redirect, url_for, g
)

from kinventory.database import get_db
from kinventory.auth import signin_required

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route("/inventory", methods=('GET',))
@signin_required
def inventory():
    return render_template("inventory_views/inventory.html")

@bp.route("/supply", methods=('GET',))
@signin_required
def supply():
    return render_template("inventory_views/supply.html")

@bp.route("/consumption", methods=('GET',))
@signin_required
def consumption():
    return render_template("inventory_views/consumption.html")

@bp.route("/menu", methods=('GET',))
@signin_required
def menu():
    return render_template("inventory_views/menu.html")

@bp.route("/analytics", methods=('GET',))
@signin_required
def analytics():
    return render_template("inventory_views/analytics.html")

@bp.route("/account", methods=('GET',))
@signin_required
def account():
    return render_template("inventory_views/account.html")