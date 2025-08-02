# QuickDesk - Help Desk Solution

A simple, powerful help desk solution built with Flask, SQLAlchemy, and SQLite. QuickDesk provides an intuitive interface for managing support tickets with role-based access control, file attachments, and real-time updates.

## Features

### Core Functionality
- **User Authentication**: Secure login/registration system with role-based access
- **Ticket Management**: Create, view, update, and track support tickets
- **File Attachments**: Support for multiple file uploads (up to 16MB)
- **Comments System**: Threaded conversations on tickets
- **Voting System**: Upvote/downvote tickets for prioritization
- **Status Tracking**: Open → In Progress → Resolved → Closed workflow

### Role-Based Access
- **End Users**: Create tickets, view own tickets, add comments
- **Support Agents**: Manage tickets, update status, respond to users
- **Administrators**: User management, category management, system oversight

### Advanced Features
- **Search & Filtering**: Filter by status, category, priority, and search text
- **Pagination**: Efficient handling of large ticket volumes
- **Email Notifications**: Automatic notifications for ticket updates
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Templates**: Jinja2 templating engine
- **Authentication**: Flask-Login
- **File Handling**: Werkzeug secure file uploads

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd quick-desk
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration (Optional)
Create a `.env` file in the project root:
```env
# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_ENV=development
FLASK_DEBUG=1

# Database Configuration (SQLite - no setup required!)
DATABASE_URL=sqlite:///quickdesk.db

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Step 5: Initialize Database
```bash
python app.py
```
The application will automatically create the SQLite database and seed initial data on first run.

## Usage

### Starting the Application
```bash
python app.py
```
The application will be available at `http://localhost:5000`

### Default Admin Account
- **Username**: admin
- **Password**: admin123
- **Role**: Administrator

### User Roles

#### End User
- Register/login to the system
- Create new tickets with attachments
- View and track own tickets
- Add comments to own tickets
- Vote on tickets (upvote/downvote)
- Search and filter tickets

#### Support Agent
- All end user capabilities
- View all tickets (not just own)
- Update ticket status
- Add comments to any ticket
- Access to ticket management tools

#### Administrator
- All agent capabilities
- User management
- Category management
- System configuration
- Access to admin dashboard

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /register` - Registration page
- `POST /register` - Create new user
- `GET /logout` - Logout user

### Tickets
- `GET /dashboard` - Main dashboard with ticket list
- `GET /ticket/new` - Create new ticket form
- `POST /ticket/new` - Submit new ticket
- `GET /ticket/<id>` - View ticket details
- `POST /ticket/<id>/comment` - Add comment to ticket
- `POST /ticket/<id>/update_status` - Update ticket status (agents/admin)
- `POST /ticket/<id>/vote` - Vote on ticket

### Admin
- `GET /admin/users` - User management
- `GET /admin/categories` - Category management
- `POST /admin/categories` - Create new category
- `POST /admin/category/<id>/delete` - Delete category

## Database Schema

### Users
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- role (user/agent/admin)
- created_at

### Categories
- id (Primary Key)
- name
- description
- created_at

### Tickets
- id (Primary Key)
- subject
- description
- status (open/in_progress/resolved/closed)
- priority (low/medium/high/urgent)
- user_id (Foreign Key)
- category_id (Foreign Key)
- assigned_to (Foreign Key)
- upvotes
- downvotes
- created_at
- updated_at

### Comments
- id (Primary Key)
- content
- user_id (Foreign Key)
- ticket_id (Foreign Key)
- created_at

### Attachments
- id (Primary Key)
- filename
- original_filename
- file_path
- ticket_id (Foreign Key)
- created_at

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask secret key for session management
- `DATABASE_URL`: SQLite database path (default: sqlite:///quickdesk.db)
- `MAIL_SERVER`: SMTP server for email notifications
- `MAIL_PORT`: SMTP port
- `MAIL_USERNAME`: Email username
- `MAIL_PASSWORD`: Email password

### File Upload Settings
- Maximum file size: 16MB
- Supported formats: PDF, DOC, DOCX, TXT, JPG, JPEG, PNG, GIF
- Upload directory: `uploads/`

## Security Features

- Password hashing with bcrypt
- CSRF protection
- Secure file uploads with filename sanitization
- Role-based access control
- Session management with Flask-Login
- Input validation and sanitization

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - URL: `http://localhost:5000`
   - Login: admin / admin123

4. **Test the installation:**
   ```bash
   python test_installation.py
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please create an issue in the repository or contact the development team.

## Roadmap

- [ ] Email notifications implementation
- [ ] Advanced reporting and analytics
- [ ] API endpoints for mobile apps
- [ ] Real-time notifications with WebSockets
- [ ] Multi-language support
- [ ] Advanced search with Elasticsearch
- [ ] Integration with external tools (Slack, Teams)
- [ ] Automated ticket assignment
- [ ] Knowledge base integration