from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import date
import os

from db import get_connection, init_db

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

UPLOAD_FOLDER = os.path.join('static', 'uploads')
PHOTO_FOLDER  = os.path.join('static', 'uploads', 'photos')
VIDEO_FOLDER  = os.path.join('static', 'uploads', 'videos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PHOTO_FOLDER,  exist_ok=True)
os.makedirs(VIDEO_FOLDER,  exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

ALLOWED_VIDEO = {'mp4', 'mov', 'avi', 'mkv'}
ALLOWED_PDF   = {'pdf'}
ALLOWED_IMG   = {'jpg', 'jpeg', 'png', 'gif', 'webp'}

def allowed(filename, exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in exts

# ── DECORATORS ──────────────────────────────
def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user_id' not in session:
            flash('Please login first.', 'error')
            return redirect(url_for('login'))
        return f(*a, **kw)
    return dec

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def dec(*a, **kw):
            if session.get('role') not in roles:
                flash('Access denied.', 'error')
                return redirect(url_for('login'))
            return f(*a, **kw)
        return dec
    return wrapper

# ── HOME ────────────────────────────────────
@app.route('/')
def index():
    # If already logged in, go to their dashboard
    if 'user_id' in session:
        r = session.get('role')
        if r == 'admin':   return redirect(url_for('admin_dashboard'))
        if r == 'staff':   return redirect(url_for('staff_dashboard'))
        if r == 'student': return redirect(url_for('student_dashboard'))
    # Show the public home / landing page
    return render_template('home.html')

# ══════════════════════════════════════════
#  AUTH
# ══════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        conn     = get_connection(); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone(); cursor.close(); conn.close()
        if user and check_password_hash(user['password'], password):
            session.update({'user_id':user['id'],'name':user['name'],
                            'email':user['email'],'role':user['role'],
                            'photo':user.get('photo','')})
            flash(f"Welcome back, {user['name']}!", 'success')
            return redirect(url_for(user['role'] + '_dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role    = request.form.get('role')
        name    = request.form.get('name','').strip()
        email   = request.form.get('email','').strip()
        mobile  = request.form.get('mobile','')
        dob     = request.form.get('dob','') or None
        pwd     = request.form.get('password','')
        confirm = request.form.get('confirm_password','')
        if pwd != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        # Handle photo upload
        photo_url = ''
        photo_f = request.files.get('photo')
        if photo_f and photo_f.filename and allowed(photo_f.filename, ALLOWED_IMG):
            fn = secure_filename(photo_f.filename)
            photo_f.save(os.path.join(PHOTO_FOLDER, fn))
            photo_url = f'/static/uploads/photos/{fn}'
        hashed = generate_password_hash(pwd)
        conn = get_connection(); cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name,email,password,role,mobile,dob,photo) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (name, email, hashed, role, mobile, dob, photo_url or None)
            )
            uid = cursor.lastrowid
            if role == 'student':
                cursor.execute(
                    "INSERT INTO students (user_id,roll_no,course,year,semester,college,department) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (uid, request.form.get('roll_no'), request.form.get('course'),
                     request.form.get('year'), request.form.get('semester'),
                     request.form.get('college'), request.form.get('department',''))
                )
            elif role == 'staff':
                cursor.execute(
                    "INSERT INTO staff (user_id,staff_id,department,designation,experience,qualification) VALUES (%s,%s,%s,%s,%s,%s)",
                    (uid, request.form.get('staff_id'), request.form.get('department'),
                     request.form.get('designation'), request.form.get('experience'),
                     request.form.get('qualification'))
                )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback(); flash(f'Registration failed: {e}', 'error')
        finally:
            cursor.close(); conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ── UPLOAD PROFILE PHOTO ─────────────────────
@app.route('/upload_photo', methods=['POST'])
@login_required
def upload_photo():
    photo_f = request.files.get('photo')
    if photo_f and photo_f.filename and allowed(photo_f.filename, ALLOWED_IMG):
        fn = secure_filename(photo_f.filename)
        photo_f.save(os.path.join(PHOTO_FOLDER, fn))
        photo_url = f'/static/uploads/photos/{fn}'
        conn = get_connection(); cursor = conn.cursor()
        cursor.execute("UPDATE users SET photo=%s WHERE id=%s", (photo_url, session['user_id']))
        conn.commit(); cursor.close(); conn.close()
        session['photo'] = photo_url
        flash('Profile photo updated! 📸', 'success')
    else:
        flash('Please upload a valid image (JPG/PNG/GIF/WEBP).', 'error')
    return redirect(request.referrer or url_for('student_dashboard'))

# ══════════════════════════════════════════
#  ADMIN MODULE
# ══════════════════════════════════════════
@app.route('/admin_dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS c FROM users WHERE role='student'"); students = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM users WHERE role='staff'");   staff    = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM courses");                    courses  = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM videos");                     videos   = cursor.fetchone()['c']
    cursor.close(); conn.close()
    return render_template('admin/admin_dashboard.html',
                           students=students, staff=staff, courses=courses, videos=videos)

@app.route('/manage_students')
@login_required
@role_required('admin')
def manage_students():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id,u.name,u.email,u.mobile,u.created_at,u.photo,
               s.roll_no,s.department,s.course,s.year
        FROM users u LEFT JOIN students s ON u.id=s.user_id
        WHERE u.role='student' ORDER BY u.id DESC
    """)
    students = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('admin/manage_students.html', students=students)

@app.route('/delete_student/<int:uid>')
@login_required
@role_required('admin')
def delete_student(uid):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s AND role='student'", (uid,))
    conn.commit(); cursor.close(); conn.close()
    flash('Student deleted successfully.', 'success')
    return redirect(url_for('manage_students'))

@app.route('/manage_staff')
@login_required
@role_required('admin')
def manage_staff():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id,u.name,u.email,u.mobile,u.created_at,u.photo,
               s.staff_id,s.department,s.designation
        FROM users u LEFT JOIN staff s ON u.id=s.user_id
        WHERE u.role='staff' ORDER BY u.id DESC
    """)
    staff = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('admin/manage_staff.html', staff=staff)

@app.route('/delete_staff/<int:uid>')
@login_required
@role_required('admin')
def delete_staff(uid):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s AND role='staff'", (uid,))
    conn.commit(); cursor.close(); conn.close()
    flash('Staff member deleted successfully.', 'success')
    return redirect(url_for('manage_staff'))

@app.route('/manage_courses', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_courses():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        title      = request.form.get('title','').strip()
        desc       = request.form.get('description','').strip()
        department = request.form.get('department','').strip()
        if not title:
            flash('Course title required!', 'error')
            return redirect(url_for('manage_courses'))
        try:
            cursor.execute(
                "INSERT INTO courses (title,description,department,created_by) VALUES (%s,%s,%s,%s)",
                (title, desc, department, session['user_id'])
            )
            conn.commit(); flash('Course created!', 'success')
        except Exception as e:
            conn.rollback(); flash(f'Failed: {e}', 'error')
        finally: cursor.close(); conn.close()
        return redirect(url_for('manage_courses'))
    cursor.execute("""
        SELECT c.*,u.name AS created_by_name FROM courses c
        LEFT JOIN users u ON c.created_by=u.id ORDER BY c.id DESC
    """)
    courses = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('admin/manage_courses.html', courses=courses)

@app.route('/edit_course/<int:cid>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_course(cid):
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        desc  = request.form.get('description','').strip()
        dept  = request.form.get('department','').strip()
        if not title:
            flash('Course title required!', 'error')
            return redirect(url_for('edit_course', cid=cid))
        try:
            cursor.execute(
                "UPDATE courses SET title=%s,description=%s,department=%s WHERE id=%s",
                (title, desc, dept, cid)
            )
            conn.commit(); flash('Course updated!', 'success')
        except Exception as e:
            conn.rollback(); flash(f'Failed: {e}', 'error')
        finally: cursor.close(); conn.close()
        return redirect(url_for('manage_courses'))
    cursor.execute("SELECT * FROM courses WHERE id=%s", (cid,))
    course = cursor.fetchone(); cursor.close(); conn.close()
    if not course:
        flash('Course not found!', 'error')
        return redirect(url_for('manage_courses'))
    return render_template('admin/edit_course.html', course=course)

@app.route('/delete_course/<int:cid>')
@login_required
@role_required('admin')
def delete_course(cid):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS c FROM enrollments WHERE course_id=%s", (cid,))
    enrollments = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) AS c FROM videos WHERE course_id=%s", (cid,))
    videos = cursor.fetchone()[0]
    if enrollments > 0 or videos > 0:
        flash(f'Cannot delete: {enrollments} enrollments, {videos} videos exist. Delete them first!', 'warning')
        cursor.close(); conn.close()
        return redirect(url_for('manage_courses'))
    try:
        cursor.execute("DELETE FROM courses WHERE id=%s", (cid,))
        conn.commit(); flash('Course deleted!', 'success')
    except Exception as e:
        conn.rollback(); flash(f'Failed: {e}', 'error')
    finally: cursor.close(); conn.close()
    return redirect(url_for('manage_courses'))

# ── ADMIN: VIDEO MANAGEMENT ──────────────────
@app.route('/admin_videos')
@login_required
@role_required('admin')
def admin_videos():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT v.*,c.title AS course_title,u.name AS uploader
        FROM videos v
        JOIN courses c ON v.course_id=c.id
        JOIN users   u ON v.uploaded_by=u.id
        ORDER BY v.id DESC
    """)
    videos = cursor.fetchall()
    cursor.execute("SELECT id,title FROM courses ORDER BY title")
    courses = cursor.fetchall()
    cursor.close(); conn.close()
    return render_template('admin/manage_videos.html', videos=videos, courses=courses)

@app.route('/admin_edit_video/<int:vid>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_video(vid):
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        title       = request.form.get('title','').strip()
        description = request.form.get('description','').strip()
        duration    = request.form.get('duration','').strip()
        course_id   = request.form.get('course_id','').strip()
        video_url   = request.form.get('video_url','').strip()
        # Handle new file upload
        vf = request.files.get('video_file')
        if vf and vf.filename and allowed(vf.filename, ALLOWED_VIDEO):
            fn = secure_filename(vf.filename)
            vf.save(os.path.join(VIDEO_FOLDER, fn))
            video_url = f'/static/uploads/videos/{fn}'
        try:
            cursor.execute(
                "UPDATE videos SET title=%s,description=%s,duration=%s,course_id=%s,video_url=%s WHERE id=%s",
                (title, description, duration, course_id, video_url, vid)
            )
            conn.commit(); flash('Video updated successfully! ✅', 'success')
        except Exception as e:
            conn.rollback(); flash(f'Update failed: {e}', 'error')
        finally: cursor.close(); conn.close()
        return redirect(url_for('admin_videos'))
    cursor.execute("SELECT * FROM videos WHERE id=%s", (vid,)); video = cursor.fetchone()
    cursor.execute("SELECT id,title FROM courses ORDER BY title"); courses = cursor.fetchall()
    cursor.close(); conn.close()
    if not video:
        flash('Video not found!', 'error'); return redirect(url_for('admin_videos'))
    return render_template('admin/edit_video.html', video=video, courses=courses)

@app.route('/admin_delete_video/<int:vid>')
@login_required
@role_required('admin')
def admin_delete_video(vid):
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("DELETE FROM videos WHERE id=%s", (vid,))
    conn.commit(); cursor.close(); conn.close()
    flash('Video deleted! 🗑️', 'success')
    return redirect(url_for('admin_videos'))

@app.route('/analytics')
@login_required
@role_required('admin')
def analytics():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS c FROM users WHERE role='student'"); students    = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM users WHERE role='staff'");   staff       = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM courses");                    courses     = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM enrollments");                enrollments = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM videos");                     videos      = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM quiz_results");               quizzes     = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM certificates");               certs       = cursor.fetchone()['c']
    cursor.close(); conn.close()
    return render_template('admin/analytics.html',
                           students=students, staff=staff, courses=courses,
                           enrollments=enrollments, videos=videos, quizzes=quizzes, certs=certs)

# ══════════════════════════════════════════
#  STAFF MODULE
# ══════════════════════════════════════════
@app.route('/staff_dashboard')
@login_required
@role_required('staff')
def staff_dashboard():
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.id,c.title,COUNT(e.id) AS enrolled
        FROM courses c LEFT JOIN enrollments e ON c.id=e.course_id
        WHERE c.created_by=%s GROUP BY c.id,c.title ORDER BY c.id DESC
    """, (uid,))
    courses = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) AS c FROM courses WHERE created_by=%s", (uid,)); my_courses     = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM videos WHERE uploaded_by=%s", (uid,)); my_videos      = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM users WHERE role='student'");           total_students = cursor.fetchone()['c']
    cursor.close(); conn.close()
    return render_template('staff/staff_dashboard.html',
                           courses=courses, my_courses=my_courses,
                           my_videos=my_videos, total_students=total_students)

