import mysql.connector
def connect_to_db():
    return mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="root@123",
    database="Project",
    use_pure=True)

def get_basic_info(cursor):
    queries = {
        "total_suppliers": """
        SELECT COUNT(*) AS TOTAL_SUPPLIERS
        FROM suppliers;
    """,

        "total_products": """
        SELECT COUNT(*) AS TOTAL_PRODUCTS
        FROM products;
    """,

        "total_categories": """
        SELECT COUNT(DISTINCT category) AS TOTAL_CATEGORIES
        FROM products;
    """,
        "total sales value(last 3 months)": """
    SELECT COALESCE(
        ROUND(SUM(ABS(se.change_quantity) * p.price), 2),
        0
    ) AS total_sales_value
    FROM stock_entries se
    JOIN products p
        ON p.product_id = se.product_id
    WHERE se.change_type = 'Sale'
    AND se.entry_date >= (
        SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
        FROM stock_entries
        WHERE change_type = 'Sale'
    );
    """,
        "total restock value (last 3months)": """
        SELECT ROUND(SUM(ABS(se.change_quantity) * p.price), 2) AS Restock
        FROM stock_entries se
        JOIN products p
            ON p.product_id = se.product_id
        WHERE se.change_type = 'Restock'
        AND se.entry_date >= (
            SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
            FROM stock_entries
        );
    """,

        "below reorder & no pending reorders": """
        SELECT COUNT(*)
        FROM products p
        WHERE p.stock_quantity < p.reorder_level
        AND p.product_id NOT IN (
            SELECT DISTINCT product_id
            FROM reorders
            WHERE status = 'Ordered'
        );
    """}
    result={}
    for label, query in queries.items():
        cursor.execute(query)
        row = cursor.fetchone()

        print("LABEL:", label)
        print("ROW:", row)

        result[label] = list(row.values())[0]
    return result
def get_additional_tables(cursor):
    queries={
"Supplier Contact Details":"select supplier_name,contact_name,email,phone from suppliers;",
"Product with Supplier and Stock":"""
select 
p.product_name,
s.supplier_name,
p.stock_quantity,
p.reorder_level from products p
join suppliers s on
p.supplier_id=s.supplier_id
order by product_name asc""",
"Products Needing Reorder":"""
select product_name,stock_quantity,reorder_level 
from products where stock_quantity<reorder_level;
""",
}
    tables={}
    for label,query in queries.items():
        cursor.execute(query)
        tables[label]=cursor.fetchall()
    return tables


def add_new_manual_id(cursor, db, p_name, p_category,
                      p_price, p_stock, p_reorder, p_supplier):
    proc_call = "Call AddNewProductManualID(%s,%s,%s,%s,%s,%s)"

    params = (
        p_name,
        p_category,
        p_price,
        p_stock,
        p_reorder,
        p_supplier
    )
    cursor.execute(proc_call, params)
    db.commit()
def get_categories(cursor):
    cursor.execute("Select distinct category from products order by category asc")
    rows=cursor.fetchall()
    return [row["category"] for row in rows]
def get_suppliers(cursor):
    cursor.execute("select supplier_id,supplier_name from suppliers order by supplier_name asc")
    return cursor.fetchall()
def get_all_products(cursor):
    cursor.execute("select product_id,product_name from products order by product_name")
    return cursor.fetchall()
def get_product_history(cursor,product_id):
    query="select * from product_inventory_history where product_id=%s  order by record_date Desc"
    cursor.execute(query,(product_id,))
    return cursor.fetchall()
def place_reorder(cursor,db,product_id,reorder_quantity):
    query="""
    insert into reorders (reorder_id,product_id,reorder_quantity,reorder_date,status)
    select max(reorder_id)+1,%s,%s,curdate(),"ordered" from reorders;"""
    cursor.execute(query,(product_id,reorder_quantity))
    db.commit()
def get_pending_reorders(cursor):
    cursor.execute(""" select r.reorder_id,p.product_name from reorders as r join products as p on r.product_id=p.product_id
    where r.status='ordered'"""
    )
    return cursor.fetchall()
def mark_reorder_as_received(cursor,db,reorder_id):
    cursor.callproc("MarkReorderAsReceived",[reorder_id])
    db.commit()

