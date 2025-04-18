import sqlite3
from datetime import datetime

import click
from flask import current_app, g

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

sqlite3.register_converter("timestamp", lambda v: datetime.fromisoformat(v.decode()))

def add_db_functionality(app):
    
    # call the close_db function after every request ends
    app.teardown_appcontext(close_db)

    # add cli commands
    app.cli.add_command(init_db_command)