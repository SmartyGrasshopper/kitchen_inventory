from flask import (
    Blueprint, render_template,
    session, request
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
    return render_template('auth_views/logout_success.html')