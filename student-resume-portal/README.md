# Student Resume Portal - Azure Cloud Application

A production-ready Flask web application demonstrating Azure cloud services integration. Perfect for Azure seminars, college final year projects, resume portfolios, and cloud deployment learning.

## 🌟 Features

- **Student Management**: Upload, view, edit, and delete student profiles
- **Resume Storage**: Secure cloud storage via Azure Blob Storage
- **Advanced Search**: Search students by name or skills
- **Dashboard**: Real-time statistics and insights
- **Azure Integration**: Full integration with Azure cloud services
- **Modern UI**: Responsive Bootstrap 5 interface with Azure-inspired design
- **File Validation**: Secure file upload with validation (PDF, DOC, DOCX)
- **Error Handling**: Comprehensive error pages and logging
- **Production Ready**: Docker containerization and GitHub Actions CI/CD

## 🏗️ Azure Architecture

```
┌─────────────────┐
│  Student Browser│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Azure App      │
│  Service        │
│  (Linux/Python) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Flask          │      │  Azure Blob       │
│  Application    ├─────►│  Storage          │
│                 │      │  (Resumes)        │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌──────────────────┐
│  Azure SQL       │
│  Database        │
│  (Students)      │
└──────────────────┘
```

## 🔧 Azure Services Used

| Service | Purpose | Tier |
|---------|---------|------|
| **Azure App Service** | Web hosting | Free (F1) |
| **Azure SQL Database** | Student data storage | Free Tier |
| **Azure Blob Storage** | Resume file storage | Standard LRS |
| **Azure Container Registry** | Docker image registry | (Optional) |

## 📋 Prerequisites

- Azure Account with active subscription
- Python 3.11 or higher
- Git and GitHub account
- Docker (optional, for containerization)
- ODBC Driver 18 for SQL Server

## 🚀 Azure Setup

### Existing Resources (Already Created)

**Resource Group**: `students-res`
**Region**: `Central India`
**Storage Account**: Already created with `resumes` container
**SQL Server**: `student-sql-yaga`
**Database**: `students-db`
**App Service**: Already created

### Required Environment Variables

```bash
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=your-storage-connection-string

# Azure SQL Database
AZURE_SQL_SERVER=student-sql-yaga.database.windows.net
AZURE_SQL_DATABASE=students-db
AZURE_SQL_USERNAME=azureadmin
AZURE_SQL_PASSWORD=your-password
AZURE_SQL_DRIVER={ODBC Driver 18 for SQL Server}
```

## 💻 Local Development

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd student-resume-portal
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file or export variables:

```bash
export FLASK_SECRET_KEY="dev-secret-key-123"
export AZURE_STORAGE_CONNECTION_STRING="your-connection-string"
export AZURE_SQL_SERVER="student-sql-yaga.database.windows.net"
export AZURE_SQL_DATABASE="students-db"
export AZURE_SQL_USERNAME="azureadmin"
export AZURE_SQL_PASSWORD="your-password"
export AZURE_SQL_DRIVER="{ODBC Driver 18 for SQL Server}"
```

### 5. Run the Application

```bash
# Development mode
flask run

# Or with Python
python app.py
```

The application will be available at `http://localhost:5000`

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t student-resume-portal .
```

### Run Container

```bash
docker run -p 8000:8000 \
  -e FLASK_SECRET_KEY="your-secret" \
  -e AZURE_STORAGE_CONNECTION_STRING="your-connection-string" \
  -e AZURE_SQL_SERVER="your-server" \
  -e AZURE_SQL_DATABASE="students-db" \
  -e AZURE_SQL_USERNAME="username" \
  -e AZURE_SQL_PASSWORD="password" \
  -e AZURE_SQL_DRIVER="{ODBC Driver 18 for SQL Server}" \
  student-resume-portal
```

## ☁️ Azure Deployment

### Using GitHub Actions

1. **Fork and Clone**: Fork this repository and clone it locally
2. **Configure Secrets**: Add these secrets to your GitHub repository:
   - `AZURE_WEBAPP_PUBLISH_PROFILE`: Azure App Service publish profile
   - `AZURE_CONTAINER_REGISTRY`: Container registry URL (optional)
   - `AZURE_CONTAINER_REGISTRY_USERNAME`: Container registry username (optional)
   - `AZURE_CONTAINER_REGISTRY_PASSWORD`: Container registry password (optional)

3. **Push to GitHub**: Push to `main` branch to trigger automatic deployment

### Manual Deployment

```bash
# Install Azure CLI
az login

# Deploy to Azure App Service
az webapp up --name student-resume-portal --resource-group students-res --sku F1

# Configure app settings
az webapp config appsettings set --name student-resume-portal --resource-group students-res --settings \
  FLASK_SECRET_KEY="your-secret" \
  AZURE_STORAGE_CONNECTION_STRING="your-connection-string" \
  AZURE_SQL_SERVER="student-sql-yaga.database.windows.net" \
  AZURE_SQL_DATABASE="students-db" \
  AZURE_SQL_USERNAME="azureadmin" \
  AZURE_SQL_PASSWORD="your-password" \
  AZURE_SQL_DRIVER="{ODBC Driver 18 for SQL Server}"
