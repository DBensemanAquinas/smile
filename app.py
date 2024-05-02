from ast import Import
from flask import Flask, render_template, request, redirect, session
import sqlite3
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "kz lkahjg lisua hg ;ahsfg ;us jj"

DATABASE = "smile.db"

def create_connection(db_file):
    """ Create a connection to the sql database
    Parameters: 
    db_file - The name of the file
    Returns: A connection to the database """
    try:
        connection = sqlite3.connect(db_file)
        return connection
    except sqlite3.Error as e:
        print(e)
    return None


def is_logged_in():
    if session.get("user_name") is None:
        print("Not logged in")
        return False
    else:
        print("Logged in")
        return True
    

def is_ordering():
    if session.get("order") is None:
        print("Not ordering")
        return False
    else:
        print("Ordering")
        return True
    

@app.route('/', methods=["GET", "POST"])
def render_home_page():
    # Get the error message from the url if there is none
    error = request.args.get('error')
    if error == None:
        error=""
    
    if request.method == "POST":
        cat_name = request.form["cat_name"].lower().strip()
        if 3 <= len(cat_name) <= 20:
            conn = create_connection(DATABASE)
            query = "INSERT INTO category (name) VALUES (?)"
            cur = conn.cursor()
            cur.execute(query, (cat_name, ))
            conn.commit()
            conn.close()
        else:
            return redirect("/?error=Name+must+be+between+3+and+20+characters")
    return render_template('home.html', logged_in=is_logged_in(),   error=error, ordering = is_ordering())


@app.route('/menu/<cat_id>', methods=["GET", "POST"])
def render_menu_page(cat_id):
    # Get the error message from the url if there is none
    error = request.args.get('error')
    if error == None:
        error=""

    # Check whether there is an item to add
    if request.method == "POST":
        name = request.form["name"].title().strip()
        description = request.form["description"].strip()
        volume = request.form["volume"].strip()
        price = request.form["price"]
        file_name = request.form["filename"].lower().strip()
        conn = create_connection(DATABASE)
        query = "INSERT INTO product VALUES (null, ?, ?, ?, ?, ?, ?)"
        cur = conn.cursor()
        cur.execute(query, (name, description, volume, file_name, price, cat_id))
        conn.commit()
        conn.close()

    # Check to see whether I am starting an order
    order_start = request.args.get("order")
    if order_start == "start" and not is_ordering():
        session["order"] = []

    # Select all the products in this category
    query = "SELECT name, description, volume, price, filename, id FROM product WHERE cat_id = ? ORDER BY name"
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    cur.execute(query, (cat_id, ))
    coffees = cur.fetchall()
    
    # Get the list of categories to display on the page as links
    cat_query = "SELECT * FROM category"
    cur.execute(cat_query)
    categories = cur.fetchall()
    cat_name_query = "SELECT name FROM category WHERE id = ?"
    cur.execute(cat_name_query, (cat_id, ))
    cat_name = cur.fetchone()[0]
    print(cat_name)
    conn.close()
    return render_template('menu.html', drinks=coffees, categories=categories, cat_id=cat_id, cat_name=cat_name.upper(), logged_in=is_logged_in(), error=error, ordering = is_ordering())


@app.route('/add_to_cart/<product_id')
def add_to_cart(product_id):
    try:
        product_id = int(product_id)
    except ValueError:
        print(f"{product_id} is not an integer")
        return redirect("/menu/1?Invalid+product+id")
    
    # Add the product to the cart
    print("adding to the cart", product_id)
    order = session['order']
    print("Order before ordering:", order)
    order.append(product_id)
    print("Order after ordering:", order)
    session['order'] = order
    
    # Return to the page the link was presses from
    return redirect(request.referrer)

@app.route('/item/<cat_id>/<item_id>', methods=["GET", "POST"])
def render_item_page(cat_id, item_id):
    # Select the products details
    query = "SELECT name, description, volume, price, filename, id FROM product WHERE id = ?"
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    cur.execute(query, (item_id, ))
    coffee = cur.fetchall()[0]   
    conn.close()
    
    return render_template('item.html', drink=coffee, cat_id=cat_id, logged_in=is_logged_in(), ordering = is_ordering())

@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', logged_in=is_logged_in())


@app.route('/login', methods=["GET", "POST"])
def render_login_page():
    if is_logged_in():
        return redirect("/")
    # Get the error message from the url if there is none
    error = request.args.get('error')
    if error == None:
        error=""
    
    if request.method == "POST":
        user_name = request.form['user_name'].strip().lower()
        password = request.form['password'].strip()
        
        # Check to see whether the user is in the database
        query = "SELECT * FROM user WHERE username = ?"
        conn = create_connection(DATABASE)
        cur = conn.cursor()
        cur.execute(query, (user_name, ))
        user_data = cur.fetchone()
        conn.close()
        
        # Check to see whether there is a user in the database
        try:
            user_id = user_data[0]
            first_name = user_data[3]
            db_password = user_data[2]
        except IndexError:
            return redirect("/login?error=Invalid+email+or+password")
        
        if not bcrypt.check_password_hash(db_password, password):
            return redirect("/login?error=Invalid+email+or+password")

        session['user_id'] = user_id
        session['user_name'] = user_name
        session['first_name'] = first_name
        return redirect("/")
        
    return render_template('login.html', error=error, ordering = is_ordering())


@app.route('/signup', methods=["GET", "POST"])
def render_signup_page():
    if is_logged_in():
        return redirect("/")
    if request.method == "POST":
        user_name = request.form['username'].strip().lower()
        password = request.form['password']
        password2 = request.form['password2']
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        
        if password != password2:
            return redirect('/signup?error=Passwords+dont+match')
        
        # Hash the password
        hashed_password= bcrypt.generate_password_hash(password)

        # Add the user to the database
        conn = create_connection(DATABASE)
        query = "INSERT INTO user VALUES (NULL, ?, ?, ?, ?)"
        cur = conn.cursor()
        cur.execute(query, (user_name, hashed_password, first_name, last_name))
        conn.commit()
        conn.close()
        return redirect('/login')
        
    return render_template("signup.html", ordering = is_ordering())


@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect('/?message=See+you+next+time')


@app.route('/delete_category/<cat_id>/<cat_name>', methods = ['GET', 'POST'])
def render_delete_category(cat_id, cat_name):
    
    if not is_logged_in():
        return redirect("/")
    print(cat_id, cat_name)
    return render_template("delete_category.html", cat_id=cat_id, cat_name=cat_name, logged_in=is_logged_in(), ordering = is_ordering())


@app.route('/delete_category_confirmed/<cat_id>')
def delete_category(cat_id):
    if not is_logged_in():
        return redirect("/")
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    query = "DELETE FROM category WHERE id = ?"
    cur.execute(query, (cat_id, ))
    query = "DELETE FROM product WHERE cat_id = ?"
    cur.execute(query, (cat_id, ))
    conn.commit()
    conn.close()
    return redirect("/")
    


app.run(host='0.0.0.0', debug=True)