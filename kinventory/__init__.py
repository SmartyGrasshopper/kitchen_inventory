import os
from flask import Flask, render_template

def create_app(test_config = None):

    # creating app object
    app = Flask(
        __name__, 
        instance_relative_config = True, 
        instance_path = "{}/instance".format(os.getcwd())
    )

    # ensuring instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass


    # defining routes
    @app.route('/', methods=('GET',))
    def home():
        return render_template('other_views/index.html')

    
    return app