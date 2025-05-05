import sqlite3
import datetime
import random

# Use this file to generate past sample consumption records 
# for a given user and ingridient id.
username = "indian_cuisine"
ingridient_id = 1
daysFromToday = 500


db = sqlite3.connect(
    "./instance/data.sqlite",
    detect_types = sqlite3.PARSE_DECLTYPES
)

db.row_factory = sqlite3.Row

'''
for i in range(daysFromToday):
    date = (datetime.datetime.today()-datetime.timedelta(days=i)).strftime("%Y-%m-%d")
    
    # command if you don't want to change any value if already present
    '''
'''
    db.execute(
        "INSERT OR IGNORE INTO {}_consumption_records "
        "(consumption_date, ingridient_id, quantity_consumed) "
        "VALUES (?,?,?);".format(username),
        (date, ingridient_id, random.uniform(6,10))
    )
'''
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
'''

# data for project
data_list = [
    ["2025-05-01",2,8,3,5],
    ["2025-04-30",2.1,7.95,3.5,4.9],
    ["2025-04-29",2.18,7.2,3.96,4.75],
    ["2025-04-28",3,7,4,4.6],
    ["2025-04-27",3.2,6.98,4.12,4.45],
    ["2025-04-26",3.28,6.96,4.14,4.3],
    ["2025-04-25",3.4,6.94,4.17,4.1],
    ["2025-04-24",3.7,6.91,4.2,3.9],
    ["2025-04-23",3.75,6.9,4.23,3.72],
    ["2025-04-22",4,6.87,4.27,3.55],
    ["2025-04-21",4.1,6.86,4.3,3.42],
    ["2025-04-20",4.18,6.85,4.33,3.3],
    ["2025-04-19",4.35,6.84,4.35,3.2],
    ["2025-04-18",4.45,6.82,4.38,3.15],
    ["2025-04-17",4.5,6.8,4.4,3.02],
    ["2025-04-16",4.5,6.77,4.44,3],
    ["2025-04-15",4.5,6.76,4.47,2.95],
    ["2025-04-14",4.55,6.75,4.5,2.9],
    ["2025-04-13",4.7,6.73,4.55,2.73],
    ["2025-04-12",4.75,6.71,4.59,2.58],
    ["2025-04-11",4.79,6.65,4.63,2.42],
    ["2025-04-10",4.91,6.62,4.67,2.3],
    ["2025-04-09",4.98,6.6,4.7,2.15],
    ["2025-04-08",5,6.55,4.8,2.1],
    ["2025-04-07",5.12,6.52,4.9,2],
    ["2025-04-06",5.13,6.51,5,2.1],
    ["2025-04-05",5.15,6.48,5,2.3],
    ["2025-04-04",5.17,6.44,4.9,2.42],
    ["2025-04-03",5.17,6.41,4.75,2.35],
    ["2025-04-02",5.2,6.4,4.72,2.4],
    ["2025-04-01",5.25,6.35,4.7,2.55],
    ["2025-03-28",5.28,6.32,4.65,2.72],
    ["2025-03-27",5.3,6.3,4.62,2.84],
    ["2025-03-26",5.31,6.26,4.6,2.97],
    ["2025-03-25",5.32,6.23,4.55,3.1],
    ["2025-03-24",5.34,6.2,4.5,3.24],
    ["2025-03-23",5.4,6,4.42,3.4],
    ["2025-03-22",5.45,5.8,4.37,3.55],
    ["2025-03-21",5.47,5.75,4.3,3.7],
    ["2025-03-20",5.48,5.73,4.2,3.85],
    ["2025-03-19",5.49,5.7,4,4.2],
    ["2025-03-18",5.5,5.65,3.9,4.35],
    ["2025-03-17",5.5,5.62,3.65,4.5],
    ["2025-03-16",5.53,5.6,3.35,4.65],
    ["2025-03-15",5.57,5.55,3.2,4.7],
    ["2025-03-14",5.6,5.5,3.1,4.85],
    ["2025-03-13",5.8,5.45,3,5],
    ["2025-03-12",5.85,5.4,2.8,5.1],
    ["2025-03-11",5.9,5.3,2.7,5.3],
]


for row in data_list:
    for i in range(4):
        db.execute(
            "INSERT INTO {}_consumption_records "
            "(consumption_date, ingridient_id, quantity_consumed) "
            "VALUES (?,?,?) "
            "ON CONFLICT (consumption_date, ingridient_id) "
            "DO UPDATE SET quantity_consumed = excluded.quantity_consumed;".format(username),
            (row[0], ingridient_id+i, row[1+i])
        )

db.commit()
db.close()