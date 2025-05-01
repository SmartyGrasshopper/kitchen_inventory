DROP TABLE IF EXISTS {username}_ingridients;
DROP TABLE IF EXISTS {username}_batches;
DROP TABLE IF EXISTS {username}_supply_orders;
DROP TABLE IF EXISTS {username}_suppliers;
DROP TABLE IF EXISTS {username}_consumption_records;

DROP VIEW IF EXISTS {username}_stocks_view;
DROP VIEW IF EXISTS {username}_supplierinfo_view;
DROP VIEW IF EXISTS {username}_supplyorders_view;

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
    order_date TIMESTAMP NOT NULL,
    supplier_id INTEGER NOT NULL,
    rate FLOAT NOT NULL,
    FOREIGN KEY (ingridient_id) REFERENCES {username}_ingridients (id),
    FOREIGN KEY (supplier_id) REFERENCES {username}_suppliers (id)
);

CREATE TABLE {username}_batches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ingridient_id INTEGER NOT NULL,
    supply_order_id INTEGER NOT NULL,
    arrival_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    disposal_date TIMESTAMP,
    payment_date TIMESTAMP,
    quantity_initial FLOAT NOT NULL,
    quantity_defective FLOAT NOT NULL,
    quantity_available FLOAT NOT NULL,
    quantity_expired FLOAT NOT NULL,
    FOREIGN KEY (ingridient_id) REFERENCES {username}_ingridients (id),
    FOREIGN KEY (supply_order_id) REFERENCES {username}_supply_orders (id)
);

CREATE TABLE {username}_consumption_records(
    consumption_date DATE NOT NULL,
    ingridient_id INTEGER NOT NULL,
    quantity_consumed FLOAT NOT NULL,
    FOREIGN KEY (ingridient_id) REFERENCES {username}_ingridients (id),
    CONSTRAINT unique_ingridient_date UNIQUE (consumption_date, ingridient_id)
);


CREATE VIEW {username}_stocks_view AS 
    SELECT 
        {username}_ingridients.id AS id, 
        {username}_ingridients.ingridient_name AS ingridient_name,
        COALESCE(S1.total_quantity,0) AS quantity_available,
        COALESCE(S1.total_batches,0) AS batches_available,
        {username}_ingridients.measuring_unit AS measuring_unit
    FROM {username}_ingridients 
    LEFT JOIN (
        SELECT ingridient_id, SUM(quantity_available) as total_quantity, COUNT(*) AS total_batches
        FROM {username}_batches
        WHERE disposal_date IS NULL
        GROUP BY ingridient_id
    ) AS S1 
    ON {username}_ingridients.id = S1.ingridient_id;

CREATE VIEW {username}_supplierinfo_view AS
    SELECT 
        suppliers.id AS id, 
        suppliers.supplier_name AS supplier_name,
        COALESCE(supply_details.pwd,0) AS payment_with_defective,
        COALESCE(supply_details.pwod,0) AS payment_without_defective
    FROM {username}_suppliers AS suppliers
    LEFT JOIN (
        SELECT 
            supply_orders.supplier_id AS supplier_id,
            SUM(_batches.quantity_initial * supply_orders.rate) AS pwd,
            SUM((_batches.quantity_initial - _batches.quantity_defective) * supply_orders.rate) AS pwod
        FROM {username}_batches AS _batches
        LEFT JOIN {username}_supply_orders AS supply_orders
        ON _batches.supply_order_id = supply_orders.id
        WHERE _batches.payment_date IS NULL
        GROUP BY supply_orders.supplier_id
    ) AS supply_details
    ON suppliers.id = supply_details.supplier_id;

CREATE VIEW {username}_supplyorders_view AS
    SELECT
        {username}_supply_orders.id AS id,
        {username}_ingridients.ingridient_name AS ingridient_name,
        {username}_ingridients.measuring_unit AS measuring_unit,
        {username}_supply_orders.quantity AS quantity,
        {username}_supply_orders.consumption_start AS consumption_start,
        {username}_supply_orders.order_date AS order_date,
        {username}_suppliers.supplier_name AS supplier_name,
        {username}_supply_orders.rate AS rate,
        supply_quantity.supplied_quantity AS supplied_quantity
    FROM {username}_supply_orders
    LEFT JOIN {username}_suppliers ON {username}_supply_orders.supplier_id = {username}_suppliers.id
    LEFT JOIN {username}_ingridients ON {username}_supply_orders.ingridient_id = {username}_ingridients.id
    LEFT JOIN (
        SELECT supply_order_id, SUM(quantity_initial) AS supplied_quantity
        FROM {username}_batches
        GROUP BY supply_order_id
    ) AS supply_quantity ON {username}_supply_orders.id = supply_quantity.supply_order_id
    WHERE {username}_supply_orders.consumption_start > CURRENT_TIMESTAMP
    ORDER BY {username}_supply_orders.consumption_start;