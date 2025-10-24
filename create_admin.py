#!/usr/bin/env python3
"""
Admin User Management Script
Creates or checks admin users for the Notes App
"""
import sqlite3
from passlib.context import CryptContext

DB_NAME = "notes_app.db"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(username, password):
    """Create a new admin user"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        print(f"User '{username}' already exists!")
        conn.close()
        return False
    
    # Hash password and create user
    hashed_password = pwd_context.hash(password)
    cursor.execute(
        "INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)",
        (username, hashed_password)
    )
    conn.commit()
    conn.close()
    print(f"Admin user '{username}' created successfully!")
    return True

def list_users():
    """List all users in the database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, is_admin FROM users")
    users = cursor.fetchall()
    conn.close()
    
    if not users:
        print("No users found in database.")
        return []
    
    print("\nExisting users:")
    print("-" * 40)
    for user in users:
        role = "Admin" if user[2] else "User"
        print(f"ID: {user[0]}, Username: {user[1]}, Role: {role}")
    print("-" * 40)
    return users

def main():
    print("=== Admin User Management ===")
    
    # List existing users
    users = list_users()
    
    # Check if any admin users exist
    admin_users = [u for u in users if u[2] == 1]
    
    if not admin_users:
        print("\n⚠️  No admin users found!")
        print("Creating default admin user...")
        
        # Create default admin user
        default_username = "admin"
        default_password = "admin123"
        
        if create_admin_user(default_username, default_password):
            print(f"\n✅ Default admin credentials:")
            print(f"Username: {default_username}")
            print(f"Password: {default_password}")
            print("\n🔒 Please change this password after first login!")
    else:
        print(f"\n✅ Found {len(admin_users)} admin user(s):")
        for admin in admin_users:
            print(f"   - {admin[1]} (ID: {admin[0]})")
        
        print("\n💡 If you forgot the password, you can reset it by:")
        print("   1. Deleting the user from database")  
        print("   2. Running this script again to create new admin")

if __name__ == "__main__":
    main()