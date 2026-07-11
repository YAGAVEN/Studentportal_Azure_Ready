from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import os
import pyodbc
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB limit
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key')

# Azure configuration
AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
AZURE_SQL_SERVER = os.environ.get('AZURE_SQL_SERVER')
AZURE_SQL_DATABASE = os.environ.get('AZURE_SQL_DATABASE')
AZURE_SQL_USERNAME = os.environ.get('AZURE_SQL_USERNAME')
AZURE_SQL_PASSWORD = os.environ.get('AZURE_SQL_PASSWORD')
AZURE_SQL_DRIVER = os.environ.get('AZURE_SQL_DRIVER', '{ODBC Driver 18 for SQL Server}')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Azure Blob Storage setup
blob_service_client = None
container_name = "resumes"

try:
    if AZURE_STORAGE_CONNECTION_STRING:
        blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )
        logger.info("Azure Blob Storage connected successfully")
    else:
        logger.warning("Azure Storage connection string not configured")
except Exception as e:
    logger.error(f"Azure Storage connection failed: {str(e)}")

# Database connection setup
def get_db_connection():
    """Create and return a database connection"""
    try:
        connection_string = (
            f'DRIVER={AZURE_SQL_DRIVER};'
            f'SERVER={AZURE_SQL_SERVER};'
            f'DATABASE={AZURE_SQL_DATABASE};'
            f'UID={AZURE_SQL_USERNAME};'
            f'PWD={AZURE_SQL_PASSWORD}'
        )
        connection = pyodbc.connect(connection_string, timeout=30)
        return connection
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

