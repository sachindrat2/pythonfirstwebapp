#!/usr/bin/env python3
"""
Quick Admin User Creator - Compatible with new hashing system
"""
import sqlite3
import hashlib

DB_NAME = "notes_app.db"

def hash_password_simple(password: str) -> str:
    """Simple SHA-256 hash for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_simple_admin():
    """Create a simple admin user with known credentials"""
    username = "admin"
    password = "admin123"
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Delete existing admin user if exists
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    
    # Create new admin user with simple hash
    hashed_password = hash_password_simple(password)
    cursor.execute(
        "INSERT INTO users (username, password, is_admin) VALUES (?, ?, 1)",
        (username, hashed_password)
    )
    conn.commit()
    conn.close()
    
    print("✅ Simple admin user created!")
    print(f"Username: {username}")
    print(f"Password: {password}")
    print("URL: http://localhost:8000/admin/login")

if __name__ == "__main__":
    create_simple_admin()