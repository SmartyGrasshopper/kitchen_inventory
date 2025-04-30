from flask import (
    Blueprint, render_template,
    session, request,
    flash, redirect, url_for, g,
    Response, current_app
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
                flash("Ingridient name '{}' already in use. Please use a unique ingridient name.".format(request.form['new_ingridient_name']), 'info')
            else:
                flash("New ingridient added successfully.", 'success')
        elif('add_batch' in request.form):
            supplyOrder = db.execute("SELECT * FROM {}_supply_orders WHERE id = ?;".format(g.user['username']),(request.form['supply_order_id'],)).fetchone()
            if(not supplyOrder):
                flash('Invalid supply-order ID used. Please enter a valid ID.', 'error')
            elif(supplyOrder[1] != float(request.form['ingridient_id'])):
                flash('Selected ingridient does not match with ingridient of supply-order ID.', 'error')
            elif(float(request.form['quantity_defective']) > float(request.form['quantity_initial'])):
                flash('Defective quantity cannot be greater than quantity received.', 'error')
            else:
                try:
                    db.execute(
                        "INSERT INTO {username}_batches (ingridient_id, supply_order_id, arrival_date,"
                        "quantity_initial, quantity_defective, quantity_available, quantity_expired)"
                        "VALUES (?,?,?,?,?,?,0);".format(username=g.user['username']),
                        (request.form['ingridient_id'], request.form['supply_order_id'], '{} 00:00:00'.format(request.form['arrival_date']),
                         request.form['quantity_initial'], request.form['quantity_defective'], float(request.form['quantity_initial'])-float(request.form['quantity_defective']))
                    )
                    db.commit()
                except:
                    flash('Some error occured.', 'error')
                else:
                    flash('Batch successfully added.', 'success')
        elif('dispose_batch' in request.form):
            batch_id = request.form['batch_id']
            batchDetails = db.execute(
                "SELECT * FROM {}_batches WHERE id = {};".format(g.user['username'], batch_id)
            ).fetchone()

            if(not batchDetails):
                flash("Batch ID {} does not exist.".format(batch_id), 'info')
            elif(batchDetails['disposal_date'] != None):
                flash("Batch ID {} already disposed on {}.".format(batch_id, batchDetails['disposal_date']), 'info')
            else:
                try:
                    db.execute(
                        "UPDATE {}_batches "
                        "SET disposal_date = CURRENT_TIMESTAMP "
                        "WHERE id = {};".format(g.user['username'], batch_id)
                    )
                except:
                    flash('Some error occured. Batch ID {} not disposed.'.format(batch_id), 'error')
                else:
                    db.commit()
                    flash("Batch ID {} disposed.".format(batch_id), 'success')
        elif('report_consumption' in request.form):
            ingridient_id = request.form['ingridient_id']
            quantity = request.form['quantity']

            # check if enough quantity present
            # if yes, do two things
            # (a) reduce that quantity from availability,
            #     probably starting with the oldest batch.
            # (b) add the consumed quantity to consumption
            #     records against ingridient and today's date.
            flash("Report consumption not implemented yet.", "info")

        else:
            flash('No functionality to handle submitted form.', 'error')

    stockData = db.execute("SELECT * FROM {}_stocks_view".format(g.user['username'])).fetchall()
    ingridientsList = db.execute("SELECT id, ingridient_name, measuring_unit FROM {}_ingridients;".format(g.user['username'])).fetchall()
    return render_template("inventory_views/inventory.html", 
        stockData=stockData, ingridientsList=ingridientsList)

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
                flash("Supplier name '{}' is already in use. Please use a unique name.".format(request.form['supplier_name']), 'info')
            else:
                flash("Supplier added successfully.", 'success')
        elif('settle_payment' in request.form):
            try:
                with current_app.open_resource('schemas/settle_payment.sql') as f:
                    db.executescript(f.read().decode('utf8').format(
                        username=g.user['username'], supplier_id=request.form['supplier_id']))
                db.commit()                
            except:
                flash("Some error occured.", 'error')
            else:
                flash("Marked the pending payments of supplier-id {} as settled.".format(request.form['supplier_id']), 'success')
        elif('add_order' in request.form):
            try:
                db.execute(
                    "INSERT INTO {}_supply_orders (ingridient_id, quantity, consumption_start, order_date, supplier_id, rate) VALUES (?,?,?,CURRENT_TIMESTAMP,?,?);".format(g.user['username']),
                    (request.form['ingridient_id'], request.form['quantity'], '{} 00:00:00'.format(request.form['consumption_start_date']),
                     request.form['supplier_id'], request.form['rate'])
                )
                db.commit()
            except db.IntegrityError:
                flash("Ingridient name already in use. Please use a unique ingridient name.", 'info')
            else:
                flash("Supply order added successfully.", 'success')
        else:
            pass
    

    supplierInfo = db.execute("SELECT * FROM {}_supplierinfo_view".format(g.user['username'])).fetchall()
    ingridientsList = db.execute("SELECT id, ingridient_name, measuring_unit FROM {}_ingridients;".format(g.user['username'])).fetchall()
    suppliersList = db.execute("SELECT id, supplier_name FROM {}_suppliers;".format(g.user['username']))
    activeSupplyOrders = db.execute("SELECT * FROM {}_supplyorders_view;".format(g.user['username']))
    return render_template(
        "inventory_views/supply.html", 
        supplierInfo=supplierInfo, ingridientsList=ingridientsList,
        suppliersList=suppliersList, activeSupplyOrders=activeSupplyOrders
        )

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
    db = get_db()

    ingridientsList = db.execute(
        "SELECT id, ingridient_name FROM {}_ingridients;".format(g.user['username'])
    ).fetchall()
    return render_template("inventory_views/analytics.html", ingridientsList=ingridientsList)

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

            flash("Business Name updated successfully.", 'success')

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

                flash("Password updated successfully. Please sign-in again.", 'success')

                return redirect(url_for('auth.signin'))

            else:
                flash("Failed to change password. Invalid current-password entered.", 'error')
        else:
            flash("Error. No action available for POSTed form at this route.", 'error')

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