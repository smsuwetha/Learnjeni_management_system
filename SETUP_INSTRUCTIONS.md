# 🚀 LearnJeni LMS - Complete Setup Instructions

## 📋 Requirements

- Python 3.7+
- MySQL 5.7+ (or MariaDB)
- pip (Python package manager)
- 200MB disk space

---

## 💻 Installation Steps

### Step 1: Prepare Your System

#### Windows:
```bash
# Open Command Prompt or PowerShell
python --version  # Should show Python 3.x
pip --version     # Should show pip version
```

#### Linux/Mac:
```bash
python3 --version  # Should show Python 3.x
pip3 --version     # Should show pip version
```

### Step 2: Extract the ZIP File

```bash
# Windows: Right-click ZIP → Extract All
# Linux/Mac:
unzip lms_complete.zip
cd lms_complete
```

### Step 3: Install Python Dependencies

```bash
# Windows:
pip install -r requirements.txt

# Linux/Mac:
pip3 install -r requirements.txt
```

**What gets installed:**
- Flask - Web framework
- MySQL-connector-python - Database connection
- Werkzeug - Security utilities

### Step 4: Setup MySQL Database

#### Option A: MySQL Already Running

```bash
# Create database user (optional, if needed)
# Open MySQL and run:
mysql -u root -p

# Then in MySQL:
CREATE USER 'lms_user'@'localhost' IDENTIFIED BY 'lms_password';
GRANT ALL PRIVILEGES ON lms_db.* TO 'lms_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Option B: Start MySQL Service

**Windows:**
```bash
# Start MySQL Service
net start MySQL80
# or in Services, find MySQL and start it
```

**Linux:**
```bash
# Start MySQL/MariaDB
sudo systemctl start mysql
# or
sudo systemctl start mariadb
```

**Mac:**
```bash
# Using Homebrew
brew services start mysql
```

### Step 5: Configure Database Connection

Edit `db.py` file:

```python
DB_CONFIG = {
    'host':     'localhost',      # MySQL server address
    'port':     3306,             # MySQL port (default)
    'user':     'root',           # MySQL username
    'password': 'your_password',  # MySQL password
    'database': 'lms_db'          # Database name (auto-created)
}
```

**For default setup (no password):**
```python
DB_CONFIG = {
    'host':     'localhost',
    'port':     3306,
    'user':     'root',
    'password': '',              # Empty if no password
    'database': 'lms_db'
}
```

### Step 6: Initialize Database

```bash
# Windows:
python db.py

# Linux/Mac:
python3 db.py
```

**Expected output:**
```
All tables created / updated successfully!
```

### Step 7: Create Necessary Folders

The app auto-creates these, but you can manually create:

```bash
# Create uploads folder
mkdir -p static/uploads/photos
mkdir -p static/uploads/videos

# Give write permissions (Linux/Mac)
chmod -R 755 static/uploads
```

### Step 8: Run the Application

```bash
# Windows:
python app.py

# Linux/Mac:
python3 app.py
```

**Expected output:**
```
Running on http://127.0.0.1:5000
Press CTRL+C to quit
```

### Step 9: Access the Application

Open your web browser and go to:
```
http://localhost:5000
```

---

## 👥 Login with Default Accounts

### Create New Account First:

1. Click "Register" button
2. Select role: "Student" / "Staff"
3. Fill all fields
4. **Upload a photo** (important!)
5. Click "Register"
6. Now login with your credentials

### Or Use Sample Accounts:

For testing, you can create manually in MySQL:

```sql
-- Run in MySQL command line after db.py
use lms_db;

-- Insert Admin (password: admin123)
INSERT INTO users (name, email, password, role, mobile, dob, photo) 
VALUES (
  'Admin User',
  'admin@lms.com',
  'pbkdf2:sha256:600000$...',  -- Hash of admin123
  'admin',
  '9999999999',
  '1990-01-01',
  '/static/uploads/photos/admin.jpg'
);

-- Insert Student (password: student123)
INSERT INTO users (name, email, password, role, mobile, dob, photo)
VALUES (
  'Test Student',
  'student@lms.com',
  'pbkdf2:sha256:600000$...',  -- Hash of student123
  'student',
  '8888888888',
  '2000-01-01',
  '/static/uploads/photos/student.jpg'
);

