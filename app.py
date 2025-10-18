from flask import Flask, flash, render_template, request, redirect, url_for, session, jsonify
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

# Inject notification counts into all templates safely
@app.context_processor
def inject_notifications():
    pending_subs = 0
    pending_hod = 0
    pending_principal = 0

    if 'user_id' not in session:
        return dict(
            pending_subs=pending_subs,
            pending_hod=pending_hod,
            pending_principal=pending_principal
        )

    cur = mysql.connection.cursor()
    try:
        role = session.get('role')
        user_id = session.get('user_id')
        dept = session.get('department')

        if role == 'faculty':
            # Substitute requests where current user needs to respond
            cur.execute("""
                SELECT COUNT(*) FROM substitute_requests 
                WHERE requested_user_id=%s AND status='Pending'
            """, (user_id,))
            pending_subs = cur.fetchone()[0] or 0

        elif role == 'hod':
            # Leaves awaiting HOD approval (either substitute accepted or not applicable)
            cur.execute("""
                SELECT COUNT(*) FROM leave_requests 
                WHERE department=%s 
                  AND substitute_status IN ('Accepted', 'Not Applicable') 
                  AND hod_status='Pending'
            """, (dept,))
            pending_hod = cur.fetchone()[0] or 0

        elif role in ('principal', 'admin'):
            # Leaves awaiting principal approval
            cur.execute("""
                SELECT COUNT(*) FROM leave_requests 
                WHERE hod_status='Approved' 
                  AND principal_status='Pending'
            """)
            pending_principal = cur.fetchone()[0] or 0
    finally:
        cur.close()

    return dict(
        pending_subs=pending_subs,
        pending_hod=pending_hod,
        pending_principal=pending_principal
    )

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
    return render_template('index.html', name=name, role=role, info=info, department=dept, active_page='home')

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        user_id = request.form['user_id'].strip()
        password = request.form['password']
        #role = request.form['role']

        if not user_id or not password:
            error = "Please enter both User ID and Password"
        else:
            cur = mysql.connection.cursor()
            cur.execute("SELECT id,user_id,password,role,name,department,email,phone FROM users WHERE user_id=%s AND password=%s",
                        (user_id, password))
            user = cur.fetchone()
            cur.close()
            if user:
                session['user_id'] = user[1]
                session['role'] = user[3]
                session['name'] = user[4]
                session['department'] = user[5]
                session['email'] = user[6]
                session['phone'] = user[7]
                return redirect(url_for('home'))
            error = "Invalid credentials"
    return render_template('login.html', error=error, active_page='login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/apply', methods=['GET','POST'])
