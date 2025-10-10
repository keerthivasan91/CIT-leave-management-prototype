from flask import Flask, render_template, request, redirect, url_for, session, jsonify
# Windows-friendly MySQL driver shim: allow PyMySQL to satisfy MySQLdb
try:
    import pymysql  # type: ignore
    pymysql.install_as_MySQLdb()
except Exception:
    # If PyMySQL is not installed yet, the app can still start for non-DB routes
    pass
from flask_mysqldb import MySQL # type: ignore

app = Flask(__name__)
app.secret_key = 'secret-key-for-demo'

# MySQL config - change password if needed
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'   # set your mysql password
app.config['MYSQL_DB'] = 'faculty_leave'

mysql = MySQL(app)

def fetch_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT id,user_id,password,role,name,department FROM users WHERE user_id=%s", (user_id,))
    u = cur.fetchone()
    cur.close()
    return u

@app.route('/api/branches')
def get_branches():
    cur = mysql.connection.cursor()
    cur.execute("SELECT DISTINCT department FROM users WHERE role='faculty' ORDER BY department")
    branches = [row[0] for row in cur.fetchall()]
    cur.close()
    return jsonify({'branches': branches})

@app.route('/api/staff/<branch>')
def get_staff_by_branch(branch):
    cur = mysql.connection.cursor()
    cur.execute("SELECT user_id, name FROM users WHERE department=%s AND role='faculty' ORDER BY name", (branch,))
    staff = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
    cur.close()
    return jsonify({'staff': staff})

@app.route('/')
def landing():
    return render_template('login.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('landing'))
    name = session.get('name')
    role = session.get('role')
    dept = session.get('department')
    # Important info points
    info = [
        "Leave requests must be approved by substitute, HOD, and Principal.",
        "Only 15 days of casual leave allowed per semester.",
        "National holidays are preloaded in Holiday Calendar."
    ]
    return render_template('index.html', name=name, role=role, info=info, department=dept)

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        user_id = request.form['user_id'].strip()
        password = request.form['password']
        role = request.form['role']

        if not role:
            error = "Please select a role"
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id,user_id,password,role,name,department FROM users WHERE user_id=%s AND password=%s AND role=%s",
                        (user_id, password, role))
            user = cur.fetchone()
            cur.close()
            if user:
                session['user_id'] = user[1]
                session['role'] = user[3]
                session['name'] = user[4]
                session['department'] = user[5]
                return redirect(url_for('home'))
            error = "Invalid credentials for selected role"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/apply', methods=['GET','POST'])
def apply():
    if 'user_id' not in session:
        return redirect(url_for('landing'))
    if request.method == 'POST':
        user_id = session['user_id']
        department = session.get('department')
        leave_type = request.form.get('leave_type', 'Casual')
        start_date = request.form['start_date'] or None
        start_session = request.form.get('start_session', 'Forenoon')
        end_date = request.form['end_date'] or None
        end_session = request.form.get('end_session', 'Afternoon')
        reason = request.form.get('reason','')
        days = int(request.form.get('days') or 1)
        substitute_user_id = request.form.get('substitute_user_id', '')

        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO leave_requests
            (user_id, department, leave_type, start_date, start_session, end_date, end_session, reason, days, substitute_user_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (user_id, department, leave_type, start_date, start_session, end_date, end_session, reason, days, substitute_user_id))
        
        leave_id = cur.lastrowid
        
        # Create substitute request
        if substitute_user_id:
            cur.execute("""INSERT INTO substitute_requests
                (leave_request_id, requested_user_id)
                VALUES (%s,%s)""",
                (leave_id, substitute_user_id))
        
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('leave_history'))
    return render_template('apply_leave.html')

@app.route('/leave_history')
def leave_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    
    # 1. Leaves applied by the user
    cur.execute("""
        SELECT lr.id, lr.leave_type, lr.start_date, lr.start_session, lr.end_date, lr.end_session, 
               lr.reason, lr.days, lr.substitute_user_id, lr.substitute_status, lr.hod_status, 
               lr.principal_status, lr.final_status, lr.applied_at, u.name as substitute_name
        FROM leave_requests lr 
        LEFT JOIN users u ON lr.substitute_user_id = u.user_id 
        WHERE lr.user_id=%s 
        ORDER BY lr.applied_at DESC 
        LIMIT 20
    """, (user_id,))
    applied_leaves = cur.fetchall()

    # 2. Substitute requests assigned to the user
    cur.execute("""
        SELECT sr.id, lr.id as leave_id, lr.user_id, lr.leave_type, lr.start_date, lr.end_date, 
               lr.days, lr.reason, sr.status, sr.responded_at, u.name as requester_name
        FROM substitute_requests sr
        JOIN leave_requests lr ON sr.leave_request_id = lr.id
        JOIN users u ON lr.user_id = u.user_id
        WHERE sr.requested_user_id=%s
        ORDER BY sr.id DESC
        LIMIT 20
    """, (user_id,))
    substitute_requests = cur.fetchall()

    cur.close()
    
    return render_template(
        'leave_history.html',
        applied_leaves=applied_leaves,
        substitute_requests=substitute_requests
    )

