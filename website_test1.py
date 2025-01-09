from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import boto3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.secret_key = 'your-secret-key'  # Required for session handling
s3 = boto3.client('s3')
BUCKET_NAME = 'your-s3-bucket-name'


# Initialize SQLite DB
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS items
                 (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, image_url TEXT, description TEXT, options TEXT)''')
    conn.commit()
    conn.close()

init_db()


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
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    total = 0
    for key, quantity in session['cart'].items():
        item_id, _ = key.split('_')
        c.execute("SELECT price FROM items WHERE id = ?", (item_id,))
        item = c.fetchone()
        if item:
            total += item[0] * quantity
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
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM items")
    menu_items = c.fetchall()
    conn.close()
    
    return render_template('admin_panel.html', menu_items=menu_items)


@app.route('/admin/add', methods=['POST'])
def add_item():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    name = request.form['name']
    price = request.form['price']
    category = request.form['category']  # Receive category from form
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
        image_path = f'uploads/{filename}'

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO items (name, category, price, image_url, description, options) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, category, price, image_path, description, options))
            conn.commit()
            flash('Item added successfully', 'success')
        except sqlite3.Error as e:
            flash(f'Error: {e}', 'error')
        finally:
            conn.close()
    return redirect(url_for('admin_panel'))



@app.route('/admin/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = c.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        options = request.form['options']
        description = request.form['description']

        c.execute("UPDATE items SET name = ?, price = ?, description = ?, options = ? WHERE id = ?",
                  (name, price, description, options, item_id))
        conn.commit()
        conn.close()

        flash('Item updated successfully', 'success')
        return redirect(url_for('admin_panel'))

    conn.close()
    return render_template('edit.html', item=item)


@app.route('/admin/delete/<int:item_id>')
def delete_item(item_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    flash('Item deleted successfully', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/menu/<category>')
def menu(category):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM items WHERE category = ?", (category,))
    items = c.fetchall()
    conn.close()
    return render_template('menu.html', items=items, category=category)

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
    flash('Item added to cart!', 'success')  # 'success' category for cart
    return redirect(request.referrer or url_for('menu', category='food'))

@app.route('/cart', methods=['GET', 'POST'])
def cart():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    items = []
    total = 0

    if 'cart' in session:
        for key, quantity in session['cart'].items():
            item_id, selected_options = key.split('_')
            c.execute("SELECT * FROM items WHERE id = ?", (item_id,))
            item = c.fetchone()
            if item:
                item = list(item)
                item.append(quantity)
                item.append(selected_options)
                items.append(item)
                total += item[3] * quantity
    conn.close()
    return render_template('cart.html', items=items, total=total)


@app.route('/remove_from_cart/<string:key>')
def remove_from_cart(key):
    if 'cart' in session and key in session['cart']:
        session['cart'].pop(key)
        session.modified = True
    return redirect(url_for('cart'))


@app.route('/checkout')
def checkout():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    total = 0
    if 'cart' in session:
        for key, quantity in session['cart'].items():
            item_id, _ = key.split('_')
            c.execute("SELECT price FROM items WHERE id = ?", (item_id,))
            item = c.fetchone()
            if item:
                total += item[0] * quantity
    
    conn.close()
    
    flash(f'Your total is ${total}. Please proceed to checkout to complete your order.', 'checkout')
    session.pop('cart', None)
    return render_template('checkout.html')

def add_sample_items():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Define some sample menu items
    sample_items = [
        ('Burger', 'food', 7.00, '/static/burger.jpg', 'Juicy beef burger with lettuce and cheese.', 'Veg,No Veg'),
        ('Pizza', 'food', 12.00, '/static/pizza.jpg', 'Cheesy pepperoni pizza with tomato sauce.', 'Thin,Thick,Stuffed Crust'),
        ('Water', 'beverages', 1.00, '/static/water.jpg', 'Bottled mineral water.', 'Cold,Room Temp'),
        ('Coffee', 'beverages', 3.00, '/static/coffee.jpg', 'Hot cup of coffee.', 'Hot,Iced')
    ]
    
    for item in sample_items:
        c.execute("SELECT * FROM items WHERE name = ?", (item[0],))
        if not c.fetchone():
            c.execute("INSERT INTO items (name, category, price, image_url, description, options) VALUES (?, ?, ?, ?, ?, ?)", item)
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    add_sample_items()
    app.run(host='0.0.0.0', port=5000)