@app.route('/add_course', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def add_course():
    if request.method == 'POST':
        title     = request.form.get('title','').strip()
        desc      = request.form.get('description','').strip()
        dept      = request.form.get('department','').strip()
        video_url = request.form.get('video_url','').strip()
        uid       = session['user_id']
        if not title:
            flash('Course title required!', 'error')
            return redirect(url_for('add_course'))
        notes_url = ''
        pdf_f = request.files.get('notes_file')
        if pdf_f and pdf_f.filename and allowed(pdf_f.filename, ALLOWED_PDF):
            fn = secure_filename(pdf_f.filename)
            pdf_f.save(os.path.join(UPLOAD_FOLDER, fn))
            notes_url = f'/static/uploads/{fn}'
        conn = get_connection(); cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO courses (title,description,department,video_url,notes_url,created_by) VALUES (%s,%s,%s,%s,%s,%s)",
                (title, desc, dept, video_url or None, notes_url or None, uid)
            )
            conn.commit(); flash('Course created! 🎉', 'success')
            return redirect(url_for('add_course'))
        except Exception as e:
            conn.rollback(); flash(f'Failed: {e}', 'error')
        finally: cursor.close(); conn.close()
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE created_by=%s ORDER BY id DESC", (session['user_id'],))
    courses = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('staff/add_course.html', courses=courses)

