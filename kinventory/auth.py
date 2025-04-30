from flask import (
    Blueprint, render_template,
    session, request,
    flash, redirect, url_for, g
)

import functools

from werkzeug.security import check_password_hash

from kinventory.database import get_db, create_new_user

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/signin', methods=('GET', 'POST'))
def signin():
    if(request.method == 'POST'):
        username = request.form['username']
        password = request.form['password']

        db = get_db()

        user = db.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            flash('User "{}" does not exit.'.format(username), 'info')
        elif not check_password_hash(user['psword'], password):
            flash('Incorrect password.', 'info')
        else:
            session.clear()
            session['username'] = username
            return redirect(url_for('inventory.inventory'))
        
    return render_template('auth_views/sign_in.html')

@bp.route('/signup', methods=('GET', 'POST'))
def signup():
    if(request.method == 'POST'):
        username = request.form['username']
        password = request.form['password']
        business_name = request.form['business_name']
        
        error, message = create_new_user(username, password, business_name)

        if(error):
            flash(message, 'error')
        else:
            flash("Sign-Up successful for the username {}".format(username), 'success')
            return redirect(url_for("auth.signin"))
        db = get_db()

        
    return render_template('auth_views/sign_up.html') 
    
@bp.route('/logout', methods=('POST',))
def logout():
    session.clear()
    flash('Logged-out successfully.', 'success')
    return redirect(url_for('index'))

@bp.before_app_request
def load_logged_in_user():
    # if a user is signed-in, load its detail in g object
    # before every request so that its details are available
    # throughout the request (through g).

    username = session.get('username')

    if username is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()

def signin_required(view):
    # wrap any view that requires a user to be logged in
    # with this decorator

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
             flash("Last visited page requires sign-in.", 'info')
             return redirect(url_for('auth.signin'))
        return view(**kwargs)
    return wrapped_view