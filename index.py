from flask import Flask, request, jsonify, render_template, send_from_directory
import sqlite3, os
from werkzeug.utils import secure_filename
from process_data import process_data
import requests

app = Flask(__name__)
DATABASE = 'smc.db'  
os.makedirs('data', exist_ok=True)
SERVER_URL = ""

def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection

def close_db_connection(connection):
    connection.close()

@app.route('/stock', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form['category']
        products = request.form.getlist('product') 

        connection = get_db_connection()

        if not products:
            cursor = connection.execute('SELECT NameToDisplay AS `Name`, Vendor, Category, Barcode, PurchaseInvNo AS `Invoice No.`, MRP, Size, CurStock AS `Stock`, CostRate FROM stock WHERE Category=? ORDER BY Name, Size', [category])
        else:
            cursor = connection.execute('SELECT NameToDisplay AS `Name`, Vendor, Category, Barcode, PurchaseInvNo AS `Invoice No.`, MRP, Size, CurStock AS `Stock`, CostRate FROM stock WHERE Category=? AND Product IN ({}) ORDER BY Name, Size'.format(','.join('?' for _ in products)), [category, *products])
        stock_items = cursor.fetchall()
        close_db_connection(connection)
        return jsonify(stock_items=[dict(item) for item in stock_items])

    else:
        connection = get_db_connection()
        cursor = connection.execute('SELECT DISTINCT Category FROM stock ORDER BY Category ASC')
        categories = [row['Category'] for row in cursor.fetchall()]

        categories_and_products = {}
        for category in categories:
            cursor = connection.execute('SELECT DISTINCT Product FROM stock WHERE Category=?', [category])
            products = [row['Product'] for row in cursor.fetchall()]
            categories_and_products[category] = products

        close_db_connection(connection)

        return render_template('index.html', categories_and_products=categories_and_products)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join('data', filename)

    try:
        file.save(file_path)
        print(f"File '{filename}' uploaded successfully")
        headers = {"content-type": "text/plain"}
        requests.post(SERVER_URL, data=str("DB File Received"), headers=headers)
        process_data(file_path)

        return jsonify({'message': 'File uploaded and data processed successfully'}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': 'Error while saving the file'}), 500

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('pwa', 'manifest.json', mimetype='application/json')

@app.route('/service-worker.js')
def serve_service_worker():
    return send_from_directory('pwa', 'service-worker.js', mimetype='application/javascript')

def format_invoice_with_time(invoice_no, entry_time):
    formatted_time = datetime.strptime(entry_time, '%Y-%m-%d %H:%M:%S').strftime('%I:%M %p')
    return f"{invoice_no} ({formatted_time})"

def get_today_sales():
    today = datetime.today().date()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT InvoiceNo, sum(amount), sum(profit), TranName, ID, SalesInvoiceEntryTime, SalesReturnEntryTime
        FROM sales
        WHERE SalesInvoiceEntryDate =? OR SalesReturnEntryDate = ? Group By EntryNo ORDER BY SalesInvoiceEntryTime DESC
    """, (today, today))
    sales = cursor.fetchall()
    formatted_sales = []

    for row in sales:
        if row[5] is not None:
            formatted_invoice = format_invoice_with_time(row[0], row[5][:19])
            formatted_sales.append((formatted_invoice, row[1], row[2], row[3], row[4], row[6]))
        elif row[6] is not None:
            formatted_invoice = format_invoice_with_time(row[0], row[6][:19])
            formatted_sales.append((formatted_invoice, row[1], row[2], row[3], row[4], row[6]))

    conn.close()
    return formatted_sales

def get_sales_by_date(selected_date):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT InvoiceNo, sum(amount), sum(profit), TranName, ID, SalesInvoiceEntryTime, SalesReturnEntryTime
        FROM sales
        WHERE SalesInvoiceEntryDate =? OR SalesReturnEntryDate = ? Group By EntryNo ORDER BY SalesInvoiceEntryTime DESC
    """, (selected_date, selected_date))
    sales = cursor.fetchall()
    formatted_sales = []
    for row in sales:
        if row[5] is not None:
            formatted_invoice = format_invoice_with_time(row[0], row[5][:19])
            formatted_sales.append((formatted_invoice, row[1], row[2], row[3], row[4], row[6]))
        elif row[6] is not None:
            formatted_invoice = format_invoice_with_time(row[0], row[6][:19])
            formatted_sales.append((formatted_invoice, row[1], row[2], row[3], row[4], row[6]))

    conn.close()
    return formatted_sales

def calculate_totals(sales):
    total_profit = sum(sale[2] for sale in sales)
    total_amount = sum(sale[1] for sale in sales)
    total_invoices = len(sales)
    return total_profit, total_amount, total_invoices

@app.route('/')
def sales():
    sales = get_today_sales()
    total_profit, total_amount, total_invoices = calculate_totals(sales)
    return render_template('sales.html', sales=sales, total_profit=total_profit, total_amount=total_amount, total_invoices=total_invoices)

@app.route('/view-sales', methods=['GET', 'POST'])
def view_sales():
    if request.method == 'GET':
        selected_date_str = request.args.get('selected_date')
        if selected_date_str:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d')
            formatted_date = selected_date.strftime('%d %B %Y')
            sales = get_sales_by_date(selected_date_str)
            total_profit, total_amount, total_invoices = calculate_totals(sales)
            return render_template('sales.html', sales=sales, selected_date=formatted_date, total_profit=total_profit, total_amount=total_amount, total_invoices=total_invoices)
    return redirect('/')

@app.route('/invoice-details/<invoiceNo>')
def invoice_details(invoiceNo):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT NameToDisplay, Size, Qty, Amount
        FROM sales
        WHERE ID = ?;
    """, (invoiceNo,))
    invoice_details = cursor.fetchall()
    conn.close()
    total_products = sum(detail[2] for detail in invoice_details)
    total_amount = sum(detail[3] for detail in invoice_details)
    return render_template('invoice_details.html', invoice_details=invoice_details, total_products=total_products, total_amount=total_amount)


@app.route('/product-query', methods=['GET', 'POST'])
def product_query():
    if request.method == 'POST':
        category = request.form['category']
        products = request.form.getlist('product') 

        conn = sqlite3.connect(DATABASE)
        sqlite_cursor = conn.cursor()

        sqlite_cursor.execute(f"SELECT DISTINCT ProdID FROM stock WHERE Product='{products[0]}'")
        pid = sqlite_cursor.fetchall()
        sqlite_cursor.close()
        query = f"""
        SET NOCOUNT ON;
        declare @p4 dbo.Filter
        insert into @p4 values(1)

        exec uspProdQryDtlGet @frmDt='2023-04-01 00:00:00',@ToDt='2023-09-23 00:00:00',@ProdID={pid[0][0]},@LocationFilter=@p4,@FKLocationID=default,@Barcode=0
        """
        print(query)
        sql_server_conn = odbc.connect(connection_string)
        cursor = sql_server_conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        return jsonify({'data': data})

    else:
        connection = get_db_connection()
        cursor = connection.execute('SELECT DISTINCT Category FROM stock ORDER BY Category ASC')
        categories = [row['Category'] for row in cursor.fetchall()]

        categories_and_products = {}
        for category in categories:
            cursor = connection.execute('SELECT DISTINCT Product FROM stock WHERE Category=?', [category])
            products = [row['Product'] for row in cursor.fetchall()]
            categories_and_products[category] = products

        close_db_connection(connection)

        return render_template('product_query.html', categories_and_products=categories_and_products)

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('pwa', 'manifest.json', mimetype='application/json')

@app.route('/service-worker.js')
def serve_service_worker():
    return send_from_directory('pwa', 'service-worker.js', mimetype='application/javascript')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True)
