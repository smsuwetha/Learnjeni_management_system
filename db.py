import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': 'Sneh@2003',
    'database': 'lms_db'
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"[DB ERROR] {e}")
        return None

def init_db():
    try:
        cfg = dict(DB_CONFIG); cfg.pop('database')
        conn = mysql.connector.connect(**cfg)
        cur  = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS lms_db")
        cur.close(); conn.close()
    except Error as e:
        print(f"[DB CREATE ERROR] {e}"); return

    conn   = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            name       VARCHAR(100)  NOT NULL,
            email      VARCHAR(100)  UNIQUE NOT NULL,
            password   VARCHAR(255)  NOT NULL,
            role       ENUM('admin','staff','student') NOT NULL,
            mobile     VARCHAR(15),
            dob        DATE,
            photo      VARCHAR(500)  DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try: cursor.execute("ALTER TABLE users ADD COLUMN photo VARCHAR(500) DEFAULT NULL"); conn.commit()
    except: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            user_id  INT NOT NULL,
            admin_id VARCHAR(20) UNIQUE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            user_id    INT NOT NULL,
            roll_no    VARCHAR(20) UNIQUE,
            course     VARCHAR(100),
            year       VARCHAR(20),
            semester   VARCHAR(20),
            college    VARCHAR(150),
            department VARCHAR(100),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            user_id       INT NOT NULL,
            staff_id      VARCHAR(20) UNIQUE,
            department    VARCHAR(100),
            designation   VARCHAR(100),
            experience    VARCHAR(50),
            qualification VARCHAR(100),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            title       VARCHAR(150) NOT NULL,
            description TEXT,
            department  VARCHAR(100),
            video_url   VARCHAR(300),
            notes_url   VARCHAR(300),
            created_by  INT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            student_id  INT NOT NULL,
            course_id   INT NOT NULL,
            progress    INT DEFAULT 0,
            enrolled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id)  REFERENCES courses(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            course_id   INT NOT NULL,
            title       VARCHAR(150),
            description TEXT,
            video_url   VARCHAR(500),
            thumbnail   VARCHAR(500) DEFAULT NULL,
            duration    VARCHAR(20),
            uploaded_by INT,
            uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id)   REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        )
    """)
    for col, defn in [('description','TEXT'),('thumbnail','VARCHAR(500) DEFAULT NULL')]:
        try: cursor.execute(f"ALTER TABLE videos ADD COLUMN {col} {defn}"); conn.commit()
        except: pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz (
            id        INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT NOT NULL,
            question  TEXT NOT NULL,
            option1   VARCHAR(200),
            option2   VARCHAR(200),
            option3   VARCHAR(200),
            option4   VARCHAR(200),
            correct   INT NOT NULL,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            course_id  INT NOT NULL,
            score      INT DEFAULT 0,
            total      INT DEFAULT 0,
            taken_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id)  REFERENCES courses(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            course_id  INT NOT NULL,
            date       DATE NOT NULL,
            status     ENUM('present','absent') DEFAULT 'present',
            marked_by  INT,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id)  REFERENCES courses(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id          INT AUTO_INCREMENT PRIMARY KEY,
            course_id   INT NOT NULL,
            title       VARCHAR(200),
            description TEXT,
            due_date    DATE,
            created_by  INT,
            FOREIGN KEY (course_id)  REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            assignment_id INT NOT NULL,
            student_id    INT NOT NULL,
            answer_text   TEXT,
            file_path     VARCHAR(300),
            grade         INT,
            submitted_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id)    REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            course_id  INT NOT NULL,
            score      INT,
            badge      VARCHAR(50),
            photo_url  VARCHAR(500) DEFAULT NULL,
            issued_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id)  REFERENCES courses(id) ON DELETE CASCADE
        )
    """)
    try: cursor.execute("ALTER TABLE certificates ADD COLUMN photo_url VARCHAR(500) DEFAULT NULL"); conn.commit()
    except: pass

    conn.commit(); cursor.close(); conn.close()
    print("All tables created / updated successfully!")

    # ── CREATE DEFAULT ADMIN (if not exists) ──────────────────────────────
    from werkzeug.security import generate_password_hash
    conn   = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM users WHERE email=%s", ('admin@learnjeni.com',))
    if not cursor.fetchone():
        hashed = generate_password_hash('Admin@123')
        cursor.execute(
            "INSERT INTO users (name,email,password,role) VALUES (%s,%s,%s,%s)",
            ('Administrator', 'admin@learnjeni.com', hashed, 'admin')
        )
        uid = cursor.lastrowid
        cursor.execute(
            "INSERT INTO admin (user_id, admin_id) VALUES (%s,%s)",
            (uid, 'ADMIN001')
        )
        conn.commit()
        print("Default admin created — Email: admin@learnjeni.com | Password: Admin@123")
    else:
        print("Admin account already exists.")
    cursor.close(); conn.close()

if __name__ == '__main__':
    init_db()
