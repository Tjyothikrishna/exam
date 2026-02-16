from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify, send_file, make_response
import mysql.connector
import os, json, random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import csv
from io import StringIO
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid
from functools import wraps
from flask import abort


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if session.get('role') != 'admin':
            abort(403)

        return f(*args, **kwargs)
    return decorated_function
# ================= FLASK APP =================

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ================= EMAIL CONFIG =================
EMAIL_USER = "jyothikrishnatunga@gmail.com"
EMAIL_PASS = "atqn sdbk triq nokq"  

# ================= DATABASE =================
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",
        database="website"
    )

# ================= OTP =================
# OTP generation
def generate_otp():
    return random.randint(100000, 999999)

# Email OTP function
def send_otp_email(recipient_email, otp):
    try:
        msg = MIMEText(f'Your OTP for registration is: {otp}')
        msg['Subject'] = 'OTP Verification'
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f'Failed to send OTP email: {e}')
        return False

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# ================= ROUTES =================

@app.route("/")
def index():
    return redirect(url_for("signup"))

# ---------- SIGNUP ----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile_number = request.form['mobile_number']
        password = generate_password_hash(request.form['password'])
        gender = request.form['gender']
        
        profile_pic = request.files.get('profile_pic')
        profile_pic_path = 'static/images/profile_pictures/default_profile.png'

        if profile_pic and allowed_file(profile_pic.filename):
            profile_pic_filename = f"{email}.jpg"
            profile_pic_path = os.path.join(
                'static/images/profile_pictures',
                profile_pic_filename
            )
            profile_pic.save(profile_pic_path)

        otp = generate_otp()
        if send_otp_email(email, otp):
            session['otp'] = otp
            session['signup_data'] = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'mobile_number': mobile_number,
                'password': password,
                'gender': gender,
                'profile_pic_path': profile_pic_path   # ✅ STORE IT
            }
            flash(
                'OTP sent to your email. Please enter the OTP to complete registration.',
                'info'
            )
            return redirect(url_for('verify_otp'))
        else:
            flash('Failed to send OTP. Please try again.', 'danger')

    return render_template('signup.html')