def init_db():
    """Initialize database table if not exists"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create students table if not exists
        cursor.execute('''
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[students]') AND type in (N'U'))
            CREATE TABLE students (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(100) NOT NULL,
                email NVARCHAR(100) NOT NULL UNIQUE,
                skills NVARCHAR(MAX),
                resume_url NVARCHAR(255),
                resume_filename NVARCHAR(255),
                created_at DATETIME DEFAULT GETDATE()
            )
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Database initialized successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Home page with student listing"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all students ordered by creation date
        cursor.execute('SELECT * FROM students ORDER BY created_at DESC')

        # Convert to list of dictionaries for easier template rendering
        students = []
        for row in cursor.fetchall():
            students.append({
                'id': row.id,
                'name': row.name,
                'email': row.email,
                'skills': row.skills,
                'resume_url': row.resume_url,
                'resume_filename': row.resume_filename,
                'created_at': row.created_at
            })

        cursor.close()
        conn.close()

        return render_template('index.html', students=students)

    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}")
        flash('Error loading student data. Please try again.', 'error')
        return render_template('index.html', students=[])

@app.route('/dashboard')
def dashboard():
    """Dashboard with statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get total students count
        cursor.execute('SELECT COUNT(*) FROM students')
        total_students = cursor.fetchone()[0]

        # Get students added this week
        cursor.execute('''
            SELECT COUNT(*) FROM students
            WHERE created_at >= DATEADD(day, -7, GETDATE())
        ''')
        recent_students = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return render_template('dashboard.html',
                             total_students=total_students,
                             recent_students=recent_students)

    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash('Error loading dashboard data. Please try again.', 'error')
        return render_template('dashboard.html', total_students=0, recent_students=0)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload student resume and details"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            skills = request.form.get('skills', '').strip()
            resume = request.files.get('resume')

            # Validation
            if not name or not email:
                flash('Name and email are required fields.', 'error')
                return render_template('upload.html')

            if not resume:
                flash('Resume file is required.', 'error')
                return render_template('upload.html')

            if not allowed_file(resume.filename):
                flash('Only PDF, DOC, and DOCX files are allowed.', 'error')
                return render_template('upload.html')

            # Check file size (Flask MAX_CONTENT_LENGTH should handle this, but double-check)
            resume.seek(0, os.SEEK_END)
            file_size = resume.tell() / (1024 * 1024)  # Size in MB
            resume.seek(0)  # Reset file pointer

            if file_size > 10:
                flash('File size exceeds 10 MB limit.', 'error')
                return render_template('upload.html')

            # Check for duplicate email
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM students WHERE email = ?', (email,))
            if cursor.fetchone()[0] > 0:
                cursor.close()
                conn.close()
                flash('Email already exists. Please use a different email address.', 'error')
                return render_template('upload.html')

            # Upload to Azure Blob Storage
            resume_url = None
            resume_filename = None

            if blob_service_client:
                try:
                    # Generate unique filename
                    file_extension = resume.filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{secure_filename(name)}.{file_extension}"

                    blob_client = blob_service_client.get_blob_client(
                        container=container_name,
                        blob=unique_filename
                    )

                    # Reset file pointer and upload
                    resume.seek(0)
                    blob_client.upload_blob(resume.read(), overwrite=True)

                    resume_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{unique_filename}"
                    resume_filename = unique_filename

                    logger.info(f"Resume uploaded successfully: {unique_filename}")

                except Exception as e:
                    logger.error(f"Blob upload failed: {str(e)}")
                    cursor.close()
                    conn.close()
                    flash('Error uploading resume to cloud storage. Please try again.', 'error')
                    return render_template('upload.html')
            else:
                flash('Cloud storage is not configured. Resume will not be uploaded.', 'warning')

            # Save to database
            try:
                cursor.execute('''
                    INSERT INTO students (name, email, skills, resume_url, resume_filename)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, email, skills, resume_url, resume_filename))

                conn.commit()
                cursor.close()
                conn.close()

                flash('Student profile created successfully!', 'success')
                return redirect(url_for('index'))

            except Exception as e:
                logger.error(f"Database insert failed: {str(e)}")
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
                flash('Error saving student details. Please try again.', 'error')
                return render_template('upload.html')

        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return render_template('upload.html')

    return render_template('upload.html')

@app.route('/student/<int:student_id>')
def student_detail(student_id):
    """Student detail page"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            flash('Student not found.', 'error')
            return redirect(url_for('index'))

        student = {
            'id': row.id,
            'name': row.name,
            'email': row.email,
            'skills': row.skills,
            'resume_url': row.resume_url,
            'resume_filename': row.resume_filename,
            'created_at': row.created_at
        }

        return render_template('detail.html', student=student)

    except Exception as e:
        logger.error(f"Error fetching student details: {str(e)}")
        flash('Error loading student details. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/search')
def search():
    """Search students by name or skills"""
    query = request.args.get('q', '').strip()

    if not query:
        return redirect(url_for('index'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Search in both name and skills fields
        cursor.execute('''
            SELECT * FROM students
            WHERE name LIKE ? OR skills LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{query}%', f'%{query}%'))

        students = []
        for row in cursor.fetchall():
            students.append({
                'id': row.id,
                'name': row.name,
                'email': row.email,
                'skills': row.skills,
                'resume_url': row.resume_url,
                'resume_filename': row.resume_filename,
                'created_at': row.created_at
            })

        cursor.close()
        conn.close()

        return render_template('index.html', students=students, search_query=query)

    except Exception as e:
        logger.error(f"Error searching students: {str(e)}")
        flash('Error performing search. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit student details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            skills = request.form.get('skills', '').strip()

            if not name or not email:
                flash('Name and email are required fields.', 'error')
                return render_template('edit.html', student=None)

            # Check for duplicate email (excluding current student)
            cursor.execute('SELECT COUNT(*) FROM students WHERE email = ? AND id != ?', (email, student_id))
            if cursor.fetchone()[0] > 0:
                flash('Email already exists. Please use a different email address.', 'error')
                return render_template('edit.html', student=None)

            # Update student
            cursor.execute('''
                UPDATE students
                SET name = ?, email = ?, skills = ?
                WHERE id = ?
            ''', (name, email, skills, student_id))

            conn.commit()
            cursor.close()
            conn.close()

            flash('Student details updated successfully!', 'success')
            return redirect(url_for('student_detail', student_id=student_id))

        # GET request - fetch student details
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            flash('Student not found.', 'error')
            return redirect(url_for('index'))

        student = {
            'id': row.id,
            'name': row.name,
            'email': row.email,
            'skills': row.skills,
            'resume_url': row.resume_url,
            'resume_filename': row.resume_filename,
            'created_at': row.created_at
        }

        return render_template('edit.html', student=student)

    except Exception as e:
        logger.error(f"Error editing student: {str(e)}")
        flash('Error updating student details. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Delete student and their resume"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get student details first (for resume deletion)
        cursor.execute('SELECT resume_filename FROM students WHERE id = ?', (student_id,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            flash('Student not found.', 'error')
            return redirect(url_for('index'))

        resume_filename = row.resume_filename

        # Delete from Azure Blob Storage if exists
        if resume_filename and blob_service_client:
            try:
                blob_client = blob_service_client.get_blob_client(
                    container=container_name,
                    blob=resume_filename
                )
                blob_client.delete_blob()
                logger.info(f"Resume deleted from storage: {resume_filename}")
            except Exception as e:
                logger.error(f"Failed to delete resume from storage: {str(e)}")

        # Delete from database
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        cursor.close()
        conn.close()

        flash('Student profile deleted successfully!', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        flash('Error deleting student profile. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/download/<int:student_id>')
def download_resume(student_id):
    """Download student resume"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT resume_filename, name FROM students WHERE id = ?', (student_id,))
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row or not row.resume_filename:
            flash('Resume file not found.', 'error')
            return redirect(url_for('index'))

        # Download from Azure Blob Storage
        if blob_service_client:
            try:
                blob_client = blob_service_client.get_blob_client(
                    container=container_name,
                    blob=row.resume_filename
                )

                download_stream = blob_client.download_blob()
                file_bytes = download_stream.readall()

                # Send file to user
                return send_file(
                    BytesIO(file_bytes),
                    as_attachment=True,
                    download_name=row.resume_filename,
                    mimetype='application/octet-stream'
                )

            except Exception as e:
                logger.error(f"Failed to download resume: {str(e)}")
                flash('Error downloading resume. Please try again.', 'error')
                return redirect(url_for('student_detail', student_id=student_id))
        else:
            flash('Cloud storage is not configured.', 'error')
            return redirect(url_for('student_detail', student_id=student_id))

    except Exception as e:
        logger.error(f"Error in download: {str(e)}")
        flash('Error downloading resume. Please try again.', 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return render_template('500.html'), 500

# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(debug=True)