def apply():
    if 'user_id' not in session:
        return redirect(url_for('landing'))

    user_id = session['user_id']
    role = session.get('role')
    department = session.get('department')

    all_faculty = []  # always define it

    cur = mysql.connection.cursor()

    # Populate dropdowns
    if role == 'staff':
        # staff → show all faculty/staff except self
        cur.execute("""
            SELECT user_id, name, department FROM users
            WHERE role='staff' AND user_id != %s
            ORDER BY department
        """, (user_id,))
        all_faculty = [{'user_id': row[0], 'name': row[1], 'department': row[2]} for row in cur.fetchall()]

    cur.close()

    if request.method == 'POST':
        leave_type = request.form.get('leave_type', 'Casual')
        start_date = request.form['start_date'] or None
        start_session = request.form.get('start_session', 'Forenoon')
        end_date = request.form['end_date'] or None
        end_session = request.form.get('end_session', 'Afternoon')
        reason = request.form.get('reason','')
        arrangement_details = request.form.get('alternate','')
        try:
            days = int(request.form.get('days') or 1)
        except ValueError:
            days = 1

        substitute_user_id = request.form.get('substitute_user_id') or None

        # Determine substitute_status
        if role == 'staff' or not substitute_user_id:
            sub_status = 'Not Applicable'
            substitute_user_id = None
        else:
            sub_status = 'Pending'

        cur = mysql.connection.cursor()
        try:
            cur.execute("""
                INSERT INTO leave_requests
                (user_id, department, leave_type, start_date, start_session, end_date, end_session,
                 reason, days, substitute_user_id, substitute_status, arrangement_details)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (user_id, department, leave_type, start_date, start_session, end_date, end_session,
                  reason, days, substitute_user_id, sub_status, arrangement_details))

            leave_id = cur.lastrowid

            # Only create substitute request if faculty leave and a substitute is chosen
            if role in ('faculty','hod') and substitute_user_id:
                cur.execute("""
                    INSERT INTO substitute_requests
                    (leave_request_id, requested_user_id, arrangement_details)
                    VALUES (%s,%s,%s)
                """, (leave_id, substitute_user_id, arrangement_details))

            mysql.connection.commit()
        finally:
            cur.close()

        return redirect(url_for('leave_history'))

    return render_template('apply_leave.html', active_page='apply', all_faculty=all_faculty)


@app.route('/leave_history', methods=['GET'])
def leave_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    role = session.get('role')
    department = session.get('department')
    selected_department = request.args.get('department')  # for principal to filter by dept

    cur = mysql.connection.cursor()

    # 1️⃣ Leaves applied by the user (for all roles)
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

    # 2️⃣ Substitute requests assigned to the user (only for faculty/HOD)
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

    # 3️⃣ Department leave history (for HOD)
    department_leaves = []
    if role == 'hod':
        cur.execute("""
            SELECT lr.id, lr.leave_type, lr.start_date, lr.start_session, lr.end_date, lr.end_session, 
                   lr.reason, lr.days, lr.substitute_user_id, lr.substitute_status, lr.hod_status, 
                   lr.principal_status, lr.final_status, lr.applied_at, u1.name as requester_name, 
                   u2.name as substitute_name
            FROM leave_requests lr
            LEFT JOIN users u1 ON lr.user_id = u1.user_id
            LEFT JOIN users u2 ON lr.substitute_user_id = u2.user_id
            WHERE u1.department=%s
            ORDER BY lr.applied_at DESC
        """, (department,))
        department_leaves = cur.fetchall()

    # 4️⃣ Institution leave history (for Principal/Admin)
    institution_leaves = []
    departments = []
    if role in ('admin', 'principal'):
        # Get all departments
        cur.execute("SELECT DISTINCT department FROM users WHERE role='faculty'")
        departments = [d[0] for d in cur.fetchall()]

        query = """
            SELECT lr.id, lr.leave_type, lr.start_date, lr.start_session, lr.end_date, lr.end_session, 
                   lr.reason, lr.days, lr.substitute_user_id, lr.substitute_status, lr.hod_status, 
                   lr.principal_status, lr.final_status, lr.applied_at, u1.name as requester_name, 
                   u1.department, u2.name as substitute_name
            FROM leave_requests lr
            LEFT JOIN users u1 ON lr.user_id = u1.user_id
            LEFT JOIN users u2 ON lr.substitute_user_id = u2.user_id
        """
        params = []
        if selected_department:
            query += " WHERE u1.department=%s"
            params.append(selected_department)
        query += " ORDER BY lr.applied_at DESC"
        cur.execute(query, params)
        institution_leaves = cur.fetchall()

    cur.close()

    return render_template(
        'leave_history.html',
        applied_leaves=applied_leaves,
        substitute_requests=substitute_requests,
        department_leaves=department_leaves,
        institution_leaves=institution_leaves,
        departments=departments,
        selected_department=selected_department,
        active_page='leave_history'
    )

@app.route('/substitute_requests')
def substitute_requests():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    cur = mysql.connection.cursor()
    cur.execute("""SELECT sr.id, lr.id as leave_id, lr.user_id, lr.leave_type, lr.start_date, lr.end_date, 
                   lr.days, lr.reason, lr.arrangement_details, sr.status, sr.responded_at, u.name as requester_name
                   FROM substitute_requests sr
                   JOIN leave_requests lr ON sr.leave_request_id = lr.id
                   JOIN users u ON lr.user_id = u.user_id
                   WHERE sr.requested_user_id=%s AND sr.status='Pending'
                   ORDER BY sr.id DESC LIMIT 10""", (user_id,))
    requests = cur.fetchall()
    cur.close()
    return render_template('substitute_requests.html', requests=requests, active_page='substitute_requests')

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
    return render_template('holiday_calendar.html', holidays=holidays, active_page='holiday_calendar')

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
    return render_template('profile.html', stats=stats, active_page='profile')

@app.route('/change_password', methods=['GET','POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return redirect(url_for('change_password'))

        cur = mysql.connection.cursor()
        cur.execute("SELECT password FROM users WHERE user_id=%s", (session['user_id'],))
        user = cur.fetchone()
        password = user[0] if user else None
        if user and password == current_password:
            cur.execute("UPDATE users SET password=%s WHERE user_id=%s", (new_password, session['user_id']))
            mysql.connection.commit()
            flash("Password changed successfully.", "success")
        else:
            flash("Current password is incorrect.", "error")
        cur.close()
        return redirect(url_for('change_password'))
    return render_template('change_password.html', active_page='change_password')

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
                   WHERE lr.department=%s AND lr.substitute_status IN ('Accepted','Not Applicable') AND lr.hod_status='Pending'
                   ORDER BY lr.applied_at DESC""", (dept,))
    requests = cur.fetchall()
    cur.close()
    return render_template('hod_dashboard.html', requests=requests, department=dept, active_page='hod')

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
    WHERE u.department=%s AND u.role In ('faculty','staff')
    GROUP BY u.user_id, u.name
    ORDER BY u.name
""", (dept,))
    leave_balances = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]

    cur.close()
    return render_template('hod_leavebalance.html', leave_balances=leave_balances, department=dept, active_page='leave_balance')


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
    departments = ['CSE', 'ECE', 'ME']  # dynamically fetch from DB
    selected_department = request.args.get('department', '')
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
    query = "SELECT lr.*, u1.name, u2.name FROM leave_requests lr LEFT JOIN users u1 ON lr.user_id=u1.user_id LEFT JOIN users u2 ON lr.substitute_user_id=u2.user_id"
    params = []
    if selected_department:
        query += " WHERE lr.department=%s"
        params.append(selected_department)
    query += " ORDER BY lr.applied_at DESC"
    cur.execute(query, params)
    institution_leaves = cur.fetchall()
    cur.close()
    return render_template('admin_dashboard.html', requests=requests, institution_leaves=institution_leaves, active_page='admin_dashboard')

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
