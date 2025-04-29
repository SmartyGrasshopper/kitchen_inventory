UPDATE {username}_batches
SET payment_date = CURRENT_DATE
WHERE payment_date IS NULL
AND supply_order_id IN(
    SELECT id FROM {username}_supply_orders
    WHERE supplier_id = {supplier_id}
);