-- Insert Staff (password: staff123)
INSERT INTO users (name, email, password, role, mobile, dob, photo)
VALUES (
  'Test Staff',
  'staff@lms.com',
  'pbkdf2:sha256:600000$...',  -- Hash of staff123
  'staff',
  '7777777777',
  '1995-01-01',
  '/static/uploads/photos/staff.jpg'
);
```

---

## 🎯 First Time Usage

### 1. Register as Student:
```
1. Click "Register" button
2. Select role: "Student"
3. Fill information:
   - Name: Your Name
   - Email: your@email.com
   - Password: your_password
   - Mobile: 9999999999
   - DOB: 2000-01-01
   - Upload Photo: ← Click to select image
   - Roll No: CS001
   - Course: B.Tech CSE
   - Year: 1st
   - Semester: 1
   - College: XYZ College
   - Department: Computer Science
4. Click "Register"
5. Login with your email and password
```

### 2. Explore Features:
```
Student can:
- View Dashboard
- Enroll in courses
- Watch videos
- Take quizzes
- View certificates (after 60% score)
- View attendance
- Submit assignments
- Click on own name to see full profile
```

### 3. Check Your Profile:
```
1. Dashboard → Profile Card (right side)
2. Click "View Full Profile" button
3. See your photo, details, and statistics
```

### 4. Earn a Certificate:
```
1. Go to Courses
2. Select a course
3. Click "Learn"
4. Watch videos
5. Take quiz (must score 60%+)
6. Go to Certificate menu
7. See your photo on certificate
8. Print or download as PDF
```

---

## 🔧 Troubleshooting

### Issue 1: "Can't connect to MySQL server"

**Problem:** Database connection error
```
Error: Can't connect to MySQL server at 'localhost:3306'
```

**Solutions:**
```
1. Check MySQL is running:
   - Windows: Services → MySQL
   - Linux: sudo systemctl status mysql
   - Mac: brew services list | grep mysql

2. Check credentials in db.py:
   - Verify hostname, port, user, password

3. Test connection:
   python -c "import mysql.connector; mysql.connector.connect(host='localhost', user='root')"

4. Reset MySQL:
   - Windows: net stop MySQL80 && net start MySQL80
   - Linux: sudo systemctl restart mysql
```

### Issue 2: "Port 5000 already in use"

**Problem:** Flask port in use
```
Error: Address already in use
```

**Solutions:**
```
1. Find and kill process on port 5000:
   - Windows: netstat -ano | findstr :5000
   - Linux: lsof -i :5000
   - Mac: lsof -i :5000

2. Kill the process:
   - Windows: taskkill /PID <pid> /F
   - Linux/Mac: kill -9 <pid>

3. Or use different port in app.py:
   app.run(debug=True, port=5001)
```

### Issue 3: "Photo not uploading"

**Problem:** Photo upload fails
```
Error: File upload failed
```

**Solutions:**
```
1. Create folders:
   mkdir -p static/uploads/photos
   chmod 755 static/uploads/photos

2. Check file size:
   - Must be < 500MB
   - Usually < 5MB for photos

3. Check file format:
   - Only JPG, PNG, GIF, WEBP allowed
   - Not SVG, BMP, TIFF

4. Check permissions:
   - Folder must be writable
   - chmod -R 755 static/
```

### Issue 4: "Template not found"

**Problem:** HTML template missing
```
Error: TemplateNotFound: student/student_profile.html
```

**Solutions:**
```
1. Check file exists:
   templates/student/student_profile.html

2. Check file name:
   - Case sensitive (student_profile.html)
   - Not student-profile.html

3. Verify folder structure:
   lms_complete/
   └── templates/
       ├── student/
       │   ├── student_profile.html
       │   └── ...
       └── staff/
           ├── staff_profile.html
           └── ...

4. Restart Flask server
```

### Issue 5: "404 Not Found on profile page"

**Problem:** Profile route not working
```
Error: 404 Not Found
```

**Solutions:**
```
1. Verify routes in app.py:
   - Check @app.route('/student_profile/<int:sid>')
   - Check @app.route('/staff_profile/<int:sid>')

2. Check route decorator:
   - Must have @login_required
   - Must be before the function definition

3. Restart Flask server:
   - Stop with CTRL+C
   - Run python app.py again

4. Clear browser cache:
   - Ctrl+Shift+Delete (Chrome)
   - Cmd+Shift+Delete (Firefox)
