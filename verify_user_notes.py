#!/usr/bin/env python3
"""
Script to verify the database schema and test user-note associations directly.
"""

import sqlite3
import sys
import os

# Add current directory to path
sys.path.append('.')

from database import create_database, create_user, create_note, get_notes, get_note
from main import hash_password

def verify_database_schema():
    """Verify that the database schema is correct."""
    print("Verifying database schema...")
    
    # Ensure database exists
    create_database()
    
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
    else:
        print("✗ user_id column missing in notes table")
        return False
    
    conn.close()
    return True

def test_user_note_association():
    """Test creating users and notes and verify associations."""
    print("\nTesting user-note associations...")
    
    # Create test users
    try:
        user1_id = create_user("testuser1", hash_password("password123"))
        user2_id = create_user("testuser2", hash_password("password123"))
        
        if user1_id and user2_id:
            print(f"✓ Created users: user1_id={user1_id}, user2_id={user2_id}")
        else:
            print("✗ Failed to create test users (may already exist)")
            # Try to get existing users
            conn = sqlite3.connect("notes_app.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", ("testuser1",))
            result = cursor.fetchone()
            user1_id = result[0] if result else None
            cursor.execute("SELECT id FROM users WHERE username = ?", ("testuser2",))
            result = cursor.fetchone()
            user2_id = result[0] if result else None
            conn.close()
            
            if user1_id and user2_id:
                print(f"✓ Found existing users: user1_id={user1_id}, user2_id={user2_id}")
    
    except Exception as e:
        print(f"✗ Error creating users: {e}")
        return
    
    # Create notes for each user
    try:
        note1 = create_note("User 1 Note", "Content for user 1", user1_id)
        note2 = create_note("User 2 Note", "Content for user 2", user2_id)
        note3 = create_note("Another User 1 Note", "More content for user 1", user1_id)
        
        print(f"✓ Created notes: {note1[0]}, {note2[0]}, {note3[0]}")
    except Exception as e:
        print(f"✗ Error creating notes: {e}")
        return
    
    # Test getting notes by user
    try:
        user1_notes = get_notes(user1_id)
        user2_notes = get_notes(user2_id)
        
        print(f"✓ User 1 has {len(user1_notes)} notes")
        for note in user1_notes:
            print(f"   - {note[1]}: {note[2]}")
        
        print(f"✓ User 2 has {len(user2_notes)} notes")
        for note in user2_notes:
            print(f"   - {note[1]}: {note[2]}")
        
        # Verify isolation
        user1_titles = [note[1] for note in user1_notes]
        user2_titles = [note[1] for note in user2_notes]
        
        if "User 2 Note" not in user1_titles and "User 1 Note" not in user2_titles:
            print("✓ Notes are properly isolated between users")
        else:
            print("✗ Notes are NOT properly isolated between users")
    
    except Exception as e:
        print(f"✗ Error retrieving notes: {e}")

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
    
    # Check notes
    cursor.execute("SELECT id, title, user_id FROM notes")
    notes = cursor.fetchall()
    print(f"Notes in database: {len(notes)}")
    for note in notes:
        print(f"  ID: {note[0]}, Title: {note[1]}, User ID: {note[2]}")
    
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
    
    print("\n=== Test Complete ===")