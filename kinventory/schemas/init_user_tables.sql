DROP TABLE IF EXISTS {username}_ingridients;
DROP TABLE IF EXISTS {username}_batches;
DROP TABLE IF EXISTS {username}_supply_orders;
DROP TABLE IF EXISTS {username}_suppliers;
DROP TABLE IF EXISTS {username}_consumption_records;

CREATE TABLE {username}_ingridients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingridient_name TEXT UNIQUE NOT NULL,
    supply_type TEXT NOT NULL,
    measuring_unit TEXT NOT NULL
);

CREATE TABLE {username}_suppliers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_name TEXT UNIQUE NOT NULL
);

CREATE TABLE {username}_supply_orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingridient_id INTEGER NOT NULL,
    quantity FLOAT NOT NULL,
    consumption_start TIMESTAMP NOT NULL,
    consumption_duration INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    rate FLOAT NOT NULL,
    order_status TEXT NOT NULL,
    FOREIGN KEY (ingridient_id) REFERENCES {username}_ingridients (id),
    FOREIGN KEY (supplier_id) REFERENCES {username}_suppliers (id)
);

CREATE TABLE {username}_batches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingridient_id INTEGER NOT NULL,
    supply_order_id INTEGER NOT NULL,
    arrival_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    disposal_date TIMESTAMP,
    quantity_initial FLOAT NOT NULL,
    quantity_defective FLOAT NOT NULL,
    quantity_available FLOAT NOT NULL,
    quantity_expired FLOAT NOT NULL,
    FOREIGN KEY (ingridient_id) REFERENCES {username}_ingridients (id),
    FOREIGN KEY (supply_order_id) REFERENCES {username}_supply_orders (id)
);

CREATE TABLE {username}_consumption_records(
    consumption_date TIMESTAMP NOT NULL,
    ingridient_id INTEGER NOT NULL,
    quantity_consumed FLOAT NOT NULL,
    FOREIGN KEY (ingridient_id) REFERENCES {username}_ingridients (id)
);

