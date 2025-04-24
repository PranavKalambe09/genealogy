# app.py
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_required
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()  # Generate a random secret key

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Import the User class and get_user function
from auth import get_user, auth_bp

# Register the user loader
@login_manager.user_loader
def load_user(user_id):
    return get_user(user_id)

# Register the blueprint
app.register_blueprint(auth_bp)

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('genealogy.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/family_tree')
@login_required
def family_tree():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all individuals
    cursor.execute('SELECT * FROM Individual')
    individuals = cursor.fetchall()
    
    # Get all relationships
    cursor.execute('''
        SELECT r.*, i1.FirstName as Name1, i1.LastName as LastName1, 
        i2.FirstName as Name2, i2.LastName as LastName2
        FROM Relationship r
        JOIN Individual i1 ON r.IndividualID1 = i1.IndividualID
        JOIN Individual i2 ON r.IndividualID2 = i2.IndividualID
    ''')
    relationships = cursor.fetchall()
    
    conn.close()
    return render_template('family_tree.html', 
                           individuals=individuals, 
                           relationships=relationships)

@app.route('/add_individual', methods=['POST'])
@login_required
def add_individual():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        gender = request.form['gender']
        birth_date = request.form['birth_date']
        death_date = request.form['death_date'] if request.form['death_date'] else None
        occupation = request.form['occupation']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Individual (FirstName, LastName, Gender, BirthDate, DeathDate, Occupation)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, gender, birth_date, death_date, occupation))
        conn.commit()
        conn.close()
        
        flash('Individual added successfully!', 'success')
        return redirect(url_for('family_tree'))

@app.route('/add_relationship', methods=['POST'])
@login_required
def add_relationship():
    if request.method == 'POST':
        individual1 = request.form['individual1']
        individual2 = request.form['individual2']
        relationship_type = request.form['relationship_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date'] if request.form['end_date'] else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Relationship (IndividualID1, IndividualID2, RelationshipType, StartDate, EndDate)
            VALUES (?, ?, ?, ?, ?)
        ''', (individual1, individual2, relationship_type, start_date, end_date))
        conn.commit()
        conn.close()
        
        flash('Relationship added successfully!', 'success')
        return redirect(url_for('family_tree'))

if __name__ == '__main__':
    app.run(debug=True)