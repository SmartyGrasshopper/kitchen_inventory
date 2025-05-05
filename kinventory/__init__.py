import os
from flask import Flask, render_template

def create_app(test_config = None):

    # creating and configuring the app object
    app = Flask(
        __name__, 
        instance_relative_config = True, 
        instance_path = "{}/instance".format(os.getcwd())
    )

    app.config.from_mapping(
        SECRET_KEY='kitchenInventory_18April2025',
        DATABASE = os.path.join(app.instance_path, 'data.sqlite')
    )

    # ensuring instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    # defining routes
    @app.route('/', methods=('GET',))
    def index():
        return render_template('index.html')
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    # registering blue-prints for other views
    from kinventory import auth, inventory
    app.register_blueprint(auth.bp)
    app.register_blueprint(inventory.bp)

    # adding db functionality to the app
    from kinventory import database
    database.add_db_functionality(app)
    
    return app