import sqlite3
import datetime
import random

# Use this file to generate past sample consumption records 
# for a given user and ingridient id.
username = "Abhijeet"
ingridient_id = 1
daysFromToday = 500


db = sqlite3.connect(
    "./instance/data.sqlite",
    detect_types = sqlite3.PARSE_DECLTYPES
)

db.row_factory = sqlite3.Row

for i in range(daysFromToday):
    date = (datetime.datetime.today()-datetime.timedelta(days=i)).strftime("%Y-%m-%d")
    
    # command if you don't want to change any value if already present
    '''
    db.execute(
        "INSERT OR IGNORE INTO {}_consumption_records "
        "(consumption_date, ingridient_id, quantity_consumed) "
        "VALUES (?,?,?);".format(username),
        (date, ingridient_id, random.uniform(6,10))
    )
    '''

    # command if you want to insert or update values (if already present)
    db.execute(
        "INSERT INTO {}_consumption_records "
        "(consumption_date, ingridient_id, quantity_consumed) "
        "VALUES (?,?,?) "
        "ON CONFLICT (consumption_date, ingridient_id) "
        "DO UPDATE SET quantity_consumed = excluded.quantity_consumed;".format(username),
        (date, ingridient_id, random.uniform(8,10))
    )


db.commit()
db.close()