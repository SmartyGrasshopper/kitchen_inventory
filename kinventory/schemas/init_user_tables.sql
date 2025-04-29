DROP TABLE IF EXISTS {username}_ingridients;
DROP TABLE IF EXISTS {username}_batches;
DROP TABLE IF EXISTS {username}_supply_orders;
DROP TABLE IF EXISTS {username}_suppliers;
DROP TABLE IF EXISTS {username}_consumption_records;

DROP VIEW IF EXISTS {username}_stocks_view;

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


CREATE VIEW {username}_stocks_view AS 
    SELECT {username}_ingridients.id AS id, {username}_ingridients.ingridient_name AS ingridient_name,
    COALESCE(S1.total_quantity,0) AS quantity_available, COALESCE(S1.total_batches,0) AS batches_available,
    {username}_ingridients.measuring_unit AS measuring_unit
    FROM {username}_ingridients 
    LEFT JOIN (
        SELECT ingridient_id, SUM(quantity_available) as total_quantity, COUNT(*) AS total_batches
        FROM {username}_batches
        WHERE disposal_date = NULL
        GROUP BY ingridient_id
    ) AS S1 
    ON {username}_ingridients.id = S1.ingridient_id;