# ---------- VERIFY OTP ----------
@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        otp = request.form['otp']

        if 'otp' in session and otp == str(session['otp']):
            signup_data = session.pop('signup_data')

            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users
                    (first_name, last_name, email, mobile_number,
                     password_hash, gender, profile_picture, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'student')
                """, (
                    signup_data['first_name'],
                    signup_data['last_name'],
                    signup_data['email'],
                    signup_data['mobile_number'],
                    signup_data['password'],
                    signup_data['gender'],
                    signup_data['profile_pic_path']   # ✅ FIX
                ))

                conn.commit()
                flash('You have successfully signed up!', 'success')
                return redirect(url_for('login'))

            except mysql.connector.IntegrityError:
                flash('Email or mobile number already exists.', 'danger')

            finally:
                cursor.close()
                conn.close()
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_otp.html')


# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        # ---- FIXED + CLEAN LOGIN LOGIC ----
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['first_name']
            session['role'] = user['role']

            print("LOGIN USER ID:", user['id'])  # DEBUG

            # ✅ Correct redirection
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('home'))

        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

# ---- NEW REDIRECTION LOGIC (ONLY THIS PART CHANGED) ----
#if user['role'] == 'admin':
#    return redirect(url_for('admin_dashboard'))
#else:
#    return redirect(url_for('home'))
#
#        else:
#            flash('Invalid email or password', 'danger')

# ---------- ADMIN HOME ----------
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---- TOTAL STUDENTS ----
    cursor.execute("""
        SELECT COUNT(*) AS total_students
        FROM users
        WHERE role = 'student'
    """)
    total_students = cursor.fetchone()['total_students']

    # ---- TOTAL TEST ATTEMPTS ----
    cursor.execute("""
        SELECT COUNT(*) AS total_attempts
        FROM test_attempts
    """)
    total_attempts = cursor.fetchone()['total_attempts']

    # ---- RECENT ATTEMPTS (for table) ----
    cursor.execute("""
        SELECT 
            ta.id,
            u.first_name, 
            qs.title, 
            ta.score, 
            ta.percentage, 
            ta.attempted_at
        FROM test_attempts ta
        JOIN users u ON ta.user_id = u.id
        JOIN question_sets qs ON ta.question_set_id = qs.id
        ORDER BY ta.attempted_at DESC
        LIMIT 10
    """)
    recent_attempts = cursor.fetchall()

    # ---- BAR CHART: ATTEMPTS PER STUDENT ----
    cursor.execute("""
        SELECT 
            u.first_name,
            COUNT(ta.id) AS attempts
        FROM users u
        LEFT JOIN test_attempts ta 
            ON u.id = ta.user_id
        WHERE u.role = 'student'
        GROUP BY u.id
        ORDER BY attempts DESC
        LIMIT 8
    """)
    chart_data = cursor.fetchall()

    student_names = [row['first_name'] for row in chart_data]
    attempt_counts = [row['attempts'] for row in chart_data]

    # ---- PIE CHART: PASS vs FAIL ----
    cursor.execute("""
        SELECT 
            SUM(passed = 1) AS passed,
            SUM(passed = 0) AS failed
        FROM test_attempts
    """)
    pass_fail = cursor.fetchone()

    passed_count = pass_fail['passed'] or 0
    failed_count = pass_fail['failed'] or 0

    # ---- LINE CHART: DAILY ATTEMPT TREND ----
    cursor.execute("""
        SELECT 
            DATE(attempted_at) AS day,
            COUNT(*) AS attempts
        FROM test_attempts
        GROUP BY DATE(attempted_at)
        ORDER BY day DESC
        LIMIT 7
    """)
    trend_data = cursor.fetchall()

    attempt_days = [str(row['day']) for row in trend_data][::-1]
    attempt_trend = [row['attempts'] for row in trend_data][::-1]

    cursor.close()
    conn.close()

    return render_template(
        'admin/dashboard.html',
        total_students=total_students,
        total_attempts=total_attempts,
        recent_attempts=recent_attempts,
        student_names=student_names,
        attempt_counts=attempt_counts,
        passed_count=passed_count,
        failed_count=failed_count,
        attempt_days=attempt_days,
        attempt_trend=attempt_trend
    )

@app.route('/admin/download_attempts_csv')
@admin_required
def download_attempts_csv():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            ta.id,
            u.first_name,
            qs.title,
            ta.score,
            ta.percentage,
            ta.attempted_at
        FROM test_attempts ta
        JOIN users u ON ta.user_id = u.id
        JOIN question_sets qs ON ta.question_set_id = qs.id
        ORDER BY ta.attempted_at DESC
    """)

    rows = cursor.fetchall()

    output = []
    output.append(["Student", "Test", "Score", "Percentage", "Date"])

    for r in rows:
        output.append([
            r['first_name'],
            r['title'],
            r['score'],
            r['percentage'],
            r['attempted_at']
        ])

    cursor.close()
    conn.close()

    # Convert to CSV string
    import csv
    from io import StringIO

    si = StringIO()
    writer = csv.writer(si)
    writer.writerows(output)

    response = make_response(si.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=attempts.csv"
    response.headers["Content-Type"] = "text/csv"

    return response

# ---------- HOME ----------
@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ---------------- USER DETAILS ----------------
    cursor.execute("""
        SELECT id, first_name, last_name, email, mobile_number,
               gender, profile_picture, role
        FROM users
        WHERE id = %s
    """, (user_id,))
    user = cursor.fetchone()

    if user['role'] != 'student':
        return redirect(url_for('login'))

    # ---------------- TOTAL ATTEMPTS ----------------
    cursor.execute("""
        SELECT COUNT(*) AS total_attempts
        FROM test_attempts
        WHERE user_id = %s
    """, (user_id,))
    total_attempts = cursor.fetchone()['total_attempts']

    # ---------------- LAST ATTEMPT ----------------
    cursor.execute("""
        SELECT
            ta.score,
            ta.total_questions,
            ta.percentage,
            ta.passed,
            ta.attempted_at,
            qs.title AS test_name
        FROM test_attempts ta
        JOIN question_sets qs ON ta.question_set_id = qs.id
        WHERE ta.user_id = %s
        ORDER BY ta.attempted_at DESC
        LIMIT 1
    """, (user_id,))
    last_attempt = cursor.fetchone()

    # ---------------- PERFORMANCE TREND ----------------
    cursor.execute("""
        SELECT score
        FROM test_attempts
        WHERE user_id = %s
        ORDER BY attempted_at DESC
        LIMIT 2
    """, (user_id,))
    scores = cursor.fetchall()

    performance_trend = None
    if len(scores) == 2:
        if scores[0]['score'] > scores[1]['score']:
            performance_trend = 'Improved'
        elif scores[0]['score'] < scores[1]['score']:
            performance_trend = 'Declined'
        else:
            performance_trend = 'Same'

    # ---------------- AVERAGE SCORE ----------------
    cursor.execute("""
        SELECT ROUND(AVG(percentage), 2) AS avg_percentage
        FROM test_attempts
        WHERE user_id = %s
    """, (user_id,))
    avg_percentage = cursor.fetchone()['avg_percentage']

    cursor.close()
    conn.close()

    return render_template(
        'home.html',
        user=user,
        total_attempts=total_attempts,
        last_attempt=last_attempt,
        performance_trend=performance_trend,
        avg_percentage=avg_percentage
    )

@app.route('/admin/students')
@admin_required
def admin_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.id, u.first_name, u.email,
               COUNT(ta.id) AS attempts,
               ROUND(AVG(ta.percentage),2) AS avg_score
        FROM users u
        LEFT JOIN test_attempts ta ON u.id = ta.user_id
        WHERE u.role = 'student'
        GROUP BY u.id
    """)

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/students.html', students=students)

@app.route('/admin/student/<int:user_id>')
@admin_required
def admin_student_detail(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    student = cursor.fetchone()

    cursor.execute("""
        SELECT qs.title, ta.score, ta.total_questions,
               ta.percentage, ta.passed, ta.attempted_at
        FROM test_attempts ta
        JOIN question_sets qs ON ta.question_set_id = qs.id
        WHERE ta.user_id = %s
        ORDER BY ta.attempted_at DESC
    """, (user_id,))
    attempts = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'admin/student_detail.html',
        student=student,
        attempts=attempts
    )

@app.route('/admin/attempt/<int:attempt_id>')
@admin_required
def admin_attempt_detail(attempt_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # --------- GET ATTEMPT + STUDENT + TEST NAME ----------
    cursor.execute("""
        SELECT 
            ta.id AS attempt_id,
            ta.score,
            ta.total_questions,
            ta.percentage,
            ta.passed,
            ta.attempted_at,
            u.id AS user_id,
            u.first_name,
            u.last_name,
            qs.title AS test_name
        FROM test_attempts ta
        JOIN users u ON ta.user_id = u.id
        JOIN question_sets qs ON ta.question_set_id = qs.id
        WHERE ta.id = %s
    """, (attempt_id,))

    attempt = cursor.fetchone()

    # 🔴 IMPORTANT SAFETY CHECK
    if not attempt:
        flash("Attempt not found.", "danger")
        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))

    # --------- GET QUESTION-WISE ANSWERS ----------
    cursor.execute("""
        SELECT 
            q.id AS question_id,
            q.question_text,
            o1.option_text AS selected_option,
            o2.option_text AS correct_option,
            sa.is_correct
        FROM student_answers sa
        JOIN questions q ON sa.question_id = q.id
        JOIN options o1 ON sa.selected_option_id = o1.id
        JOIN options o2 
            ON o2.question_id = q.id AND o2.is_correct = 1
        WHERE sa.test_attempt_id = %s
        ORDER BY q.id
    """, (attempt_id,))

    answers = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'admin/attempt_detail.html',
        attempt=attempt,
        answers=answers
    )


@app.route('/admin/question_sets', methods=['GET', 'POST'])
@admin_required
def admin_question_sets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        admin_id = session['user_id']

        cursor.execute("""
            INSERT INTO question_sets (title, description, created_by)
            VALUES (%s, %s, %s)
        """, (title, description, admin_id))
        conn.commit()

        flash('Question set created successfully!', 'success')

    cursor.execute("SELECT * FROM question_sets ORDER BY created_at DESC")
    sets = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin/question_sets.html', sets=sets)

@app.route('/admin/question_set/<int:set_id>/add', methods=['GET', 'POST'])
@admin_required
def admin_add_question(set_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        question_text = request.form['question_text']
        correct_index = int(request.form['correct'])

        cursor.execute("""
            INSERT INTO questions (question_set_id, question_text)
            VALUES (%s, %s)
        """, (set_id, question_text))
        question_id = cursor.lastrowid

        options = request.form.getlist('options[]')

        for i, opt in enumerate(options):
            cursor.execute("""
                INSERT INTO options (question_id, option_text, is_correct)
                VALUES (%s, %s, %s)
            """, (question_id, opt, i == correct_index))

        conn.commit()
        flash('Question added successfully!', 'success')

    cursor.execute("SELECT * FROM question_sets WHERE id = %s", (set_id,))
    qset = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template('admin/add_question.html', qset=qset)


# ---------- FORGOT PASSWORD ----------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            otp = generate_otp()
            if send_otp_email(email, otp):
                session['otp'] = otp
                session['email'] = email
                flash('OTP sent to your email. Please enter the OTP to reset your password.', 'info')
                return redirect(url_for('reset_password'))
            else:
                flash('Failed to send OTP. Please try again.', 'danger')
        else:
            flash('Email not registered. Please sign up.', 'danger')

    return render_template('forgot_password.html')

# ---------- RESET PASSWORD ----------
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        otp = request.form['otp']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # OTP validation
        if 'otp' in session and otp == str(session['otp']):

            if new_password != confirm_password:
                flash('Passwords do not match. Please try again.', 'danger')
                return redirect(url_for('reset_password'))

            # 🔐 HASH PASSWORD (IMPORTANT)
            hashed_password = generate_password_hash(new_password)

            email = session['email']
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                'UPDATE users SET password_hash = %s WHERE email = %s',
                (hashed_password, email)
            )

            conn.commit()
            cursor.close()
            conn.close()

            # cleanup session
            session.pop('otp', None)
            session.pop('email', None)

            flash('Password updated successfully! Please log in.', 'success')
            return redirect(url_for('login'))

        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('reset_password.html')

#-------------------RANDOM QUESTION SET LOADER-----------------
def load_random_question_set():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # pick random question set
    cursor.execute("""
        SELECT id, title
        FROM question_sets
        ORDER BY RAND()
        LIMIT 1
    """)
    question_set = cursor.fetchone()

    # fetch questions
    cursor.execute("""
        SELECT id, question_text
        FROM questions
        WHERE question_set_id = %s
    """, (question_set['id'],))
    questions = cursor.fetchall()

    # fetch options for each question
    for q in questions:
        cursor.execute("""
            SELECT id, option_text, is_correct
            FROM options
            WHERE question_id = %s
        """, (q['id'],))
        q['options'] = cursor.fetchall()

        # store correct option ID
        q['correct_option_id'] = next(
            o['id'] for o in q['options'] if o['is_correct']
        )

    cursor.close()
    conn.close()

    random.shuffle(questions)
    return questions, question_set['id']


# ---------- TEST ----------
@app.route('/test')
def test():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    questions, question_set_id = load_random_question_set()

    # 🔴 IMPORTANT SAFETY CHECK
    if not questions or not question_set_id:
        flash("No question sets available. Ask admin to create one.", "danger")
        return redirect(url_for('home'))

    session['questions'] = questions
    session['question_set_id'] = question_set_id
    session['current_index'] = 0
    session['score'] = 0
    session['answers'] = []

    return redirect(url_for('question'))


# ---------- QUESTIONS ----------

@app.route('/question', methods=['GET', 'POST'])
def question():
    if 'questions' not in session:
        return redirect(url_for('home'))

    index = session.get('current_index', 0)
    questions = session['questions']

    if index >= len(questions):
        return redirect(url_for('test_result'))

    question = questions[index]

    if request.method == 'POST':
        selected_option_id = int(request.form.get('option'))

        is_correct = selected_option_id == question['correct_option_id']
        if is_correct:
            session['score'] += 1

        session['answers'].append({
            'question_id': question['id'],
            'selected_option_id': selected_option_id,
            'is_correct': is_correct
        })

        session['current_index'] += 1
        return redirect(url_for('question'))

    return render_template(
        'question.html',
        question=question,
        index=index + 1,
        total=len(questions)
    )

# ---------- TEST RESULT ----------
@app.route('/test_result')
def test_result():
    if 'questions' not in session:
        return redirect(url_for('home'))

    total = len(session['questions'])
    score = session.get('score', 0)
    percentage = round((score / total) * 100, 2)

    return render_template(
        'test_result.html',
        score=score,
        total=total,
        percentage=percentage
    )

# ---------- SUBMIT TEST ----------
@app.route('/submit_test', methods=['POST'])
def submit_test():
    if 'user_id' not in session or 'questions' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    questions = session.get('questions', [])
    answers = session.get('answers', [])
    question_set_id = session.get('question_set_id')

    score = session.get('score', 0)
    total_questions = len(questions)
    percentage = round((score / total_questions) * 100, 2)
    passed = percentage >= 70

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO test_attempts
        (user_id, question_set_id, score, total_questions, percentage, passed)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, question_set_id, score, total_questions, percentage, passed))

    attempt_id = cursor.lastrowid

    for ans in answers:
        cursor.execute("""
            INSERT INTO student_answers
            (test_attempt_id, question_id, selected_option_id, is_correct)
            VALUES (%s, %s, %s, %s)
        """, (
            attempt_id,
            ans['question_id'],
            ans['selected_option_id'],
            ans['is_correct']
        ))

    conn.commit()
    cursor.close()
    conn.close()

    session.pop('questions', None)
    session.pop('answers', None)
    session.pop('score', None)
    session.pop('current_index', None)
    session.pop('question_set_id', None)

    return redirect(url_for('home'))


# ---------- ABOUT ----------
@app.route('/about')
def about():
    return render_template('about.html')

# ---------- HELP ----------
@app.route('/help', methods=['GET', 'POST'])
def help():
    if request.method == 'POST':
        #  Read data from form
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        subject = request.form.get('subject')
        message = request.form.get('content')

        # Basic validation
        if not all([name, email, phone, subject, message]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('help'))

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            #  Save to database
            cursor.execute("""
                INSERT INTO help_requests
                (name, email, phone_number, subject, content)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, phone, subject, message))
            conn.commit()

            #  Send email to admin
            email_body = f"""
            New Help Request

            Name: {name}
            Email: {email}
            Phone: {phone}

            Message:
            {message}
            """

            msg = MIMEText(email_body)
            msg['Subject'] = subject
            msg['From'] = EMAIL_USER
            msg['To'] = 'support@vstand4usolutions.com'

            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)

            flash('Your message has been sent successfully.', 'success')

        except Exception as e:
            conn.rollback()
            flash(f'Something went wrong: {e}', 'danger')

        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('help'))

    # GET request
    return render_template('help.html')

# ---------- SETTINGS ----------

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        mobile = request.form['mobile']
        college = request.form['college']
        qualification = request.form['qualification']
        gender = request.form['gender']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET first_name = %s, last_name = %s, email = %s, mobile_number = %s, gender = %s 
                WHERE id = %s
            ''', (first_name, last_name, email, mobile, gender, user_id))
            conn.commit()

            profile_pic = request.files.get('profile_pic')
            if profile_pic:
                if allowed_file(profile_pic.filename):
                    profile_pic_path = os.path.join('static/images/profile_pictures', f'{email}.jpg')
                    profile_pic.save(profile_pic_path)
                    cursor.execute('UPDATE users SET profile_picture = %s WHERE id = %s', (profile_pic_path, user_id))
                    conn.commit()
                else:
                    flash('Invalid file type. Only PNG, JPG, JPEG, and GIF files are allowed.', 'danger')

            flash('Settings updated successfully.', 'success')
        except mysql.connector.Error as e:
            flash('Error updating settings: ' + str(e), 'danger')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('settings'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('settings.html', user=user, user_name=session.get('user_name'))

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