@app.route('/manage_quiz', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def manage_quiz():
    uid       = session['user_id']
    course_id = request.args.get('course_id','')
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE created_by=%s", (uid,)); my_courses = cursor.fetchall()
    questions = []
    if course_id:
        cursor.execute("SELECT * FROM quiz WHERE course_id=%s ORDER BY id DESC", (course_id,))
        questions = cursor.fetchall()
    cursor.close(); conn.close()
    if request.method == 'POST':
        course_id = request.form.get('course_id','').strip()
        q = request.form.get('question','').strip()
        o1,o2,o3,o4 = [request.form.get(f'option{i}','').strip() for i in range(1,5)]
        correct = request.form.get('correct','').strip()
        if not all([course_id, q, o1, o2, o3, o4, correct]):
            flash('All fields required!', 'error')
            return redirect(url_for('manage_quiz', course_id=course_id))
        conn = get_connection(); cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO quiz (course_id,question,option1,option2,option3,option4,correct) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (int(course_id), q, o1, o2, o3, o4, correct)
            )
            conn.commit(); flash('Question added!', 'success')
            return redirect(url_for('manage_quiz', course_id=course_id))
        except Exception as e:
            conn.rollback(); flash(f'Failed: {e}', 'error')
        finally: cursor.close(); conn.close()
    return render_template('staff/manage_quiz.html',
                           my_courses=my_courses, questions=questions, course_id=course_id)

