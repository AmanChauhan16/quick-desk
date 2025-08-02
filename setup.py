#!/usr/bin/env python3
"""
QuickDesk Setup Script
This script helps you set up the QuickDesk application with proper configuration.
"""

import os
import sys
import getpass
from pathlib import Path

def create_env_file():
    """Create a .env file with user input"""
    print("=== QuickDesk Setup ===")
    print("This script will help you create a .env file with proper configuration.")
    print()
    
    # Check if .env already exists
    if os.path.exists('.env'):
        response = input("A .env file already exists. Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    # Get Flask secret key
    print("\n=== Flask Configuration ===")
    secret_key = input("Flask secret key (press Enter for auto-generated): ").strip()
    if not secret_key:
        import secrets
        secret_key = secrets.token_hex(32)
    
    # Email configuration (optional)
    print("\n=== Email Configuration (Optional) ===")
    use_email = input("Do you want to configure email notifications? (y/N): ").lower() == 'y'
    
    email_config = ""
    if use_email:
        mail_server = input("SMTP server (default: smtp.gmail.com): ").strip() or "smtp.gmail.com"
        mail_port = input("SMTP port (default: 587): ").strip() or "587"
        mail_username = input("Email username: ").strip()
        mail_password = getpass.getpass("Email password/app password: ")
        
        email_config = f"""
# Email Configuration
MAIL_SERVER={mail_server}
MAIL_PORT={mail_port}
MAIL_USE_TLS=True
MAIL_USERNAME={mail_username}
MAIL_PASSWORD={mail_password}"""
    
    # Create .env file
    env_content = f"""# Flask Configuration
SECRET_KEY={secret_key}
FLASK_ENV=development
FLASK_DEBUG=1

# Database Configuration (SQLite - no setup required!)
DATABASE_URL=sqlite:///quickdesk.db{email_config}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ .env file created successfully!")
    print(f"📁 Location: {os.path.abspath('.env')}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n=== Checking Dependencies ===")
    
    required_packages = [
        'flask',
        'flask-sqlalchemy',
        'flask-login',
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
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies are installed!")
        return True

def create_upload_directory():
    """Create uploads directory if it doesn't exist"""
    upload_dir = Path('uploads')
    if not upload_dir.exists():
        upload_dir.mkdir()
        print("✅ Created uploads directory")
    else:
        print("✅ Uploads directory already exists")

def main():
    """Main setup function"""
    print("🚀 QuickDesk Setup Script")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies before continuing.")
        sys.exit(1)
    
    # Create upload directory
    create_upload_directory()
    
    # Create .env file
    create_env_file()
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run the application:")
    print("   python app.py")
    print("2. Open your browser and go to: http://localhost:5000")
    print("3. Login with default admin account:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\nFor more information, see the README.md file.")

if __name__ == '__main__':
    main() 