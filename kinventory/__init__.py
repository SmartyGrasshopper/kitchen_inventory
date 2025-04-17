import os
from flask import Flask

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
    @app.route('/')
    def home():
        return "<html>" \
        "<head><title>Kitchen Inventory</title><link rel=icon href=/static/favicon.png type=image/png></head>" \
        "<body>Home Page</body></html>", 200

    
    return app