@app.route('/delete_question/<int:qid>')
@login_required
@role_required('staff')
def delete_question(qid):
    course_id = request.args.get('course_id','')
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("DELETE FROM quiz WHERE id=%s", (qid,))
    conn.commit(); cursor.close(); conn.close()
    flash('Question deleted!', 'success')
    return redirect(url_for('manage_quiz', course_id=course_id))

@app.route('/view_students')
@login_required
@role_required('staff')
def view_students():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id,u.name,u.email,u.mobile,u.photo,s.roll_no,s.course,s.year,s.department
        FROM users u LEFT JOIN students s ON u.id=s.user_id
        WHERE u.role='student' ORDER BY u.id DESC
    """)
    students = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('staff/view_students.html', students=students)

@app.route('/mark_attendance', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def mark_attendance():
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE created_by=%s", (uid,)); courses = cursor.fetchall()
    cursor.close(); conn.close()
    attendance = []
    if request.method == 'POST':
        course_id = request.form.get('course_id','').strip()
        if not course_id:
            flash('Please select a course!', 'error')
            return redirect(url_for('mark_attendance'))
        conn = get_connection(); cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.id,u.name,e.student_id FROM enrollments e
            JOIN users u ON e.student_id=u.id WHERE e.course_id=%s
        """, (int(course_id),))
        attendance = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('staff/mark_attendance.html', courses=courses, attendance=attendance)