@app.route('/substitute_requests')
def substitute_requests():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""SELECT sr.id, lr.id as leave_id, lr.user_id, lr.leave_type, lr.start_date, lr.end_date, 
                   lr.days, lr.reason, sr.status, sr.responded_at, u.name as requester_name
                   FROM substitute_requests sr
                   JOIN leave_requests lr ON sr.leave_request_id = lr.id
                   JOIN users u ON lr.user_id = u.user_id
                   WHERE sr.requested_user_id=%s AND sr.status='Pending'
                   ORDER BY sr.id DESC LIMIT 10""", (user_id,))
    requests = cur.fetchall()
    cur.close()
    return render_template('substitute_requests.html', requests=requests)

@app.route('/accept_substitute/<int:request_id>')
def accept_substitute(request_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE substitute_requests SET status='Accepted', responded_at=NOW() WHERE id=%s", (request_id,))
    cur.execute("""UPDATE leave_requests lr 
                   JOIN substitute_requests sr ON lr.id = sr.leave_request_id 
                   SET lr.substitute_status='Accepted', lr.substitute_responded_at=NOW() 
                   WHERE sr.id=%s""", (request_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('substitute_requests'))

@app.route('/reject_substitute/<int:request_id>')
def reject_substitute(request_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE substitute_requests SET status='Rejected', responded_at=NOW() WHERE id=%s", (request_id,))
    cur.execute("""UPDATE leave_requests lr 
                   JOIN substitute_requests sr ON lr.id = sr.leave_request_id 
                   SET lr.substitute_status='Rejected', lr.substitute_responded_at=NOW(), lr.final_status='Rejected'
                   WHERE sr.id=%s""", (request_id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('substitute_requests'))

@app.route('/holiday_calendar')
def holiday_calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, date, name FROM holidays ORDER BY date")
    holidays = cur.fetchall()
    cur.close()
    return render_template('holiday_calendar.html', holidays=holidays)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(final_status='Approved') AS approved,
            SUM(final_status='Rejected') AS rejected,
            SUM(final_status='Pending') AS pending,
            SUM(days) AS total_days
        FROM leave_requests WHERE user_id=%s
    """, (user_id,))
    stats = cur.fetchone()
    cur.close()
    return render_template('profile.html', stats=stats)

# HOD dashboard - same UI but extra Approve tab
@app.route('/hod')
def hod_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'hod':
        return redirect(url_for('home'))
    dept = session.get('department')
    cur = mysql.connection.cursor()
    cur.execute("""SELECT lr.id, lr.user_id, lr.leave_type, lr.start_date, lr.start_session, lr.end_date, lr.end_session, 
                   lr.reason, lr.days, lr.substitute_user_id, lr.substitute_status, lr.hod_status, lr.final_status, 
                   lr.applied_at, u1.name as requester_name, u2.name as substitute_name
                   FROM leave_requests lr 
                   LEFT JOIN users u1 ON lr.user_id = u1.user_id
                   LEFT JOIN users u2 ON lr.substitute_user_id = u2.user_id
                   WHERE lr.department=%s AND lr.substitute_status='Accepted' AND lr.hod_status='Pending'
                   ORDER BY lr.applied_at DESC""", (dept,))
    requests = cur.fetchall()
    cur.close()
    return render_template('hod_dashboard.html', requests=requests, department=dept)

@app.route('/hod/leave_balance')
def hod_leave_balance():
    if 'user_id' not in session or session.get('role') != 'hod':
        return redirect(url_for('home'))

    dept = session.get('department')
    cur = mysql.connection.cursor()
    # Fetch leave balances for all faculty in the department
    cur.execute("""
    SELECT u.name,
           COUNT(lr.id) AS total,
           SUM(lr.final_status='Approved') AS approved,
           SUM(lr.final_status='Rejected') AS rejected,
           SUM(lr.final_status='Pending') AS pending,
           COALESCE(SUM(lr.days),0) AS total_days
    FROM users u
    LEFT JOIN leave_requests lr ON u.user_id=lr.user_id
    WHERE u.department=%s AND u.role='faculty'
    GROUP BY u.user_id, u.name
    ORDER BY u.name
""", (dept,))
    leave_balances = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]

    cur.close()
    return render_template('hod_leavebalance.html', leave_balances=leave_balances, department=dept)


@app.route('/approve_hod/<int:rid>')
def approve_hod(rid):
    if session.get('role') != 'hod':
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE leave_requests SET hod_status='Approved', hod_responded_at=NOW() WHERE id=%s", (rid,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('hod_dashboard'))

@app.route('/reject_hod/<int:rid>')
def reject_hod(rid):
    if session.get('role') != 'hod':
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE leave_requests SET hod_status='Rejected', hod_responded_at=NOW(), final_status='Rejected' WHERE id=%s", (rid,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('hod_dashboard'))

# Admin dashboard - view all
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("""SELECT lr.id, lr.user_id, lr.department, lr.leave_type, lr.start_date, lr.start_session, lr.end_date, lr.end_session, 
                   lr.reason, lr.days, lr.substitute_user_id, lr.substitute_status, lr.hod_status, lr.principal_status, lr.final_status, 
                   lr.applied_at, u1.name as requester_name, u2.name as substitute_name
                   FROM leave_requests lr 
                   LEFT JOIN users u1 ON lr.user_id = u1.user_id
                   LEFT JOIN users u2 ON lr.substitute_user_id = u2.user_id
                   WHERE lr.hod_status='Approved' AND lr.principal_status='Pending'
                   ORDER BY lr.applied_at DESC""", ())
    requests = cur.fetchall()
    cur.close()
    return render_template('admin_dashboard.html', requests=requests)

@app.route('/approve_principal/<int:rid>')
def approve_principal(rid):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE leave_requests SET principal_status='Approved', principal_responded_at=NOW(), final_status='Approved' WHERE id=%s", (rid,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/reject_principal/<int:rid>')
def reject_principal(rid):
    if session.get('role') != 'admin':
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    cur.execute("UPDATE leave_requests SET principal_status='Rejected', principal_responded_at=NOW(), final_status='Rejected' WHERE id=%s", (rid,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
