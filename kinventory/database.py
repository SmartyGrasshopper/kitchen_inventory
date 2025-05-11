import sqlite3
from datetime import datetime

import click
from flask import current_app, g

from werkzeug.security import generate_password_hash

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db',None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schemas/init_users.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized database and user table successfully.')

sqlite3.register_converter("timestamp", lambda v: datetime.fromisoformat(v.decode()).date())

def add_db_functionality(app):
    
    # call the close_db function after every request ends
    app.teardown_appcontext(close_db)

    # add cli commands
    app.cli.add_command(init_db_command)

def create_new_user(username, password, business_name):
    db = get_db()

    # Adding user to the users table
    try:
        db.execute(
            "INSERT INTO users (username, psword, business_name) VALUES (?,?,?);",
                (username, generate_password_hash(password), business_name)
        )        
    except db.IntegrityError:
        db.rollback()
        return (True, "Error in sign-up: Username already in use. Please select a different username.")
    
    # creating all the tables for the user's data
    f = current_app.open_resource("schemas/init_user_tables.sql")
    try:
        # Removed executescript since it commits before executing.
        # This behaviour is strictly not wanted here. We only want commit at the end.
        #db.executescript(f.read().decode('utf8').format(username=username))
        for statement in f.read().decode('utf8').split(';'):
            statement = statement.strip()
            if(statement != ''):
                statement += ';'
                db.execute(statement.format(username=username))
    except:
        db.rollback()
        return(True, 'Some error occured during signup.')
    finally:
        f.close()

    db.commit()
    return (False, "")    # False means no error