@app.route('/save_attendance', methods=['POST'])
@login_required
@role_required('staff')
def save_attendance():
    course_id = request.form.get('course_id','').strip()
    if not course_id:
        flash('Invalid course!', 'error')
        return redirect(url_for('mark_attendance'))
    conn = get_connection(); cursor = conn.cursor()
    for k, v in request.form.items():
        if k.startswith('attendance_'):
            sid = k.replace('attendance_', '')
            cursor.execute(
                "INSERT IGNORE INTO attendance (student_id,course_id,date,status,marked_by) VALUES (%s,%s,%s,%s,%s)",
                (sid, int(course_id), str(date.today()), v, session['user_id'])
            )
    conn.commit(); cursor.close(); conn.close()
    flash('Attendance saved! ✅', 'success')
    return redirect(url_for('mark_attendance'))

# ── UPLOAD VIDEO ─────────────────────────────
@app.route('/upload_video', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def upload_video():
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id,title FROM courses WHERE created_by=%s", (uid,)); courses = cursor.fetchall()
    if request.method == 'POST':
        course_id   = request.form.get('course_id','').strip()
        title       = request.form.get('title','').strip()
        description = request.form.get('description','').strip()
        duration    = request.form.get('duration','').strip()
        youtube_url = request.form.get('video_url','').strip()
        if not course_id: flash('Select a course!', 'error'); return redirect(url_for('upload_video'))
        if not title:     flash('Video title required!', 'error'); return redirect(url_for('upload_video'))
        video_url = ''
        vf = request.files.get('video_file')
        if vf and vf.filename and allowed(vf.filename, ALLOWED_VIDEO):
            fn = secure_filename(vf.filename)
            vf.save(os.path.join(VIDEO_FOLDER, fn))
            video_url = f'/static/uploads/videos/{fn}'
        elif youtube_url:
            video_url = youtube_url
        else:
            flash('Upload a video file OR paste a YouTube URL!', 'error')
            return redirect(url_for('upload_video'))
        conn2 = get_connection(); cur2 = conn2.cursor()
        try:
            cur2.execute(
                "INSERT INTO videos (course_id,title,description,video_url,duration,uploaded_by) VALUES (%s,%s,%s,%s,%s,%s)",
                (int(course_id), title, description or None, video_url, duration or None, uid)
            )
            conn2.commit(); flash('Video uploaded! 🎉', 'success')
        except Exception as e:
            conn2.rollback(); flash(f'Upload failed: {e}', 'error')
        finally: cur2.close(); conn2.close()
        return redirect(url_for('upload_video'))
    cursor.execute("""
        SELECT v.*,c.title AS course_title FROM videos v
        JOIN courses c ON v.course_id=c.id
        WHERE v.uploaded_by=%s ORDER BY v.id DESC
    """, (uid,))
    videos = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('staff/upload_video.html', courses=courses, videos=videos)

# ── STAFF EDIT VIDEO ─────────────────────────
@app.route('/edit_video/<int:vid>', methods=['GET', 'POST'])
@login_required
@role_required('staff')
def edit_video(vid):
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    # Security: only uploader can edit
    cursor.execute("SELECT * FROM videos WHERE id=%s AND uploaded_by=%s", (vid, uid))
    video = cursor.fetchone()
    if not video:
        flash('Video not found or access denied!', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('upload_video'))
    cursor.execute("SELECT id,title FROM courses WHERE created_by=%s", (uid,)); courses = cursor.fetchall()
    if request.method == 'POST':
        title       = request.form.get('title','').strip()
        description = request.form.get('description','').strip()
        duration    = request.form.get('duration','').strip()
        course_id   = request.form.get('course_id','').strip()
        video_url   = request.form.get('video_url','').strip() or video['video_url']
        vf = request.files.get('video_file')
        if vf and vf.filename and allowed(vf.filename, ALLOWED_VIDEO):
            fn = secure_filename(vf.filename)
            vf.save(os.path.join(VIDEO_FOLDER, fn))
            video_url = f'/static/uploads/videos/{fn}'
        try:
            cursor.execute(
                "UPDATE videos SET title=%s,description=%s,duration=%s,course_id=%s,video_url=%s WHERE id=%s",
                (title, description, duration, int(course_id), video_url, vid)
            )
            conn.commit(); flash('Video updated! ✅', 'success')
        except Exception as e:
            conn.rollback(); flash(f'Update failed: {e}', 'error')
        finally: cursor.close(); conn.close()
        return redirect(url_for('upload_video'))
    cursor.close(); conn.close()
    return render_template('staff/edit_video.html', video=video, courses=courses)

# ── STAFF DELETE VIDEO ───────────────────────
@app.route('/delete_video/<int:vid>')
@login_required
@role_required('staff')
def delete_video(vid):
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM videos WHERE id=%s AND uploaded_by=%s", (vid, uid))
    video = cursor.fetchone()
    if not video:
        flash('Video not found or access denied!', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('upload_video'))
    cursor.execute("DELETE FROM videos WHERE id=%s", (vid,))
    conn.commit(); cursor.close(); conn.close()
    flash('Video deleted! 🗑️', 'success')
    return redirect(url_for('upload_video'))

# ══════════════════════════════════════════
#  STUDENT MODULE
# ══════════════════════════════════════════
@app.route('/student_dashboard')
@login_required
@role_required('student')
def student_dashboard():
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS c FROM enrollments WHERE student_id=%s", (uid,));               enrolled  = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM attendance WHERE student_id=%s AND status='present'", (uid,)); present   = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM attendance WHERE student_id=%s", (uid,));                total_att = cursor.fetchone()['c']
    cursor.execute("SELECT score,total FROM quiz_results WHERE student_id=%s ORDER BY taken_at DESC LIMIT 1", (uid,)); last_quiz = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) AS c FROM certificates WHERE student_id=%s", (uid,));              certs     = cursor.fetchone()['c']
    cursor.execute("SELECT photo FROM users WHERE id=%s", (uid,)); photo_row = cursor.fetchone()
    att_pct = round((present / total_att * 100) if total_att else 0)
    photo   = photo_row['photo'] if photo_row else ''
    cursor.close(); conn.close()
    return render_template('student/student_dashboard.html',
                           enrolled=enrolled, att_pct=att_pct,
                           last_quiz=last_quiz, certs=certs, photo=photo)

