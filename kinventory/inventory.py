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
            ingridient_id = int(request.form['ingridient_id'])
            quantity = float(request.form['quantity'])

            # check if enough quantity present
            # if yes, do two things
            # (a) reduce that quantity from availability,
            #     probably starting with the oldest batch.
            #     Dispose the batches where available quantity is reduced to 0.
            # (b) add the consumed quantity to consumption
            #     records against ingridient and today's date.

            ingridient_batches = db.execute(
                "SELECT id, quantity_available "
                "FROM {}_batches "
                "WHERE ingridient_id = ? "
                "AND disposal_date IS NULL;".format(g.user['username']),
                (ingridient_id,)
            )

            updateData = []
            Q = quantity
            for i, q in ingridient_batches:
                if(Q > q):
                    updateData.append((i,0))
                    Q -= q
                else:
                    updateData.append((i, q-Q))
                    Q = 0
                    break

            if(Q > 0):
                flash('Not enough quantity present in inventory to consume.', 'info')
            else:
                try:
                    # updating the quantity in batches
                    for id, q in updateData:
                        if(q==0):
                            db.execute(
                                "UPDATE {}_batches "
                                "SET quantity_available = {}, disposal_date = CURRENT_TIMESTAMP "
                                "WHERE id = {};".format(g.user['username'], q, id)
                            )
                        else:
                            db.execute(
                                "UPDATE {}_batches "
                                "SET quantity_available = {} "
                                "WHERE id = {};".format(g.user['username'], q, id)
                            )

                    # adding the record to consumption records (UPSERT OPERATION)
                    db.execute(
                        "INSERT INTO {}_consumption_records "
                        "(consumption_date, ingridient_id, quantity_consumed) VALUES (CURRENT_DATE,?,?) "
                        "ON CONFLICT (consumption_date, ingridient_id) "
                        "DO UPDATE SET quantity_consumed = quantity_consumed + excluded.quantity_consumed;".format(g.user['username']),
                        (ingridient_id, quantity)
                    )
                except:
                    db.rollback()
                    flash('Some error occured.', 'error')
                else:
                    db.commit()
                    
                    disposedIDs=[str(id) for id,q in updateData if q==0]

                    flash('Consumption reported successfully.', 'success')
                    if(disposedIDs):
                        flash('Batch ID {} disposed on getting empty.'.format(', '.join(disposedIDs)), 'info')
        elif('report_expiry' in request.form):
            username = g.user['username']
            ingridient_id = int(request.form['ingridient_id'])
            batch_id = int(request.form['batch_id'])
            expired_quantity = float(request.form['expired_quantity'])

            batchDetails = db.execute(
                "SELECT * FROM {}_batches "
                "WHERE id = {};".format(username, batch_id)
            ).fetchone()

            if(batchDetails['disposal_date'] != None):
                flash('Batch-ID {} is already disposed on {}. Details cannot be updated.'.format(batch_id, batchDetails['disposal_date']), 'info')
            elif(batchDetails['ingridient_id'] != ingridient_id):
                flash('Selected ingridient (Ingridient-ID {}) does not match with batch details (Batch-ID {}). '
                      'Please check the details.'.format(ingridient_id, batch_id), 'error')
            elif(float(batchDetails['quantity_available']) < expired_quantity):
                flash("Expired quantity cannot be greater than "
                      "quantity currently available in the batch ({} units).".format(
                          batchDetails['quantity_available']
                      ), 'info')
            else:
                remaining_quantity = float(batchDetails['quantity_available']) - expired_quantity
                total_expired_quantity = float(batchDetails['quantity_expired']) + expired_quantity

                try:
                    if(remaining_quantity > 0):
                        db.execute(
                            "UPDATE {}_batches "
                            "SET quantity_available = {}, quantity_expired = {} "
                            "WHERE id = {};".format(username, remaining_quantity, total_expired_quantity, batch_id)
                        )
                    else:
                        db.execute(
                            "UPDATE {}_batches "
                            "SET quantity_available = {}, quantity_expired = {}, disposal_date = CURRENT_TIMESTAMP "
                            "WHERE id = {};".format(username, remaining_quantity, total_expired_quantity, batch_id)
                        )
                except:
                    db.rollback()
                    flash("Some error occured while processing the request.", 'error')
                else:
                    db.commit()
                    flash('Expired quantity successfully submitted for Batch-ID {}. '
                          'Remaining units {}.'.format(batch_id, remaining_quantity), 'success')
                    if(remaining_quantity == 0):
                        flash('Batch-ID {} disposed as available quantity reduced to 0.'.format(batch_id), 'info')

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
            flash("No functionality to handle the submitted form.", 'error')
    

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

@bp.route("/analytics", methods=('GET', 'POST'))
@signin_required
def analytics():
    db = get_db()
    ingridientID = None

    if(request.method=='POST'):
        if('analytics_ingridient_id' in request.form):
            ingridientID = int(request.form['analytics_ingridient_id'])
        else:
            flash('No functionality to handle the submitted form.', 'error')

    ingridientsList = db.execute(
        "SELECT id, ingridient_name, measuring_unit FROM {}_ingridients;".format(g.user['username'])
    ).fetchall()
    return render_template(
        "inventory_views/analytics.html", 
        ingridientsList=ingridientsList, ingridientID = ingridientID
    )

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

