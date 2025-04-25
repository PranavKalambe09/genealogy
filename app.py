from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, current_user, login_required
import sqlite3
import os
import datetime

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

def get_user_tree_id(user_id):
    """Get the user's tree ID, or create a new tree if none exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user already has a tree
    cursor.execute('SELECT TreeID FROM FamilyTree WHERE OwnerID = ?', (user_id,))
    tree = cursor.fetchone()
    
    if tree:
        tree_id = tree['TreeID']
    else:
        # Create a new tree for the user
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO FamilyTree (TreeName, OwnerID, Description, IsPublic, CreatedDate, LastModifiedDate)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (f"{user_id}'s Family Tree", user_id, "My personal family tree", 0, current_date, current_date))
        conn.commit()
        tree_id = cursor.lastrowid
    
    conn.close()
    return tree_id

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/family_tree')
@login_required
def family_tree():
    # Get the user's tree ID
    tree_id = get_user_tree_id(current_user.id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get individuals belonging to this tree
    cursor.execute('SELECT * FROM Individual WHERE TreeID = ?', (tree_id,))
    individuals = cursor.fetchall()
    
    # Get relationships for individuals in this tree
    cursor.execute('''
        SELECT r.*, i1.FirstName as Name1, i1.LastName as LastName1, 
        i2.FirstName as Name2, i2.LastName as LastName2
        FROM Relationship r
        JOIN Individual i1 ON r.IndividualID1 = i1.IndividualID
        JOIN Individual i2 ON r.IndividualID2 = i2.IndividualID
        WHERE i1.TreeID = ? AND i2.TreeID = ?
    ''', (tree_id, tree_id))
    relationships = cursor.fetchall()
    
    conn.close()
    return render_template('family_tree.html', 
                          individuals=individuals, 
                          relationships=relationships)

@app.route('/api/family-tree-data')
@login_required
def family_tree_data():
    # Get the user's tree ID
    tree_id = get_user_tree_id(current_user.id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get individuals belonging to this tree
    cursor.execute('SELECT * FROM Individual WHERE TreeID = ?', (tree_id,))
    individuals = [dict(row) for row in cursor.fetchall()]
    
    # Get relationships for individuals in this tree
    cursor.execute('''
        SELECT r.*, i1.FirstName as FirstName1, i1.LastName as LastName1, 
        i2.FirstName as FirstName2, i2.LastName as LastName2
        FROM Relationship r
        JOIN Individual i1 ON r.IndividualID1 = i1.IndividualID
        JOIN Individual i2 ON r.IndividualID2 = i2.IndividualID
        WHERE i1.TreeID = ? AND i2.TreeID = ?
    ''', (tree_id, tree_id))
    relationships = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Format data for D3.js visualization
    nodes = []
    links = []
    
    # Create nodes for each individual
    for person in individuals:
        nodes.append({
            'id': person['IndividualID'],
            'name': f"{person['FirstName']} {person['LastName']}",
            'gender': person['Gender'],
            'birthDate': person['BirthDate'],
            'deathDate': person['DeathDate'],
            'occupation': person['Occupation']
        })
    
    # Create links for relationships
    for rel in relationships:
        links.append({
            'source': rel['IndividualID1'],
            'target': rel['IndividualID2'],
            'type': rel['RelationshipType'],
            'startDate': rel['StartDate'],
            'endDate': rel['EndDate']
        })
    
    return {'nodes': nodes, 'links': links}

@app.route('/add_individual', methods=['POST'])
@login_required
def add_individual():
    if request.method == 'POST':
        # Get the user's tree ID
        tree_id = get_user_tree_id(current_user.id)
        
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        gender = request.form['gender']
        birth_date = request.form['birth_date']
        death_date = request.form['death_date'] if request.form['death_date'] else None
        occupation = request.form['occupation']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Individual (FirstName, LastName, Gender, BirthDate, DeathDate, Occupation, TreeID)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, gender, birth_date, death_date, occupation, tree_id))
        
        # Update the last modified date for the tree
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE FamilyTree SET LastModifiedDate = ? WHERE TreeID = ?', 
                      (current_date, tree_id))
        
        conn.commit()
        conn.close()
        
        flash('Individual added successfully!', 'success')
        return redirect(url_for('family_tree'))
    
@app.route('/delete_individual', methods=['POST'])
@login_required
def delete_individual():
    individual_id = request.form['individual_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM Individual WHERE IndividualID = ?', (individual_id,))
    conn.commit()
    conn.close()
    flash('Individual deleted successfully!', 'success')
    return redirect(url_for('family_tree'))

@app.route('/add_relationship', methods=['POST'])
@login_required
def add_relationship():
    if request.method == 'POST':
        # Get the user's tree ID
        tree_id = get_user_tree_id(current_user.id)
        
        individual1 = request.form['individual1']
        individual2 = request.form['individual2']
        relationship_type = request.form['relationship_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date'] if request.form['end_date'] else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verify both individuals belong to the user's tree
        cursor.execute('''
            SELECT COUNT(*) as count FROM Individual 
            WHERE (IndividualID = ? OR IndividualID = ?) AND TreeID = ?
        ''', (individual1, individual2, tree_id))
        result = cursor.fetchone()
        
        if result['count'] != 2:
            conn.close()
            flash('Cannot create relationship: one or both individuals do not belong to your family tree.', 'danger')
            return redirect(url_for('family_tree'))
        
        # Add the relationship
        cursor.execute('''
            INSERT INTO Relationship (IndividualID1, IndividualID2, RelationshipType, StartDate, EndDate, TreeID)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (individual1, individual2, relationship_type, start_date, end_date, tree_id))
        
        # Update the last modified date for the tree
        current_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('UPDATE FamilyTree SET LastModifiedDate = ? WHERE TreeID = ?', 
                      (current_date, tree_id))
        
        conn.commit()
        conn.close()
        
        flash('Relationship added successfully!', 'success')
        return redirect(url_for('family_tree'))

def setup_database():
    conn = sqlite3.connect('genealogy.db')
    cursor = conn.cursor()
    
    # Create FamilyTree table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS FamilyTree (
        TreeID INTEGER PRIMARY KEY AUTOINCREMENT,
        TreeName TEXT NOT NULL,
        OwnerID INTEGER NOT NULL,
        Description TEXT,
        IsPublic INTEGER DEFAULT 0,
        CreatedDate TEXT,
        LastModifiedDate TEXT,
        FOREIGN KEY (OwnerID) REFERENCES Users(id)
    )
    ''')
    
    # Check if Individual table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Individual'")
    if not cursor.fetchone():
        # Create Individual table with TreeID column
        cursor.execute('''
        CREATE TABLE Individual (
            IndividualID INTEGER PRIMARY KEY AUTOINCREMENT,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Gender TEXT,
            BirthDate TEXT,
            DeathDate TEXT,
            Occupation TEXT,
            TreeID INTEGER,
            FOREIGN KEY (TreeID) REFERENCES FamilyTree(TreeID)
        )
        ''')
    else:
        # Modify Individual table to include TreeID if it doesn't exist
        cursor.execute("PRAGMA table_info(Individual)")
        columns = cursor.fetchall()
        has_tree_id = any(col[1] == 'TreeID' for col in columns)
        if not has_tree_id:
            cursor.execute('ALTER TABLE Individual ADD COLUMN TreeID INTEGER')
    
    # Check if Relationship table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Relationship'")
    if not cursor.fetchone():
        # Create Relationship table with TreeID column
        cursor.execute('''
        CREATE TABLE Relationship (
            RelationshipID INTEGER PRIMARY KEY AUTOINCREMENT,
            IndividualID1 INTEGER NOT NULL,
            IndividualID2 INTEGER NOT NULL,
            RelationshipType TEXT NOT NULL,
            StartDate TEXT,
            EndDate TEXT,
            TreeID INTEGER,
            FOREIGN KEY (IndividualID1) REFERENCES Individual(IndividualID),
            FOREIGN KEY (IndividualID2) REFERENCES Individual(IndividualID),
            FOREIGN KEY (TreeID) REFERENCES FamilyTree(TreeID)
        )
        ''')
    else:
        # Modify Relationship table to include TreeID if it doesn't exist
        cursor.execute("PRAGMA table_info(Relationship)")
        columns = cursor.fetchall()
        has_tree_id = any(col[1] == 'TreeID' for col in columns)
        if not has_tree_id:
            cursor.execute('ALTER TABLE Relationship ADD COLUMN TreeID INTEGER')

    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_individual_tree ON Individual(TreeID)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_relationship_tree ON Relationship(TreeID)')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)