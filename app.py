from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///quickdesk.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Notification helper functions
def create_notification(user_id, ticket_id, notification_type, message, comment_id=None):
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        ticket_id=ticket_id,
        type=notification_type,
        message=message,
        comment_id=comment_id
    )
    db.session.add(notification)
    db.session.commit()

def notify_ticket_created(ticket):
    """Notify admins and agents about new ticket"""
    # Notify all admins
    admins = User.query.filter_by(role='admin').all()
    for admin in admins:
        create_notification(
            admin.id,
            ticket.id,
            'ticket_created',
            f'New ticket "{ticket.subject}" created by {ticket.author.username}'
        )
    
    # Notify all agents
    agents = User.query.filter_by(role='agent').all()
    for agent in agents:
        create_notification(
            agent.id,
            ticket.id,
            'ticket_created',
            f'New ticket "{ticket.subject}" created by {ticket.author.username}'
        )

def notify_ticket_assigned(ticket, assigned_user):
    """Notify user when ticket is assigned to them"""
    if assigned_user:
        create_notification(
            assigned_user.id,
            ticket.id,
            'ticket_assigned',
            f'Ticket "{ticket.subject}" has been assigned to you'
        )

def notify_status_changed(ticket, old_status, new_status):
    """Notify ticket creator about status change"""
    create_notification(
        ticket.user_id,
        ticket.id,
        'status_changed',
        f'Your ticket "{ticket.subject}" status changed from {old_status.replace("_", " ").title()} to {new_status.replace("_", " ").title()}'
    )

def notify_comment_added(comment):
    """Notify relevant users about new comment"""
    ticket = comment.ticket
    
    # Notify ticket creator (if comment is not from them)
    if comment.user_id != ticket.user_id:
        create_notification(
            ticket.user_id,
            ticket.id,
            'comment_added',
            f'New comment on your ticket "{ticket.subject}" by {comment.author.username}',
            comment.id
        )
    
    # Notify assigned agent (if different from commenter and ticket creator)
    if ticket.assigned_to and ticket.assigned_to != comment.user_id and ticket.assigned_to != ticket.user_id:
        create_notification(
            ticket.assigned_to,
            ticket.id,
            'comment_added',
            f'New comment on assigned ticket "{ticket.subject}" by {comment.author.username}',
            comment.id
        )
    
    # Notify admins about comments on important tickets
    if ticket.priority in ['high', 'urgent']:
        admins = User.query.filter_by(role='admin').all()
        for admin in admins:
            if admin.id != comment.user_id:
                create_notification(
                    admin.id,
                    ticket.id,
                    'comment_added',
                    f'New comment on {ticket.priority} priority ticket "{ticket.subject}" by {comment.author.username}',
                    comment.id
                )

