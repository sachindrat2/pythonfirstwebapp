#!/usr/bin/env python3
"""
Test script to verify that notes are properly created and retrieved per user.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_user_notes():
    print("Testing user-specific notes functionality...")
    
    # Test data
    user1_data = {"username": "testuser1", "password": "password123"}
    user2_data = {"username": "testuser2", "password": "password123"}
    
    print("\n1. Testing user registration and authentication...")
    
    # Register two test users
    try:
        response1 = requests.post(f"{BASE_URL}/register", json=user1_data)
        print(f"User 1 registration: {response1.status_code}")
        if response1.status_code == 200:
            token1 = response1.json()["access_token"]
            print("✓ User 1 registered successfully")
        else:
            print(f"✗ User 1 registration failed: {response1.text}")
            return
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to server. Make sure the app is running on localhost:8000")
        return
    
    try:
        response2 = requests.post(f"{BASE_URL}/register", json=user2_data)
        print(f"User 2 registration: {response2.status_code}")
        if response2.status_code == 200:
            token2 = response2.json()["access_token"]
            print("✓ User 2 registered successfully")
        else:
            print(f"✗ User 2 registration failed: {response2.text}")
            return
    except Exception as e:
        print(f"✗ Error registering user 2: {e}")
        return
    
    print("\n2. Testing note creation per user...")
    
    # Create notes for user 1
    headers1 = {"Authorization": f"Bearer {token1}", "Content-Type": "application/json"}
    note1_data = {"title": "User 1 Note 1", "content": "This is user 1's first note"}
    note2_data = {"title": "User 1 Note 2", "content": "This is user 1's second note"}
    
    response = requests.post(f"{BASE_URL}/notes", json=note1_data, headers=headers1)
    print(f"User 1 note 1 creation: {response.status_code}")
    if response.status_code == 200:
        print("✓ User 1 note 1 created successfully")
    else:
        print(f"✗ Failed to create note for user 1: {response.text}")
    
    response = requests.post(f"{BASE_URL}/notes", json=note2_data, headers=headers1)
    print(f"User 1 note 2 creation: {response.status_code}")
    
    # Create notes for user 2
    headers2 = {"Authorization": f"Bearer {token2}", "Content-Type": "application/json"}
    note3_data = {"title": "User 2 Note 1", "content": "This is user 2's first note"}
    note4_data = {"title": "User 2 Note 2", "content": "This is user 2's second note"}
    
    response = requests.post(f"{BASE_URL}/notes", json=note3_data, headers=headers2)
    print(f"User 2 note 1 creation: {response.status_code}")
    if response.status_code == 200:
        print("✓ User 2 note 1 created successfully")
    else:
        print(f"✗ Failed to create note for user 2: {response.text}")
    
    response = requests.post(f"{BASE_URL}/notes", json=note4_data, headers=headers2)
    print(f"User 2 note 2 creation: {response.status_code}")
    
    print("\n3. Testing note retrieval per user...")
    
    # Get notes for user 1
    response = requests.get(f"{BASE_URL}/notes", headers=headers1)
    print(f"User 1 notes retrieval: {response.status_code}")
    if response.status_code == 200:
        user1_notes = response.json()
        print(f"✓ User 1 has {len(user1_notes)} notes")
        for note in user1_notes:
            print(f"   - {note['title']}: {note['content']}")
    else:
        print(f"✗ Failed to get notes for user 1: {response.text}")
    
    # Get notes for user 2
    response = requests.get(f"{BASE_URL}/notes", headers=headers2)
    print(f"User 2 notes retrieval: {response.status_code}")
    if response.status_code == 200:
        user2_notes = response.json()
        print(f"✓ User 2 has {len(user2_notes)} notes")
        for note in user2_notes:
            print(f"   - {note['title']}: {note['content']}")
    else:
        print(f"✗ Failed to get notes for user 2: {response.text}")
    
    print("\n4. Testing cross-user access restriction...")
    
    # Try to access user 2's notes with user 1's token (should be isolated)
    if len(user1_notes) > 0 and len(user2_notes) > 0:
        user1_note_titles = [note['title'] for note in user1_notes]
        user2_note_titles = [note['title'] for note in user2_notes]
        
        # Check if notes are properly isolated
        if "User 2 Note 1" not in user1_note_titles and "User 1 Note 1" not in user2_note_titles:
            print("✓ Notes are properly isolated between users")
        else:
            print("✗ Notes are NOT properly isolated between users")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_user_notes()