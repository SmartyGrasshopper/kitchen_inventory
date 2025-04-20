from flask import (
    Blueprint, render_template,
    session, request,
    flash, redirect, url_for, g
)

from werkzeug.security import generate_password_hash, check_password_hash

from kinventory.database import get_db
from kinventory.auth import signin_required, load_logged_in_user

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

@bp.route("/account", methods=('GET', 'POST'))
@signin_required
def account():
    if(request.method == 'POST'):
        if('change_business_name' in request.form):
            # form to change business name is received

            db = get_db()
            db.execute(
                "UPDATE users SET business_name = ? WHERE username = ?;",
                (request.form['business_name'], g.user['username'])
            )
            db.commit()

            flash("Business Name updated successfully.")

            load_logged_in_user()  #updating the details stored in g-object before proceeding
            

        elif('change_password' in request.form):
            # form to change password is received
            
            if(check_password_hash(g.user['psword'], request.form['current_password'])):
                db = get_db()
                db.execute(
                    "UPDATE users SET psword = ? WHERE username = ?;",
                    (generate_password_hash(request.form['new_password']), g.user['username'])
                )
                db.commit()

                session.clear()   # signing/logging out

                flash("Password updated successfully. Please sign-in again.")

                return redirect(url_for('auth.signin'))

            else:
                flash("Failed to change password. Invalid current-password entered.")
        else:
            flash("Error. No action available for POSTed form at this route.")

    return render_template("inventory_views/account.html")