# Jinja filter for nl2br
@app.template_filter('nl2br')
def nl2br_filter(text):
    if text:
        return text.replace('\n', '<br>')
    return text

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, agent, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='author', lazy=True, foreign_keys='Ticket.user_id')
    assigned_tickets = db.relationship('Ticket', backref='assigned_agent', lazy=True, foreign_keys='Ticket.assigned_to')
    comments = db.relationship('Comment', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True, order_by='Notification.created_at.desc()')

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tickets = db.relationship('Ticket', backref='category', lazy=True)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    
    # Relationships
    comments = db.relationship('Comment', backref='ticket', lazy=True, order_by='Comment.created_at')
    attachments = db.relationship('Attachment', backref='ticket', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    type = db.Column(db.String(50), nullable=False)  # ticket_created, ticket_updated, comment_added, ticket_assigned, status_changed
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ticket = db.relationship('Ticket', backref='notifications')
    comment = db.relationship('Comment', backref='notifications')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get filter parameters
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    search_query = request.args.get('search', '')
    sort_by = request.args.get('sort', 'updated_at')
    
    # Build query
    query = Ticket.query
    
    if current_user.role == 'user':
        query = query.filter_by(user_id=current_user.id)
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    if search_query:
        query = query.filter(Ticket.subject.contains(search_query) | Ticket.description.contains(search_query))
    
    # Sorting
    if sort_by == 'recent':
        query = query.order_by(Ticket.updated_at.desc())
    elif sort_by == 'priority':
        priority_order = {'urgent': 4, 'high': 3, 'medium': 2, 'low': 1}
        query = query.order_by(db.case(priority_order, value=Ticket.priority).desc())
    else:
        query = query.order_by(Ticket.updated_at.desc())
    
    tickets = query.paginate(page=request.args.get('page', 1, type=int), per_page=10)
    categories = Category.query.all()
    
    return render_template('dashboard.html', tickets=tickets, categories=categories)

@app.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    if request.method == 'POST':
        subject = request.form.get('subject')
        description = request.form.get('description')
        category_id = request.form.get('category_id')
        priority = request.form.get('priority', 'medium')
        
        # Validation
        if not subject or not description or not category_id:
            flash('Please fill in all required fields', 'error')
            categories = Category.query.all()
            return render_template('new_ticket.html', categories=categories)
        
        ticket = Ticket(
            subject=subject,
            description=description,
            category_id=category_id,
            priority=priority,
            user_id=current_user.id
        )
        db.session.add(ticket)
        db.session.commit()
        
        # Handle file uploads
        files = request.files.getlist('attachments')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{ticket.id}_{filename}")
                file.save(file_path)
                
                attachment = Attachment(
                    filename=f"{ticket.id}_{filename}",
                    original_filename=filename,
                    file_path=file_path,
                    ticket_id=ticket.id
                )
                db.session.add(attachment)
        
        db.session.commit()
        
        # Create notifications for new ticket
        notify_ticket_created(ticket)
        
        flash('Ticket created successfully!', 'success')
        return redirect(url_for('ticket_detail', ticket_id=ticket.id))
    
    categories = Category.query.all()
    return render_template('new_ticket.html', categories=categories)

@app.route('/ticket/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check if user has permission to view this ticket
    if current_user.role == 'user' and ticket.user_id != current_user.id:
        flash('You do not have permission to view this ticket', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('ticket_detail.html', ticket=ticket)

@app.route('/ticket/<int:ticket_id>/comment', methods=['POST'])
@login_required
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check if user has permission to comment
    if current_user.role == 'user' and ticket.user_id != current_user.id:
        flash('You do not have permission to comment on this ticket', 'error')
        return redirect(url_for('dashboard'))
    
    content = request.form.get('content')
    if content and content.strip():
        comment = Comment(
            content=content.strip(),
            user_id=current_user.id,
            ticket_id=ticket_id
        )
        db.session.add(comment)
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create notifications for new comment
        notify_comment_added(comment)
        
        flash('Comment added successfully!', 'success')
    else:
        flash('Comment cannot be empty', 'error')
    
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route('/ticket/<int:ticket_id>/update_status', methods=['POST'])
@login_required
def update_ticket_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Only agents and admins can update status
    if current_user.role not in ['agent', 'admin']:
        flash('You do not have permission to update ticket status', 'error')
        return redirect(url_for('ticket_detail', ticket_id=ticket_id))
    
    status = request.form.get('status')
    if status in ['open', 'in_progress', 'resolved', 'closed']:
        old_status = ticket.status
        ticket.status = status
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create notification for status change
        if old_status != status:
            notify_status_changed(ticket, old_status, status)
        
        flash('Ticket status updated successfully!', 'success')
    
    return redirect(url_for('ticket_detail', ticket_id=ticket_id))

@app.route('/ticket/<int:ticket_id>/vote', methods=['POST'])
@login_required
def vote_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    vote_type = request.form.get('vote_type')
    
    if vote_type == 'upvote':
        ticket.upvotes += 1
    elif vote_type == 'downvote':
        ticket.downvotes += 1
    
    db.session.commit()
    return jsonify({'upvotes': ticket.upvotes, 'downvotes': ticket.downvotes})

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Notification routes
@app.route('/notifications')
@login_required
def notifications():
    """View all notifications for current user"""
    page = request.args.get('page', 1, type=int)
    notifications = Notification.query.filter_by(user_id=current_user.id).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('notifications.html', notifications=notifications)

@app.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    notification = Notification.query.get_or_404(notification_id)
    
    # Ensure user can only mark their own notifications as read
    if notification.user_id != current_user.id:
        flash('Access denied', 'error')
        return redirect(url_for('notifications'))
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    flash('All notifications marked as read!', 'success')
    return redirect(url_for('notifications'))

@app.route('/api/notifications/count')
@login_required
def notification_count():
    """Get unread notification count for current user"""
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})

# Admin routes
@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
def admin_new_user():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('admin/new_user.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('admin/new_user.html')
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address', 'error')
            return render_template('admin/new_user.html')
        
        if role not in ['user', 'agent', 'admin']:
            flash('Invalid role selected', 'error')
            return render_template('admin/new_user.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('admin/new_user.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('admin/new_user.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} created successfully as {role}!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/new_user.html')

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        new_password = request.form.get('new_password')
        
        # Validation
        if not username or not email or not role:
            flash('Username, email, and role are required', 'error')
            return render_template('admin/edit_user.html', user=user)
        
        if role not in ['user', 'agent', 'admin']:
            flash('Invalid role selected', 'error')
            return render_template('admin/edit_user.html', user=user)
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address', 'error')
            return render_template('admin/edit_user.html', user=user)
        
        # Check if username/email already exists (excluding current user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user_id:
            flash('Username already exists', 'error')
            return render_template('admin/edit_user.html', user=user)
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            flash('Email already registered', 'error')
            return render_template('admin/edit_user.html', user=user)
        
        # Update user
        user.username = username
        user.email = email
        user.role = role
        
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('admin/edit_user.html', user=user)
            user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        flash(f'User {username} updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('admin_users'))
    
    # Check if user has tickets
    if user.tickets:
        flash('Cannot delete user with existing tickets', 'error')
        return redirect(url_for('admin_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} deleted successfully!', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def admin_categories():
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Category name is required', 'error')
            categories = Category.query.all()
            return render_template('admin/categories.html', categories=categories)
        
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!', 'success')
        return redirect(url_for('admin_categories'))
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/category/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    if current_user.role != 'admin':
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    category = Category.query.get_or_404(category_id)
    
    # Check if category has tickets
    if category.tickets:
        flash('Cannot delete category with existing tickets', 'error')
        return redirect(url_for('admin_categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('admin_categories'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default categories if none exist
        if not Category.query.first():
            default_categories = [
                Category(name='Technical Support', description='Technical issues and problems'),
                Category(name='General Inquiry', description='General questions and information'),
                Category(name='Bug Report', description='Software bugs and issues'),
                Category(name='Feature Request', description='New feature suggestions'),
                Category(name='Account Issues', description='Account-related problems')
            ]
            for category in default_categories:
                db.session.add(category)
            db.session.commit()
        
        # Create admin user if none exists
        if not User.query.filter_by(role='admin').first():
            admin = User(
                username='admin',
                email='admin@quickdesk.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True) 