@app.route('/courses')
@login_required
def courses():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses ORDER BY id DESC")
    data = cursor.fetchall(); cursor.close(); conn.close()
    return render_template('student/courses.html', data=data)

@app.route('/course/<int:cid>')
@login_required
def course_detail(cid):
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE id=%s", (cid,)); course = cursor.fetchone()
    cursor.execute("SELECT * FROM videos WHERE course_id=%s ORDER BY id", (cid,)); videos = cursor.fetchall()
    cursor.close(); conn.close()
    if not course:
        flash('Course not found.', 'error'); return redirect(url_for('courses'))
    return render_template('student/course_detail.html', course=course, videos=videos)

@app.route('/learn/<int:cid>')
@login_required
@role_required('student')
def learn(cid):
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses WHERE id=%s", (cid,)); course = cursor.fetchone()
    cursor.execute("SELECT * FROM videos WHERE course_id=%s ORDER BY id", (cid,)); videos = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) AS c FROM enrollments WHERE student_id=%s AND course_id=%s", (uid, cid))
    if cursor.fetchone()['c'] == 0:
        cursor.execute("INSERT INTO enrollments (student_id,course_id) VALUES (%s,%s)", (uid, cid))
        conn.commit()
    cursor.close(); conn.close()
    return render_template('student/learn.html', course=course, videos=videos)

@app.route('/quiz/<int:cid>', methods=['GET', 'POST'])
@login_required
@role_required('student')
def quiz(cid):
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM quiz WHERE course_id=%s", (cid,)); questions = cursor.fetchall()
    if request.method == 'POST':
        score = sum(1 for q in questions
                    if request.form.get(str(q['id'])) and
                    int(request.form.get(str(q['id']))) == q['correct'])
        cursor.execute(
            "INSERT INTO quiz_results (student_id,course_id,score,total) VALUES (%s,%s,%s,%s)",
            (session['user_id'], cid, score, len(questions))
        )
        conn.commit()
        if questions and (score / len(questions)) >= 0.6:
            pct   = round(score / len(questions) * 100)
            badge = 'Gold' if pct >= 80 else 'Silver' if pct >= 60 else 'Bronze'
            # Save photo_url into certificate
            cursor.execute("SELECT photo FROM users WHERE id=%s", (session['user_id'],))
            photo_row = cursor.fetchone()
            photo_url = photo_row['photo'] if photo_row else None
            cursor.execute(
                "INSERT INTO certificates (student_id,course_id,score,badge,photo_url) VALUES (%s,%s,%s,%s,%s)",
                (session['user_id'], cid, pct, badge, photo_url)
            )
            conn.commit()
        cursor.close(); conn.close()
        return redirect(url_for('result', cid=cid))
    cursor.close(); conn.close()
    return render_template('student/quiz.html', questions=questions, course_id=cid)

@app.route('/result/<int:cid>')
@login_required
@role_required('student')
def result(cid):
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.*,c.title FROM quiz_results r
        JOIN courses c ON r.course_id=c.id
        WHERE r.student_id=%s AND r.course_id=%s
        ORDER BY r.taken_at DESC LIMIT 1
    """, (session['user_id'], cid))
    res = cursor.fetchone(); cursor.close(); conn.close()
    return render_template('student/result.html', result=res, course_id=cid)

@app.route('/attendance')
@login_required
@role_required('student')
def attendance():
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS c FROM attendance WHERE student_id=%s", (uid,));               total   = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM attendance WHERE student_id=%s AND status='present'", (uid,)); present = cursor.fetchone()['c']
    pct = round((present / total * 100) if total else 0)
    cursor.close(); conn.close()
    return render_template('student/attendance.html', total=total, present=present, percentage=pct)

@app.route('/assignment', methods=['GET', 'POST'])
@login_required
@role_required('student')
def assignment():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.*,c.title AS course_title FROM assignments a
        JOIN courses c ON a.course_id=c.id ORDER BY a.due_date
    """)
    assignments = cursor.fetchall()
    if request.method == 'POST':
        aid = request.form.get('assignment_id')
        ans = request.form.get('answer_text','')
        fp  = ''
        if 'file' in request.files:
            f = request.files['file']
            if f and f.filename:
                fn = secure_filename(f.filename)
                f.save(os.path.join(UPLOAD_FOLDER, fn))
                fp = f'/static/uploads/{fn}'
        cursor.execute(
            "INSERT INTO submissions (assignment_id,student_id,answer_text,file_path) VALUES (%s,%s,%s,%s)",
            (aid, session['user_id'], ans, fp)
        )
        conn.commit(); flash('Assignment submitted! ✅', 'success')
    cursor.close(); conn.close()
    return render_template('student/assignment.html', assignments=assignments, today=date.today())

