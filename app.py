from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, session
from db import conn, cursor
import joblib

print("SMARTDESK STARTED")

app = Flask(__name__)

app.secret_key = "smartdesk_secret"

import os

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

        query = """
        INSERT INTO users(username,email,password)
        VALUES(%s,%s,%s)
        """

        values = (
            username,
            email,
            password
        )

        cursor.execute(query, values)

        conn.commit()

        return "Registration Successful"

    return render_template(
        'register.html'
    )


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        query = """
        SELECT * FROM users
        WHERE email=%s AND password=%s
        """

        values = (
            email,
            password
        )

        cursor.execute(query, values)

        user = cursor.fetchone()

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

    query = """
    INSERT INTO tickets(
    issue_text,
    category,
    priority,
    status
    )
    VALUES(%s,%s,%s,%s)
    """

    values = (
        ticket,
        category,
        priority,
        "Open"
    )

    cursor.execute(query, values)

    conn.commit()

    return render_template(
        'dashboard.html',
        category=category,
        priority=priority,
        solution=solution
    )


# LOGOUT
@app.route('/logout')
def logout():

    session.pop(
        'user',
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

    search = request.args.get('search')

    status = request.args.get('status')

    query = """
    SELECT * FROM tickets
    WHERE 1=1
    """

    values = []

    if search:

        query += """
        AND LOWER(issue_text)
        LIKE LOWER(%s)
        """

        values.append(
            "%" + search + "%"
        )

    if status:

        query += """
        AND status=%s
        """

        values.append(status)

    cursor.execute(
        query,
        tuple(values)
    )

    tickets = cursor.fetchall()

    return render_template(
        'history.html',
        tickets=tickets
    )

# EXPORT CSV
@app.route('/export')

def export():

    query = """
    SELECT * FROM tickets
    """

    cursor.execute(query)

    data = cursor.fetchall()

    import pandas as pd

    df = pd.DataFrame(
        data,
        columns=[
            'ID',
            'Issue',
            'Category',
            'Priority',
            'Status'
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

        query = """
        SELECT * FROM admin
        WHERE username=%s
        AND password=%s
        """

        values = (
            username,
            password
        )

        cursor.execute(query, values)

        admin = cursor.fetchone()

        if admin:

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

    query = """
    SELECT * FROM tickets
    """

    cursor.execute(query)

    tickets = cursor.fetchall()

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

    query = """
    DELETE FROM tickets
    WHERE id=%s
    """

    values = (id,)

    cursor.execute(query, values)

    conn.commit()

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

    query = """
    UPDATE tickets
    SET assigned_to=%s
    WHERE id=%s
    """

    values = (
        technician,
        id
    )

    cursor.execute(query, values)

    conn.commit()

    return redirect(
        '/admin'
    )

# TEST EMAIL
@app.route('/test_email')
def test_email():

    try:

        msg = Message(

            'SmartDesk Test Email',

            sender='danielfinney@gmail.com',

            recipients=['danielfinney1935@gmail.com']

        )

        msg.body = """
SmartDesk Email System Working Successfully
"""

        mail.send(msg)

        return "Test Email Sent Successfully"

    except Exception as e:

        return str(e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)