```

### Issue 6: "Login not working"

**Problem:** Can't login
```
Error: Invalid email or password
```

**Solutions:**
```
1. Check account exists:
   - Register new account first
   - Or check database:
     SELECT * FROM users WHERE email='your@email.com';

2. Check password:
   - Passwords are case-sensitive
   - No spaces at beginning/end

3. Check database:
   - Run: python db.py
   - To reinitialize tables

4. Check email:
   - Must match exactly what was registered
```

---

## 📊 Database Operations

### View All Users:
```sql
use lms_db;
SELECT id, name, email, role, photo FROM users;
```

### View Student Details:
```sql
SELECT u.id, u.name, u.email, s.roll_no, s.course, s.year 
FROM users u 
LEFT JOIN students s ON u.id=s.user_id 
WHERE u.role='student';
```

### View Certificates:
```sql
SELECT c.id, c.student_id, c.score, c.badge, c.photo_url, u.name
FROM certificates c
JOIN users u ON c.student_id=u.id;
```

### Backup Database:
```bash
# Windows:
mysqldump -u root -p lms_db > backup.sql

# Linux/Mac:
mysqldump -u root -p lms_db > backup.sql
```

### Restore Database:
```bash
mysql -u root -p lms_db < backup.sql
```

---

## 🔐 Security Setup

### Before Production:

1. **Change Secret Key in app.py:**
```python
app.secret_key = 'your-super-secret-key-123456'  # Change this!
```

2. **Change Database Password:**
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
```

3. **Disable Debug Mode:**
```python
app.run(debug=False)  # Change from True to False
```

4. **Use Environment Variables:**
```bash
# Create .env file
DATABASE_PASSWORD=your_password
FLASK_SECRET_KEY=your_secret_key

# Load in app.py:
import os
app.secret_key = os.getenv('FLASK_SECRET_KEY')
```

---

## 📱 Testing Checklist

After setup, test these:

- [ ] Login page loads
- [ ] Registration page works
- [ ] Can upload photo during registration
- [ ] Can login with credentials
- [ ] Dashboard loads with correct role
- [ ] Can view student profile
- [ ] Can view staff profile
- [ ] Photo displays on profile
- [ ] Can enroll in course (student)
- [ ] Can create course (admin)
- [ ] Can take quiz (student)
- [ ] Can view certificate (student)
- [ ] Photo on certificate
- [ ] Can print/download certificate
- [ ] Mobile responsive
- [ ] No console errors (F12)

---

## 📈 Performance Optimization

### For Better Performance:

1. **Enable Caching:**
```python
# In app.py
app.config['JSON_CACHE'] = 300
```

2. **Use Database Indexing:**
```sql
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_student_user ON students(user_id);
```

3. **Optimize Images:**
- Keep photo size < 2MB
- Use JPG format for photos

4. **Enable Compression:**
```python
from flask_compress import Compress
Compress(app)
```

---

## 🌐 Deployment

### Local Testing:
```bash
python app.py
# Visit http://localhost:5000
```

### Production Deployment:

**Using Gunicorn:**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**Using Nginx + Gunicorn:**
```
nginx acts as reverse proxy
gunicorn runs Flask app
```

### Cloud Deployment:

Options:
- Heroku
- AWS EC2
- Google Cloud
- DigitalOcean
- Azure

---

## 📞 Getting Help

1. **Check Documentation:**
   - README.md - Overview
   - QUICK_REFERENCE.md - Quick guide
   - IMPLEMENTATION_GUIDE.md - Detailed guide
   - CODE_CHANGES.md - Code details

2. **Check Errors:**
   - Browser console (F12)
   - Terminal output
   - Flask error messages

3. **Common Issues:**
   - See Troubleshooting section above

4. **Database Issues:**
   - Verify MySQL is running
   - Check credentials
   - Verify database tables exist

---

## ✅ Installation Complete!

If you've followed all steps, your LMS is ready to use! 🎉

**Next steps:**
1. ✅ Open http://localhost:5000
2. ✅ Register a new student with photo
3. ✅ Login and explore
4. ✅ View your profile
5. ✅ Enroll in a course
6. ✅ Take a quiz
7. ✅ View your certificate!

---

**Need help?** Check the documentation files included in the package.

**Status:** ✅ Ready for use  
**Last Updated:** April 3, 2026  
**Version:** 1.0

Happy learning! 🎓📚🎖️
