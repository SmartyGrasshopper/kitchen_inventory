from flask import (
    Blueprint, render_template,
    session, request,
    flash, redirect, url_for
)

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/signin', methods=('GET', 'POST'))
def signin():
    if(request.method == 'POST'):
        ## handle post logic
        pass
    else:
        return render_template('auth_views/sign_in.html')

@bp.route('/signup', methods=('GET', 'POST'))
def signup():
    if(request.method == 'POST'):
        ## handle post logic
        pass
    else:
        return render_template('auth_views/sign_up.html') 
    
@bp.route('/logout', methods=('GET', 'POST'))
def logout():
    session.clear()
    flash('Logged-out successfully.')
    return redirect(url_for('index'))