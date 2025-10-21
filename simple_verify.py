#!/usr/bin/env python3
"""
Simple script to verify the database schema and test user-note associations directly.
"""

import sqlite3
import hashlib

def hash_password_simple(password):
    """Simple password hashing for testing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_database_schema():
    """Verify that the database schema is correct."""
    print("Verifying database schema...")
    
    # Check the schema
    conn = sqlite3.connect("notes_app.db")
    cursor = conn.cursor()
    
    # Check users table
    cursor.execute("PRAGMA table_info(users)")
    users_columns = cursor.fetchall()
    print("\nUsers table schema:")
    for col in users_columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Check notes table
    cursor.execute("PRAGMA table_info(notes)")
    notes_columns = cursor.fetchall()
    print("\nNotes table schema:")
    for col in notes_columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Verify user_id column exists in notes
    notes_column_names = [col[1] for col in notes_columns]
    if "user_id" in notes_column_names:
        print("✓ user_id column exists in notes table")
        schema_ok = True
    else:
        print("✗ user_id column missing in notes table")
        schema_ok = False
    
    conn.close()
    return schema_ok

def test_user_note_association():
    """Test creating users and notes and verify associations."""
    print("\nTesting user-note associations...")
    
    conn = sqlite3.connect("notes_app.db")
    cursor = conn.cursor()
    
    # Create test users if they don't exist
    try:
        cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
                       ("testuser1", hash_password_simple("password123"), 0))
        cursor.execute("INSERT OR IGNORE INTO users (username, password, is_admin) VALUES (?, ?, ?)", 
                       ("testuser2", hash_password_simple("password123"), 0))
        conn.commit()
        
        # Get user IDs
        cursor.execute("SELECT id FROM users WHERE username = ?", ("testuser1",))
        user1_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM users WHERE username = ?", ("testuser2",))
        user2_id = cursor.fetchone()[0]
        
        print(f"✓ Test users: user1_id={user1_id}, user2_id={user2_id}")
        
        # Create test notes
        cursor.execute("INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)", 
                       ("User 1 Test Note", "Content for user 1", user1_id))
        cursor.execute("INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)", 
                       ("User 2 Test Note", "Content for user 2", user2_id))
        cursor.execute("INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)", 
                       ("Another User 1 Note", "More content for user 1", user1_id))
        conn.commit()
        
        print("✓ Created test notes")
        
        # Test getting notes by user
        cursor.execute("SELECT id, title, content, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user1_id,))
        user1_notes = cursor.fetchall()
        
        cursor.execute("SELECT id, title, content, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user2_id,))
        user2_notes = cursor.fetchall()
        
        print(f"✓ User 1 has {len(user1_notes)} notes:")
        for note in user1_notes:
            print(f"   - {note[1]}: {note[2]}")
        
        print(f"✓ User 2 has {len(user2_notes)} notes:")
        for note in user2_notes:
            print(f"   - {note[1]}: {note[2]}")
        
        # Verify isolation
        user1_titles = [note[1] for note in user1_notes]
        user2_titles = [note[1] for note in user2_notes]
        
        if "User 2 Test Note" not in user1_titles and "User 1 Test Note" not in user2_titles:
            print("✓ Notes are properly isolated between users")
        else:
            print("✗ Notes are NOT properly isolated between users")
            
    except Exception as e:
        print(f"✗ Error during test: {e}")
    finally:
        conn.close()

def check_existing_data():
    """Check what data currently exists in the database."""
    print("\nChecking existing data in database...")
    
    conn = sqlite3.connect("notes_app.db")
    cursor = conn.cursor()
    
    # Check users
    cursor.execute("SELECT id, username, is_admin FROM users")
    users = cursor.fetchall()
    print(f"Users in database: {len(users)}")
    for user in users:
        print(f"  ID: {user[0]}, Username: {user[1]}, Admin: {user[2]}")
    
    # Check notes with user association
    cursor.execute("SELECT n.id, n.title, n.user_id, u.username FROM notes n LEFT JOIN users u ON n.user_id = u.id")
    notes = cursor.fetchall()
    print(f"Notes in database: {len(notes)}")
    for note in notes:
        print(f"  ID: {note[0]}, Title: {note[1]}, User ID: {note[2]}, Username: {note[3]}")
    
    conn.close()

if __name__ == "__main__":
    print("=== Database Schema and User-Note Association Test ===")
    
    # Check existing data first
    check_existing_data()
    
    # Verify schema
    schema_ok = verify_database_schema()
    
    if schema_ok:
        # Test user-note associations
        test_user_note_association()
        
        # Check data after test
        check_existing_data()
    else:
        print("\n✗ Schema verification failed. Please check the database migration.")
    
    print("\n=== Test Complete ===")