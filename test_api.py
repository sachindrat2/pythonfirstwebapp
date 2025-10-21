#!/usr/bin/env python3
"""
Test script to verify user-specific notes functionality via API.
"""

import json
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = "http://localhost:8000"

def make_request(url, method="GET", data=None, headers=None):
    """Make HTTP request and return response."""
    if headers is None:
        headers = {}
    
    if data is not None:
        data = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode(), json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.reason}
    except Exception as e:
        return None, {"error": str(e)}

def test_user_notes_api():
    """Test the user-specific notes functionality via API."""
    print("Testing user-specific notes functionality via API...")
    
    # Test data
    user1_data = {"username": "apitest1", "password": "password123"}
    user2_data = {"username": "apitest2", "password": "password123"}
    
    print("\n1. Testing user registration...")
    
    # Register two test users
    status1, response1 = make_request(f"{BASE_URL}/register", "POST", user1_data)
    print(f"User 1 registration: {status1}")
    
    if status1 == 200:
        token1 = response1["access_token"]
        print("✓ User 1 registered successfully")
    else:
        print(f"✗ User 1 registration failed: {response1}")
        return
    
    status2, response2 = make_request(f"{BASE_URL}/register", "POST", user2_data)
    print(f"User 2 registration: {status2}")
    
    if status2 == 200:
        token2 = response2["access_token"]
        print("✓ User 2 registered successfully")
    else:
        print(f"✗ User 2 registration failed: {response2}")
        return
    
    print("\n2. Testing note creation per user...")
    
    # Create notes for user 1
    headers1 = {"Authorization": f"Bearer {token1}"}
    note1_data = {"title": "API User 1 Note 1", "content": "Content for API user 1's first note"}
    note2_data = {"title": "API User 1 Note 2", "content": "Content for API user 1's second note"}
    
    status, response = make_request(f"{BASE_URL}/notes", "POST", note1_data, headers1)
    print(f"User 1 note 1 creation: {status}")
    if status == 200:
        print("✓ User 1 note 1 created successfully")
        print(f"   Note ID: {response['id']}, Title: {response['title']}")
    else:
        print(f"✗ Failed to create note for user 1: {response}")
    
    status, response = make_request(f"{BASE_URL}/notes", "POST", note2_data, headers1)
    print(f"User 1 note 2 creation: {status}")
    
    # Create notes for user 2
    headers2 = {"Authorization": f"Bearer {token2}"}
    note3_data = {"title": "API User 2 Note 1", "content": "Content for API user 2's first note"}
    note4_data = {"title": "API User 2 Note 2", "content": "Content for API user 2's second note"}
    
    status, response = make_request(f"{BASE_URL}/notes", "POST", note3_data, headers2)
    print(f"User 2 note 1 creation: {status}")
    if status == 200:
        print("✓ User 2 note 1 created successfully")
        print(f"   Note ID: {response['id']}, Title: {response['title']}")
    else:
        print(f"✗ Failed to create note for user 2: {response}")
    
    status, response = make_request(f"{BASE_URL}/notes", "POST", note4_data, headers2)
    print(f"User 2 note 2 creation: {status}")
    
    print("\n3. Testing note retrieval per user...")
    
    # Get notes for user 1
    status, user1_notes = make_request(f"{BASE_URL}/notes", "GET", headers=headers1)
    print(f"User 1 notes retrieval: {status}")
    if status == 200:
        print(f"✓ User 1 has {len(user1_notes)} notes")
        for note in user1_notes:
            print(f"   - ID: {note['id']}, Title: {note['title']}")
    else:
        print(f"✗ Failed to get notes for user 1: {user1_notes}")
    
    # Get notes for user 2
    status, user2_notes = make_request(f"{BASE_URL}/notes", "GET", headers=headers2)
    print(f"User 2 notes retrieval: {status}")
    if status == 200:
        print(f"✓ User 2 has {len(user2_notes)} notes")
        for note in user2_notes:
            print(f"   - ID: {note['id']}, Title: {note['title']}")
    else:
        print(f"✗ Failed to get notes for user 2: {user2_notes}")
    
    print("\n4. Testing note isolation between users...")
    
    if status == 200 and len(user1_notes) > 0 and len(user2_notes) > 0:
        user1_titles = [note['title'] for note in user1_notes]
        user2_titles = [note['title'] for note in user2_notes]
        
        # Check if notes are properly isolated
        if ("API User 2 Note 1" not in user1_titles and 
            "API User 1 Note 1" not in user2_titles):
            print("✓ Notes are properly isolated between users")
        else:
            print("✗ Notes are NOT properly isolated between users")
            print(f"   User 1 titles: {user1_titles}")
            print(f"   User 2 titles: {user2_titles}")
    
    print("\n5. Testing unauthorized access...")
    
    # Try to get notes without token
    status, response = make_request(f"{BASE_URL}/notes", "GET")
    if status == 401:
        print("✓ Unauthorized access properly blocked")
    else:
        print(f"✗ Unauthorized access not blocked: {status} - {response}")
    
    print("\nAPI Test completed!")

if __name__ == "__main__":
    test_user_notes_api()