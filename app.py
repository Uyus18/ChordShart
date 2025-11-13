from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3, os

app = Flask(__name__)
app.secret_key = "chordchart_secret"

# --- Database setup ---
def init_db():
    # Users table
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

    # Orders table
    conn = sqlite3.connect("shop.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            price REAL,
            quantity INTEGER,
            total REAL,
            fullname TEXT,
            email TEXT,
            address TEXT,
            payment_method TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_shop_connection():
    return sqlite3.connect("shop.db")

# --- Home ---
@app.route('/')
def index():
    if "username" in session:
        return render_template("index.html", username=session["username"])
    return redirect(url_for("login"))

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = username
            flash("Login successful!", "success")
            return redirect(url_for("shop"))
        else:
            flash("Invalid username or password.", "error")
    return render_template("login.html")

# --- Signup ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists.", "error")
        finally:
            conn.close()
    return render_template("signup.html")

# --- Logout ---
@app.route('/logout')
def logout():
    session.pop("username", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

# --- Shop ---
@app.route('/shop')
def shop():
    if "username" not in session:
        return redirect(url_for("login"))

    guitars = [
        {"name": "Fender Stratocaster", "price": 45000},
        {"name": "Gibson Les Paul", "price": 75000},
        {"name": "Ibanez RG Series", "price": 52000},
        {"name": "Yamaha Acoustic F310", "price": 10500},
        {"name": "Taylor 214ce", "price": 65000},
        {"name": "PRS Custom 24", "price": 90000},
    ]
    return render_template('shop.html', guitars=guitars)

# --- Add to Cart ---
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    name = request.form.get("name")
    price = float(request.form.get("price"))
    quantity = int(request.form.get("quantity", 1))

    if "cart" not in session:
        session["cart"] = []

    cart = session["cart"]

    # Check if item already in cart
    for item in cart:
        if item["name"] == name:
            item["quantity"] += quantity
            break
    else:
        cart.append({"name": name, "price": price, "quantity": quantity})

    session["cart"] = cart
    flash(f"{name} added to cart!", "success")
    return redirect(url_for("shop"))

# --- Cart Page ---
@app.route('/cart')
def cart():
    cart = session.get("cart", [])
    total_price = sum(item["price"] * item["quantity"] for item in cart)
    return render_template("cart.html", cart=cart, total_price=total_price)

# --- Checkout ---
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', [])
    total_price = sum(item['price']*item['quantity'] for item in cart)

    if request.method == 'POST':
        fullname = request.form['fullname']
        email = request.form['email']
        address = request.form['address']
        payment_method = request.form['payment_method']
        username = session.get('username')

        # Connect to shop.db
        conn = sqlite3.connect("shop.db")
        cursor = conn.cursor()

        # Insert each item from cart
        for item in cart:
            cursor.execute("""
                INSERT INTO orders (id, username, total, payment_method, address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                username, 
                item['name'], 
                item['price'], 
                item['quantity'], 
                item['price']*item['quantity'], 
                fullname, 
                email, 
                address, 
                payment_method
            ))

        conn.commit()
        conn.close()

        # Clear cart
        session.pop('cart', None)
        flash("Thank you! Your order has been placed.", "success")
        return redirect(url_for('shop'))

    return render_template("checkout.html", cart=cart, total_price=total_price)


if __name__ == "__main__":
    app.run(debug=True)
