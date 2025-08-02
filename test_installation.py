#!/usr/bin/env python3
"""
Quick Installation Test
Tests if the basic packages are installed correctly.
"""

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing package imports...")
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
    except ImportError as e:
        print(f"❌ Flask: {e}")
        return False
    
    try:
        import flask_sqlalchemy
        print("✅ Flask-SQLAlchemy")
    except ImportError as e:
        print(f"❌ Flask-SQLAlchemy: {e}")
        return False
    
    try:
        import flask_login
        print("✅ Flask-Login")
    except ImportError as e:
        print(f"❌ Flask-Login: {e}")
        return False
    
    try:
        import dotenv
        print("✅ python-dotenv")
    except ImportError as e:
        print(f"❌ python-dotenv: {e}")
        return False
    
    return True

def test_flask_app():
    """Test if we can create a basic Flask app with SQLite"""
    print("\n🔍 Testing Flask app creation...")
    
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        
        with app.app_context():
            db.create_all()
            print("✅ Flask app with SQLite created successfully")
            return True
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

def test_sqlite_database():
    """Test SQLite database functionality"""
    print("\n🔍 Testing SQLite database...")
    
    try:
        import sqlite3
        # Test if SQLite is available
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        cursor.execute('INSERT INTO test (name) VALUES (?)', ('test',))
        cursor.execute('SELECT * FROM test')
        result = cursor.fetchone()
        conn.close()
        
        if result and result[1] == 'test':
            print("✅ SQLite database working correctly")
            return True
        else:
            print("❌ SQLite database test failed")
            return False
    except Exception as e:
        print(f"❌ SQLite database test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 QuickDesk Installation Test")
    print("=" * 40)
    
    if test_imports() and test_flask_app() and test_sqlite_database():
        print("\n🎉 Installation successful!")
        print("You can now run: python app.py")
    else:
        print("\n❌ Installation failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main()) 