@bp.route("/consumption_graph/<ingridient_id>/<measuring_unit>", methods=('GET',))
@signin_required
def consumption_graph(ingridient_id,measuring_unit):
    db = get_db()
    ingridient_id = int(ingridient_id)
    historySeconds = 50*24*60*60 # seconds in 50 days

    consumptionData = db.execute(
        "SELECT consumption_date, quantity_consumed "
        "FROM {}_consumption_records "
        "WHERE ingridient_id = {} "
        "AND (unixepoch(CURRENT_DATE) - unixepoch(consumption_date))<({}) "
        "AND consumption_date != CURRENT_DATE "
        "ORDER BY consumption_date;".format(
                g.user['username'], ingridient_id, historySeconds
            )
    ).fetchall()

    y = [x['quantity_consumed'] for x in consumptionData]
    #x = [x['consumption_date'] for x in consumptionData]

    # calculating predicion list using simple moving average
    max_window_size = 50
    prediction_length = 10

    prediction = []
    window_size = min(len(y), max_window_size)
    if(window_size > 0):
        dp = list(map(lambda x: x/window_size, y[len(y)-window_size:]))
        s = sum(dp)
        left = 0
        for i in range(prediction_length):
            prediction.append(s)
            dp.append(s/window_size)
            s += dp[-1]
            s -= dp[left]
            left += 1


    # Custom theme definitions
    plt.rcParams['grid.color']='white'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor']='#F5F5F5'
    plt.rcParams['axes.edgecolor']='black'
    plt.rcParams['ytick.color'] = 'gray'
    plt.rcParams['xtick.color'] = 'gray'
    plt.rcParams['ytick.labelcolor'] = 'gray'
    plt.rcParams['xtick.labelcolor'] = 'gray'
    plt.rcParams['axes.labelcolor']='gray'
    plt.rcParams['axes.titlecolor']='gray'
    plt.rcParams['axes.spines.top']=False
    plt.rcParams['axes.spines.right']=False
    plt.rcParams['axes.spines.left']=False
    plt.rcParams['legend.facecolor']='white'
    plt.rcParams['legend.edgecolor']='white'
    plt.rcParams['legend.labelcolor']='grey'
    # custom theme definitions
    
    fig, ax = plt.subplots()
    ax.plot(range(-len(y),0),y, label="Past", color="chocolate", linewidth=1) #, marker='o', markersize=3)
    if(window_size > 0):
        ax.plot(range(0,prediction_length),prediction, label="Prediction", color="chocolate", linestyle="dashed", linewidth=1)
    else:
        plt.title("Not enough data present for analytics.")
    plt.legend()
    ax.grid()
    ax.set_xlabel("Day")
    ax.set_ylabel("Consumption ({})".format(measuring_unit))

    buf = io.BytesIO()
    plt.savefig(buf, format='webp')
    buf.seek(0)
    plt.close(fig)

    return Response(buf.read(), mimetype='image/webp')

@bp.route("/wastage_graph/<ingridient_id>", methods=('GET',))
@signin_required
def wastage_graph(ingridient_id):
    db = get_db()

    wastageData = db.execute(
        "SELECT id, (quantity_defective/quantity_initial)*100 AS defective_percent, "
        "CASE "
        "   WHEN disposal_date IS NULL THEN (quantity_expired/(quantity_initial-quantity_defective))*100 "
        "   ELSE ((quantity_expired+quantity_available)/(quantity_initial-quantity_defective))*100 "
        "END AS expiry_percent "
        "FROM {}_batches WHERE ingridient_id={} "
        "ORDER BY id ASC;".format(g.user['username'], int(ingridient_id))
    ).fetchall()

    expiryData = [w['expiry_percent'] for w in wastageData]
    defectiveData = [w['defective_percent'] for w in wastageData]

    # Custom theme definitions
    plt.rcParams['grid.color']='white'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor']='#F5F5F5'
    plt.rcParams['axes.edgecolor']='black'
    plt.rcParams['ytick.color'] = 'gray'
    plt.rcParams['xtick.color'] = 'gray'
    plt.rcParams['ytick.labelcolor'] = 'gray'
    plt.rcParams['xtick.labelcolor'] = 'gray'
    plt.rcParams['axes.labelcolor']='gray'
    plt.rcParams['axes.titlecolor']='gray'
    plt.rcParams['axes.spines.top']=False
    plt.rcParams['axes.spines.right']=False
    plt.rcParams['axes.spines.left']=False
    plt.rcParams['legend.facecolor']='white'
    plt.rcParams['legend.edgecolor']='white'
    plt.rcParams['legend.labelcolor']='grey'
    # custom theme definitions

    fig, ax = plt.subplots()
    if(wastageData):
        ax.plot(expiryData, label="Expired", color='goldenrod', linewidth=1)
        ax.plot(defectiveData, label="Defective", color='darkkhaki', linewidth=1)
    ax.legend()
    ax.set_xlabel('nth batch of ingridient')
    ax.set_ylabel('Percent')
    ax.grid()
    #ax.set_title("Wastage analytics for {}\n(Dummy Graph)".format(ingridient_id))

    buf = io.BytesIO()
    plt.savefig(buf, format='webp')
    buf.seek(0)
    plt.close(fig)

    return Response(buf.read(), mimetype='image/webp')