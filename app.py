from flask import Flask, render_template, request, redirect
import sqlite3
app = Flask(__name__)

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
    return render_template('home.html')


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
    return render_template('menu.html', drinks=coffees, categories=categories, cat_id=cat_id)


@app.route('/contact')
def render_contact_page():
    return render_template('contact.html')


app.run(host='0.0.0.0', debug=True)