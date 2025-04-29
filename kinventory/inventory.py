from flask import (
    Blueprint, render_template,
    session, request,
    flash, redirect, url_for, g,
    Response
)

from werkzeug.security import generate_password_hash, check_password_hash

import io
import matplotlib
matplotlib.use('agg')   # using agg backend so that matplotlib does not create a GUI loop
import matplotlib.pyplot as plt

from kinventory.database import get_db
from kinventory.auth import signin_required, load_logged_in_user

bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@bp.route("/inventory", methods=('GET', 'POST'))
@signin_required
def inventory():
    db = get_db()
    if(request.method == 'POST'):
        if('add_ingridient' in request.form):
            try:
                db.execute(
                    "INSERT INTO {}_ingridients (ingridient_name, supply_type, measuring_unit)"
                    "VALUES (?,?,?)".format(g.user['username']),
                    (request.form['new_ingridient_name'], "EXTERNAL", request.form['measuring_unit'])
                )
                db.commit()
            except db.IntegrityError:
                flash("Error: Ingridient name '{}' already in use. Please use a unique ingridient name.".format(request.form['new_ingridient_name']))
            else:
                flash("New ingridient added successfully.")

    stockData = db.execute("SELECT * FROM {}_stocks_view".format(g.user['username'])).fetchall()
    return render_template("inventory_views/inventory.html", stockData=stockData)

@bp.route("/supply", methods=('GET', 'POST'))
@signin_required
def supply():
    db = get_db()
    if(request.method == 'POST'):
        if('add_supplier' in request.form):
            try:
                db.execute(
                    "INSERT INTO {username}_suppliers (supplier_name) VALUES (?);".format(username=g.user['username']),
                    (request.form['supplier_name'],)
                )
                db.commit()
            except db.IntegrityError:
                flash("Error: Supplier name '{}' is already in use. Please use a unique name.".format(request.form['supplier_name']))
            else:
                flash("Supplier added successfully.")

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

@bp.route("/consumption_graph/<ingridient_name>", methods=('GET',))
@signin_required
def consumption_graph(ingridient_name):
    fig, ax = plt.subplots()
    x = [-4,-3,-2,-1]
    y = [8,7.8,9,8.5]
    ax.plot(x,y, label="Past", color="#5555FF")
    ax.plot([-1,0,1],[8.5,9,9.2], label="Prediction", color="#5555FF", linestyle="dashed")
    plt.title("Consumption analytics for {}\nDummy graph".format(ingridient_name))
    plt.legend()
    ax.set_xlabel("Day")
    ax.set_ylabel("Consumption (in kg)")

    buf = io.BytesIO()
    plt.savefig(buf, format='webp')
    buf.seek(0)
    plt.close(fig)

    return Response(buf.read(), mimetype='image/webp')

@bp.route("/wastage_graph/<ingridient_name>", methods=('GET',))
@signin_required
def wastage_graph(ingridient_name):
    fig, ax = plt.subplots()
    x = [1,2,3]
    y1 = [5,2,4]
    y2 = [2,4,3]
    ax.plot(x,y1, label="Expiry Percentage")
    ax.plot(x,y2, label="Defective Percentage")
    ax.legend()
    ax.set_xlabel('Batch No.')
    ax.set_ylabel('Percent')
    ax.set_title("Wastage analytics for {}\n(Dummy Graph)".format(ingridient_name))

    buf = io.BytesIO()
    plt.savefig(buf, format='webp')
    buf.seek(0)
    plt.close(fig)

    return Response(buf.read(), mimetype='image/webp')