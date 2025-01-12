import os
import pymysql
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

# Flask app configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'your-secret-key'  # Required for session handling

# Use environment variables for RDS configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')  # Default to localhost if not set
DB_USER = os.getenv('DB_USER', 'root')       # Default to root if not set
DB_PASSWORD = os.getenv('DB_PASSWORD', '')   # Default to empty if not set
DB_NAME = os.getenv('DB_NAME', 'test')       # Default to test if not set

print(f"Connecting to database at {DB_HOST} with user {DB_USER}")

# Database connection helper function
def get_db_connection():
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("Database connection established.")
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to database: {e}")
        return None

# Example route for testing database connection
@app.route('/db_test')
def db_test():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        conn.close()
        return {"tables": tables}
    return {"error": "Failed to connect to database"}, 500


@app.route('/update_cart', methods=['POST'])
def update_cart():
    data = request.json
    item_id = data.get('item_id')
    options = data.get('options')
    quantity = int(data.get('quantity', 1))

    key = f"{item_id}_{options}"

    if 'cart' not in session:
        session['cart'] = {}

    if quantity > 0:
        session['cart'][key] = quantity
    else:
        session['cart'].pop(key, None)

    session.modified = True

    conn = get_db_connection()
    cursor = conn.cursor()
    total = 0
    for key, quantity in session['cart'].items():
        item_id, _ = key.split('_')
        cursor.execute("SELECT price FROM items WHERE id = %s", (item_id,))
        item = cursor.fetchone()
        if item:
            total += item['price'] * quantity
    conn.close()

    return {'total': total}

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'AccuSnake' and password == 'abc123':
            session['admin'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('admin_login.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    flash('You have been logged out.', 'logout')
    return redirect(url_for('index'))

@app.route('/admin_panel')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    menu_items = cursor.fetchall()
    conn.close()

    return render_template('SQLadmin_panel.html', menu_items=menu_items)

@app.route('/uploads/<filename>')
def serve_uploads(filename):
    return send_from_directory(os.path.join(app.root_path, 'uploads'), filename)

@app.route('/admin/add', methods=['POST'])
def add_item():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    name = request.form['name']
    price = request.form['price']
    category = request.form['category']
    options = request.form.get('options', 'Default')
    description = request.form['description']
    image = request.files['image']

    if not name or not price or not category or not description or not image:
        flash('All fields are required', 'error')
        return redirect(url_for('admin_panel'))

    if image:
        filename = secure_filename(image.filename)
        upload_path = os.path.join(app.root_path, 'uploads', filename)
        if not os.path.exists(os.path.join(app.root_path, 'uploads')):
            os.makedirs(os.path.join(app.root_path, 'uploads'))
        image.save(upload_path)
        image_path = f'/uploads/{filename}'

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO items (name, category, price, image_url, description, options) VALUES (%s, %s, %s, %s, %s, %s)",
                           (name, category, price, image_path, description, options))
            conn.commit()
            flash('Item added successfully', 'success')
        except pymysql.MySQLError as e:
            flash(f'Error: {e}', 'error')
        finally:
            conn.close()

    return redirect(url_for('admin_panel'))

@app.route('/admin/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    item = cursor.fetchone()  # Returns a dictionary when using DictCursor

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        options = request.form['options']
        description = request.form['description']

        try:
            cursor.execute(
                "UPDATE items SET name = %s, price = %s, description = %s, options = %s WHERE id = %s",
                (name, price, description, options, item_id)
            )
            conn.commit()
            flash('Item updated successfully', 'success')
        except pymysql.MySQLError as e:
            flash(f"Error: {e}", 'error')
        finally:
            conn.close()

        return redirect(url_for('admin_panel'))

    conn.close()
    return render_template('SQLedit.html', item=item)


@app.route('/admin/delete/<int:item_id>')
def delete_item(item_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = %s", (item_id,))
    conn.commit()
    conn.close()

    flash('Item deleted successfully', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu/<category>')
def menu(category):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE category = %s", (category,))
    items = cursor.fetchall()
    conn.close()
    return render_template('SQLmenu.html', items=items, category=category)

@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    selected_options = request.form.get(f'options_{item_id}', 'Default')
    if 'cart' not in session:
        session['cart'] = {}

    key = f"{item_id}_{selected_options}"
    if key in session['cart']:
        session['cart'][key] += 1
    else:
        session['cart'][key] = 1

    session.modified = True
    flash('Item added to cart!', 'success')
    return redirect(request.referrer or url_for('menu', category='food'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    conn = get_db_connection()
    cursor = conn.cursor()
    items = []
    total = 0

    if 'cart' in session:
        for key, quantity in session['cart'].items():
            item_id, selected_options = key.split('_')
            cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            if item:
                item = dict(item)
                item['quantity'] = quantity
                item['options'] = selected_options
                items.append(item)
                total += item['price'] * quantity
    conn.close()
    return render_template('SQLcart.html', items=items, total=total)

@app.route('/remove_from_cart/<string:key>')
def remove_from_cart(key):
    if 'cart' in session and key in session['cart']:
        session['cart'].pop(key)
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    conn = get_db_connection()
    cursor = conn.cursor()
    total = 0
    if 'cart' in session:
        for key, quantity in session['cart'].items():
            item_id, _ = key.split('_')
            cursor.execute("SELECT price FROM items WHERE id = %s", (item_id,))
            item = cursor.fetchone()
            if item:
                total += item['price'] * quantity

    conn.close()

    flash(f'Your total is ${total}. Please proceed to checkout to complete your order.', 'checkout')
    session.pop('cart', None)
    return render_template('checkout.html')

def add_sample_items():
    conn = get_db_connection()
    cursor = conn.cursor()

    sample_items = [
        ('Burger', 'food', 7.00, '/static/burger.jpg', 'Juicy beef burger with lettuce and cheese.', 'Veg,No Veg'),
        ('Pizza', 'food', 12.00, '/static/pizza.jpg', 'Cheesy pepperoni pizza with tomato sauce.', 'Thin,Thick,Stuffed Crust'),
        ('Water', 'beverages', 1.00, '/static/water.jpg', 'Bottled mineral water.', 'Cold,Room Temp'),
        ('Coffee', 'beverages', 3.00, '/static/coffee.jpg', 'Hot cup of coffee.', 'Hot,Iced')
    ]

    for item in sample_items:
        cursor.execute("SELECT * FROM items WHERE name = %s", (item[0],))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO items (name, category, price, image_url, description, options) VALUES (%s, %s, %s, %s, %s, %s)", item)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_sample_items()
    app.run(host='0.0.0.0', port=5000)
