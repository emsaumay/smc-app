from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)
DATABASE = 'smc.db'  # Replace with your database name

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
            cursor = connection.execute('SELECT NameToDisplay AS `Name`, ManufacturingCo AS `Vendor`, MarketingCo AS `Category`, StockValue, LotMRP AS `MRP`, Size, Stock FROM stock WHERE Category=?', [category])
        else:
            cursor = connection.execute('SELECT NameToDisplay AS `Name`, ManufacturingCo AS `Vendor`, MarketingCo AS `Category`, StockValue, LotMRP AS `MRP`, Size, Stock FROM stock WHERE Category=? AND Product IN ({})'.format(','.join('?' for _ in products)), [category, *products])
        stock_items = cursor.fetchall()
        close_db_connection(connection)
        return jsonify(stock_items=[dict(item) for item in stock_items])

    else:
        connection = get_db_connection()
        cursor = connection.execute('SELECT DISTINCT Category FROM stock')
        categories = [row['Category'] for row in cursor.fetchall()]

        categories_and_products = {}
        for category in categories:
            cursor = connection.execute('SELECT DISTINCT Product FROM stock WHERE Category=?', [category])
            products = [row['Product'] for row in cursor.fetchall()]
            categories_and_products[category] = products

        close_db_connection(connection)

        return render_template('index.html', categories_and_products=categories_and_products)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
