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
    

@app.route('/', methods=["GET", "POST"])
def render_home_page():
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
    return render_template('home.html', logged_in=is_logged_in())


@app.route('/menu/<cat_id>', methods=["GET", "POST"])
def render_menu_page(cat_id):
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

    # Select all the products in this category
    query = "SELECT name, description, volume, price, filename FROM product WHERE cat_id = ? ORDER BY name"
    conn = create_connection(DATABASE)
    cur = conn.cursor()
    cur.execute(query, (cat_id, ))
    coffees = cur.fetchall()
    
    # Get the list of categories to display on the page as links
    cat_query = "SELECT * FROM category"
    cur.execute(cat_query)
    categories = cur.fetchall()
    conn.close()
    return render_template('menu.html', drinks=coffees, categories=categories, cat_id=cat_id, logged_in=is_logged_in())


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html', logged_in=is_logged_in())


@app.route('/login', methods=["GET", "POST"])
def render_login_page():
    if is_logged_in():
        return redirect("/")
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
        
    return render_template('login.html')


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
        
    return render_template("signup.html")


@app.route('/logout')
def logout():
    [session.pop(key) for key in list(session.keys())]
    return redirect('/?message=See+you+next+time')


app.run(host='0.0.0.0', debug=True)