from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import joblib
import os
import pandas as pd

print("SMARTDESK STARTED")

app = Flask(__name__)

# SQLITE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smartdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# SECRET KEY
app.secret_key = "smartdesk_secret"

# MAIL CONFIGURATION
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

# LOAD ML MODELS
category_model = joblib.load(
    'category_model.pkl'
)

priority_model = joblib.load(
    'priority_model.pkl'
)

# USER TABLE
class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100)
    )

    email = db.Column(
        db.String(100)
    )

    password = db.Column(
        db.String(100)
    )

# TICKET TABLE
class Ticket(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    issue_text = db.Column(
        db.Text
    )

    category = db.Column(
        db.String(100)
    )

    priority = db.Column(
        db.String(50)
    )

    status = db.Column(
        db.String(50)
    )

    assigned_to = db.Column(
        db.String(100)
    )

# HOME
@app.route('/')
def home():

    return redirect(
        '/login'
    )

# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        user = User(
            username=username,
            email=email,
            password=password
        )

        db.session.add(user)

        db.session.commit()

        return redirect(
            '/login'
        )

    return render_template(
        'register.html'
    )

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(
            email=email,
            password=password
        ).first()

        if user:

            session['user'] = email

            return redirect(
                '/dashboard'
            )

        else:

            return "Invalid Email or Password"

    return render_template(
        'login.html'
    )

# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:

        return redirect(
            '/login'
        )

    return render_template(
        'dashboard.html'
    )

# SUBMIT TICKET
@app.route('/submit_ticket', methods=['POST'])
def submit_ticket():

    if 'user' not in session:

        return redirect(
            '/login'
        )

    ticket = request.form['ticket']

    category = category_model.predict(
        [ticket]
    )[0]

    priority = priority_model.predict(
        [ticket]
    )[0]

    solutions = {

        "Network": "Check WiFi and router settings",

        "Hardware": "Inspect hardware connections",

        "Software": "Update or reinstall software",

        "Account": "Reset password"

    }

    solution = solutions.get(
        category,
        "Contact support"
    )

    new_ticket = Ticket(

        issue_text=ticket,

        category=category,

        priority=priority,

        status="Open",

        assigned_to="Not Assigned"
    )

    db.session.add(new_ticket)

    db.session.commit()



    # MOCK EMAIL NOTIFICATION
    email_message = f"""
Mock Email Notification

Ticket Submitted Successfully

Category : {category}

Priority : {priority}

Support Team Will Contact You Soon
"""

    print("EMAIL SENT SUCCESSFULLY")

    return render_template(

        'dashboard.html',

        category=category,

        priority=priority,

        solution=solution,

        email_message=email_message
    )

# LOGOUT
@app.route('/logout')
def logout():

    session.pop(
        'user',
        None
    )

    session.pop(
        'admin',
        None
    )

    return redirect(
        '/login'
    )

# HISTORY
@app.route('/history')
def history():

    if 'user' not in session:

        return redirect(
            '/login'
        )

    tickets = Ticket.query.all()

    return render_template(
        'history.html',
        tickets=tickets
    )

# EXPORT CSV
@app.route('/export')
def export():

    tickets = Ticket.query.all()

    data = []

    for ticket in tickets:

        data.append([

            ticket.id,

            ticket.issue_text,

            ticket.category,

            ticket.priority,

            ticket.status,

            ticket.assigned_to
        ])

    df = pd.DataFrame(

        data,

        columns=[

            'ID',

            'Issue',

            'Category',

            'Priority',

            'Status',

            'Assigned To'
        ]
    )

    df.to_csv(
        'tickets_export.csv',
        index=False
    )

    return "CSV Exported Successfully"

# ADMIN LOGIN
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "admin123":

            session['admin'] = username

            return redirect(
                '/admin'
            )

        else:

            return "Invalid Admin Credentials"

    return render_template(
        'admin_login.html'
    )

# ADMIN DASHBOARD
@app.route('/admin')
def admin():

    if 'admin' not in session:

        return redirect(
            '/admin_login'
        )

    tickets = Ticket.query.all()

    return render_template(
        'admin.html',
        tickets=tickets
    )

# DELETE TICKET
@app.route('/delete_ticket/<int:id>')
def delete_ticket(id):

    if 'admin' not in session:

        return redirect(
            '/admin_login'
        )

    ticket = Ticket.query.get(id)

    db.session.delete(ticket)

    db.session.commit()

    return redirect(
        '/admin'
    )

# RESOLVE TICKET
@app.route('/resolve/<int:id>')
def resolve(id):

    if 'admin' not in session:

        return redirect(
            '/admin_login'
        )

    ticket = Ticket.query.get(id)

    ticket.status = "Resolved"

    db.session.commit()

    return redirect(
        '/admin'
    )

# ASSIGN TICKET
@app.route('/assign/<int:id>', methods=['POST'])
def assign(id):

    if 'admin' not in session:

        return redirect(
            '/admin_login'
        )

    technician = request.form['technician']

    ticket = Ticket.query.get(id)

    ticket.assigned_to = technician

    db.session.commit()

    return redirect(
        '/admin'
    )

# TEST EMAIL
@app.route('/test_email')
def test_email():

    return "SmartDesk Email Notification Working Successfully"

# CREATE USER
@app.route('/create_user')
def create_user():

    existing_user = User.query.filter_by(
        email="danielfinney1935@gmail.com"
    ).first()

    if existing_user:

        return "User Already Exists"

    user = User(

        username="Daniel",

        email="danielfinney1935@gmail.com",

        password="12345"
    )

    db.session.add(user)

    db.session.commit()

    return "User Created Successfully"

# CREATE DATABASE
with app.app_context():

    db.create_all()

# RUN APP
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )