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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        category = request.form['category']
        products = request.form.getlist('product') 

        connection = get_db_connection()

        if not products:
            cursor = connection.execute('SELECT NameToDisplay AS `Name`, Vendor, Category, Barcode, PurchaseInvNo AS `Invoice No.`, MRP, Size, CurStock AS `Stock` FROM stock WHERE Category=? ORDER BY Name, Size', [category])
        else:
            cursor = connection.execute('SELECT NameToDisplay AS `Name`, Vendor, Category, Barcode, PurchaseInvNo AS `Invoice No.`, MRP, Size, CurStock AS `Stock` FROM stock WHERE Category=? AND Product IN ({}) ORDER BY Name, Size'.format(','.join('?' for _ in products)), [category, *products])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1337, debug=True)