```

## 📁 Project Structure

```
student-resume-portal/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
├── .dockerignore               # Docker ignore rules
│
├── templates/                  # HTML templates
│   ├── base.html              # Base template with navigation
│   ├── index.html             # Home page with student listing
│   ├── upload.html            # Student upload form
│   ├── detail.html            # Student detail page
│   ├── edit.html              # Edit student form
│   ├── dashboard.html         # Dashboard with statistics
│   ├── 404.html               # 404 error page
│   └── 500.html               # 500 error page
│
├── static/                     # Static files
│   ├── css/                    # Custom CSS files
│   ├── js/                     # Custom JavaScript files
│   └── images/                 # Image assets
│
└── .github/
    └── workflows/
        └── azure-webapp.yml   # GitHub Actions workflow
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page - list all students |
| `/dashboard` | GET | Dashboard with statistics |
| `/upload` | GET/POST | Upload student resume form |
| `/student/<id>` | GET | Student detail page |
| `/edit/<id>` | GET/POST | Edit student details |
| `/delete/<id>` | POST | Delete student profile |
| `/download/<id>` | GET | Download student resume |
| `/search` | GET | Search students by name/skills |

## 🗄️ Database Schema

### Students Table

```sql
CREATE TABLE students (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(100) NOT NULL UNIQUE,
    skills NVARCHAR(MAX),
    resume_url NVARCHAR(255),
    resume_filename NVARCHAR(255),
    created_at DATETIME DEFAULT GETDATE()
);
```

## 🔐 Security Features

- Input validation and sanitization
- File type validation (PDF, DOC, DOCX only)
- File size limit (10 MB maximum)
- Duplicate email prevention
- SQL injection prevention
- Secure error handling
- Azure secure connection strings
- Non-root Docker user

## 🎨 UI Features

- **Responsive Design**: Mobile-first Bootstrap 5 layout
- **Azure Color Scheme**: Professional Azure-inspired design
- **Modern Cards**: Card-based UI with hover effects
- **Navigation**: Sticky navbar with mobile support
- **Animations**: Smooth transitions and fade-in effects
- **Error Pages**: Custom 404 and 500 pages
- **Flash Messages**: Auto-dismiss notifications
- **Search Interface**: Real-time search functionality
- **Dashboard**: Statistics and insights

## 📊 Features Breakdown

### Student Management
- Upload student profiles with resume files
- View all students in a responsive grid
- Edit student details (name, email, skills)
- Delete students (removes both database record and blob storage file)
- Download resumes directly

### Search Functionality
- Search by student name
- Search by skills
- Real-time search results
- Clear search functionality

### Dashboard
- Total students count
- Recent students (added this week)
- Azure services integration status
- Quick action buttons

### File Handling
- Azure Blob Storage integration
- Secure file upload
- File type validation
- File size validation
- Direct download links

## 🛠️ Technologies Used

- **Backend**: Flask 2.3.0, Python 3.11
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Database**: Azure SQL Database, pyodbc
- **Storage**: Azure Blob Storage
- **Hosting**: Azure App Service (Linux)
- **Containerization**: Docker, Gunicorn
- **CI/CD**: GitHub Actions
- **Version Control**: Git

## 📝 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `FLASK_SECRET_KEY` | Yes | Flask session encryption key | `your-secret-key-123` |
| `AZURE_STORAGE_CONNECTION_STRING` | Yes | Azure Storage connection string | `DefaultEndpointsProtocol=https...` |
| `AZURE_SQL_SERVER` | Yes | SQL Server hostname | `server.database.windows.net` |
| `AZURE_SQL_DATABASE` | Yes | Database name | `students-db` |
| `AZURE_SQL_USERNAME` | Yes | Database username | `azureadmin` |
| `AZURE_SQL_PASSWORD` | Yes | Database password | `YourPassword123!` |
| `AZURE_SQL_DRIVER` | Yes | ODBC Driver specification | `{ODBC Driver 18 for SQL Server}` |

## 🐛 Troubleshooting

### ODBC Driver Issues

If you encounter ODBC driver errors:

1. **Linux/Ubuntu**:
   ```bash
   curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
   curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
   apt-get update
   ACCEPT_EULA=Y apt-get install -y msodbcsql18
   ```

2. **Windows**: Download from [Microsoft ODBC Driver for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

3. **macOS**: Install using Homebrew:
   ```bash
   brew tap microsoft/mssql-release
   brew update
   ACCEPT_EULA=Y brew install msodbcsql18
   ```

### Database Connection Issues

1. Verify firewall rules allow your IP
2. Check SQL Server credentials
3. Ensure database server is accessible
4. Verify connection string format

### Azure Storage Issues

1. Verify storage account connection string
2. Check container exists (`resumes`)
3. Ensure proper permissions
4. Test connection using Azure Storage Explorer

## 📈 Performance Optimization

- Connection pooling for database queries
- Efficient blob storage operations
- Caching headers for static content
- Optimized Docker image size
- Gunicorn worker configuration
- Database indexes on frequently queried fields

## 🔄 Continuous Improvement

Potential enhancements:
- [ ] User authentication and authorization
- [ ] Bulk upload functionality
- [ ] Advanced search filters
- [ ] Export to CSV functionality
- [ ] Email notifications
- [ ] Resume preview in browser
- [ ] Multi-language support
- [ ] Application Insights integration
- [ ] API rate limiting
- [ ] Cache layer with Redis

## 🤝 Contributing

This is an educational project. Feel free to use it for:
- Azure seminar demonstrations
- College final year projects
- Resume portfolio projects
- Cloud deployment learning
- GitHub showcase

## 📄 License

MIT License - Feel free to use for educational purposes.

## 👨‍💻 Author

Created as a demonstration of Azure cloud services integration with modern web development practices.

## 🙏 Acknowledgments

- Microsoft Azure for cloud services
- Flask web framework
- Bootstrap for UI components
- Open source community

---

**Note**: This project is designed for educational and demonstration purposes. Always follow security best practices when deploying to production environments.

For questions or issues, please open an issue in the GitHub repository.