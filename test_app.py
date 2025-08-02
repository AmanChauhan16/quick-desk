#!/usr/bin/env python3
"""
QuickDesk Test Script
This script tests the basic functionality of the QuickDesk application.
"""

import os
import sys
import requests
from datetime import datetime

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        from app import db, User, Category
        with app.app_context():
            # Test if we can query the database
            user_count = User.query.count()
            category_count = Category.query.count()
            print(f"✅ Database connection successful!")
            print(f"   - Users: {user_count}")
            print(f"   - Categories: {category_count}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    print("\n🔍 Testing file structure...")
    required_files = [
        'app.py',
        'requirements.txt',
        'config.py',
        'templates/base.html',
        'templates/index.html',
        'templates/login.html',
        'templates/register.html',
        'templates/dashboard.html',
        'templates/new_ticket.html',
        'templates/ticket_detail.html',
        'templates/admin/users.html',
        'templates/admin/categories.html',
        'templates/errors/404.html',
        'templates/errors/500.html'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist!")
        return True

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("\n🔍 Testing dependencies...")
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'werkzeug',
        'pymysql',
        'dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {missing_packages}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies are installed!")
        return True

def test_environment():
    """Test environment configuration"""
    print("\n🔍 Testing environment configuration...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file exists")
    else:
        print("⚠️  .env file not found - using default configuration")
    
    # Check uploads directory
    if os.path.exists('uploads'):
        print("✅ uploads directory exists")
    else:
        print("⚠️  uploads directory not found - will be created on startup")
    
    return True

def test_flask_app():
    """Test Flask application startup"""
    print("\n🔍 Testing Flask application...")
    try:
        from app import app, db
        
        with app.app_context():
            # Test database creation
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Test if admin user exists
            from app import User
            admin_user = User.query.filter_by(role='admin').first()
            if admin_user:
                print(f"✅ Admin user exists: {admin_user.username}")
            else:
                print("⚠️  No admin user found - will be created on startup")
            
            return True
    except Exception as e:
        print(f"❌ Flask application test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 QuickDesk Application Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies),
        ("Environment", test_environment),
        ("Flask App", test_flask_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nNext steps:")
        print("1. Make sure your SQLite database is running")
        print("2. Run: python app.py")
        print("3. Open: http://localhost:5000")
        print("4. Login with: admin / admin123")
    else:
        print("❌ Some tests failed. Please fix the issues before running the application.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 