@app.route('/certificate')
@login_required
@role_required('student')
def certificate():
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT cert.*,c.title,u.name,u.photo
        FROM certificates cert
        JOIN courses c ON cert.course_id=c.id
        JOIN users   u ON cert.student_id=u.id
        WHERE cert.student_id=%s ORDER BY cert.issued_at DESC LIMIT 1
    """, (session['user_id'],))
    cert = cursor.fetchone(); cursor.close(); conn.close()
    if not cert:
        flash('No certificate yet. Score 60%+ in a quiz!', 'error')
        return redirect(url_for('student_dashboard'))
    stars = round((cert['score'] / 100) * 5)
    # Use cert-level photo_url first, fallback to user photo
    photo_url = cert.get('photo_url') or cert.get('photo') or ''
    return render_template('student/certificate.html',
                           name=cert['name'], course=cert['title'],
                           score=cert['score'], badge=cert['badge'],
                           stars=stars, date=cert['issued_at'].strftime('%B %d, %Y'),
                           photo_url=photo_url)

@app.route('/mark_my_attendance')
@login_required
@role_required('student')
def mark_my_attendance():
    uid = session['user_id']
    conn = get_connection(); cursor = conn.cursor()
    cursor.execute("SELECT course_id FROM enrollments WHERE student_id=%s", (uid,))
    for (cid,) in cursor.fetchall():
        cursor.execute(
            "INSERT IGNORE INTO attendance (student_id,course_id,date,status) VALUES (%s,%s,%s,'present')",
            (uid, cid, str(date.today()))
        )
    conn.commit(); cursor.close(); conn.close()
    flash('Attendance marked for today! ✅', 'success')
    return redirect(url_for('student_dashboard'))

# ══════════════════════════════════════════
#  PROFILE PAGES (NEW)
# ══════════════════════════════════════════
@app.route('/student_profile/<int:sid>')
@login_required
def student_profile(sid):
    """View detailed student profile with photo and statistics"""
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    # Get student details with photo
    cursor.execute("""
        SELECT u.id,u.name,u.email,u.mobile,u.dob,u.photo,u.created_at,
               s.roll_no,s.course,s.year,s.semester,s.college,s.department
        FROM users u LEFT JOIN students s ON u.id=s.user_id
        WHERE u.id=%s AND u.role='student'
    """, (sid,))
    student = cursor.fetchone()
    
    if not student:
        flash('Student not found.', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('student_dashboard'))
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) AS c FROM enrollments WHERE student_id=%s", (sid,))
    enrolled = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM attendance WHERE student_id=%s AND status='present'", (sid,))
    present = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM attendance WHERE student_id=%s", (sid,))
    total_att = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM certificates WHERE student_id=%s", (sid,))
    certs = cursor.fetchone()['c']
    cursor.execute("SELECT score,total FROM quiz_results WHERE student_id=%s ORDER BY taken_at DESC LIMIT 1", (sid,))
    last_quiz = cursor.fetchone()
    
    att_pct = round((present / total_att * 100) if total_att else 0)
    cursor.close(); conn.close()
    
    return render_template('student/student_profile.html',
                           student=student, enrolled=enrolled, att_pct=att_pct,
                           certs=certs, last_quiz=last_quiz)

@app.route('/staff_profile/<int:sid>')
@login_required
def staff_profile(sid):
    """View detailed staff profile with photo and statistics"""
    conn = get_connection(); cursor = conn.cursor(dictionary=True)
    # Get staff details with photo
    cursor.execute("""
        SELECT u.id,u.name,u.email,u.mobile,u.dob,u.photo,u.created_at,
               s.staff_id,s.department,s.designation,s.experience,s.qualification
        FROM users u LEFT JOIN staff s ON u.id=s.user_id
        WHERE u.id=%s AND u.role='staff'
    """, (sid,))
    staff = cursor.fetchone()
    
    if not staff:
        flash('Staff member not found.', 'error')
        cursor.close(); conn.close()
        return redirect(url_for('staff_dashboard'))
    
    # Get statistics
    cursor.execute("SELECT COUNT(*) AS c FROM courses WHERE created_by=%s", (sid,))
    courses_created = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) AS c FROM videos WHERE uploaded_by=%s", (sid,))
    videos_uploaded = cursor.fetchone()['c']
    
    cursor.close(); conn.close()
    
    return render_template('staff/staff_profile.html',
                           staff=staff, courses_created=courses_created,
                           videos_uploaded=videos_uploaded)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
