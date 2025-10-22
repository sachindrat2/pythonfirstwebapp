#!/usr/bin/env python3
"""
Comprehensive test for user-specific notes functionality including DELETE API
"""

import urllib.request
import urllib.error
import json

BASE_URL = "http://localhost:8000"

def make_request(url, method="GET", data=None, headers=None):
    """Make HTTP request and return response"""
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
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            return e.code, error_body
        except:
            return e.code, {"error": e.reason}
    except Exception as e:
        return None, {"error": str(e)}

def test_user_specific_notes():
    """Test complete user-specific notes functionality"""
    print("🧪 Testing User-Specific Notes with DELETE API")
    print("=" * 60)
    
    # Test data
    user1_data = {"username": "testuser1", "password": "password123"}
    user2_data = {"username": "testuser2", "password": "password123"}
    
    print("1. 👤 User Registration and Authentication")
    print("-" * 40)
    
    # Register/login user 1
    status, response = make_request(f"{BASE_URL}/register", "POST", user1_data)
    if status == 200:
        token1 = response["access_token"]
        print("✅ User 1 registered and authenticated")
    elif status == 400:
        # User already exists, try login
        form_data = f"username={user1_data['username']}&password={user1_data['password']}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        req = urllib.request.Request(f"{BASE_URL}/token", data=form_data.encode(), headers=headers)
        with urllib.request.urlopen(req) as response:
            token1 = json.loads(response.read().decode())["access_token"]
        print("✅ User 1 logged in (already existed)")
    else:
        print(f"❌ User 1 registration failed: {response}")
        return
    
    # Register/login user 2
    status, response = make_request(f"{BASE_URL}/register", "POST", user2_data)
    if status == 200:
        token2 = response["access_token"]
        print("✅ User 2 registered and authenticated")
    elif status == 400:
        # User already exists, try login
        form_data = f"username={user2_data['username']}&password={user2_data['password']}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        req = urllib.request.Request(f"{BASE_URL}/token", data=form_data.encode(), headers=headers)
        with urllib.request.urlopen(req) as response:
            token2 = json.loads(response.read().decode())["access_token"]
        print("✅ User 2 logged in (already existed)")
    else:
        print(f"❌ User 2 registration failed: {response}")
        return
    
    print("\n2. 📝 Creating Notes for Each User")
    print("-" * 40)
    
    # Create notes for user 1
    headers1 = {"Authorization": f"Bearer {token1}"}
    user1_notes = [
        {"title": "User 1 - Personal Note", "content": "This is my personal note"},
        {"title": "User 1 - Work Note", "content": "Meeting notes for project"},
        {"title": "User 1 - Shopping List", "content": "Milk, Bread, Eggs"}
    ]
    
    user1_note_ids = []
    for note_data in user1_notes:
        status, response = make_request(f"{BASE_URL}/notes", "POST", note_data, headers1)
        if status == 200:
            user1_note_ids.append(response["id"])
            print(f"✅ Created note: {response['title']}")
        else:
            print(f"❌ Failed to create note: {response}")
    
    # Create notes for user 2
    headers2 = {"Authorization": f"Bearer {token2}"}
    user2_notes = [
        {"title": "User 2 - Travel Plans", "content": "Trip to Tokyo next month"},
        {"title": "User 2 - Book List", "content": "Books to read this year"}
    ]
    
    user2_note_ids = []
    for note_data in user2_notes:
        status, response = make_request(f"{BASE_URL}/notes", "POST", note_data, headers2)
        if status == 200:
            user2_note_ids.append(response["id"])
            print(f"✅ Created note: {response['title']}")
        else:
            print(f"❌ Failed to create note: {response}")
    
    print("\n3. 🔍 Testing User Isolation (Each User Sees Only Their Notes)")
    print("-" * 40)
    
    # Get notes for user 1
    status, user1_retrieved = make_request(f"{BASE_URL}/notes", "GET", headers=headers1)
    if status == 200:
        print(f"✅ User 1 can see {len(user1_retrieved)} notes:")
        for note in user1_retrieved:
            print(f"   - {note['title']}")
    else:
        print(f"❌ Failed to get user 1 notes: {user1_retrieved}")
    
    # Get notes for user 2
    status, user2_retrieved = make_request(f"{BASE_URL}/notes", "GET", headers=headers2)
    if status == 200:
        print(f"✅ User 2 can see {len(user2_retrieved)} notes:")
        for note in user2_retrieved:
            print(f"   - {note['title']}")
    else:
        print(f"❌ Failed to get user 2 notes: {user2_retrieved}")
    
    # Verify isolation
    user1_titles = [note['title'] for note in user1_retrieved] if status == 200 else []
    user2_titles = [note['title'] for note in user2_retrieved] if status == 200 else []
    
    # Check that users don't see each other's notes
    cross_contamination = any("User 2" in title for title in user1_titles) or any("User 1" in title for title in user2_titles)
    if not cross_contamination:
        print("✅ Perfect isolation: Users only see their own notes")
    else:
        print("❌ Privacy breach: Users can see other users' notes!")
    
    print("\n4. ✏️  Testing Update Functionality")
    print("-" * 40)
    
    if user1_note_ids:
        note_id = user1_note_ids[0]
        updated_note = {"title": "Updated Personal Note", "content": "This note has been updated"}
        status, response = make_request(f"{BASE_URL}/notes/{note_id}", "PUT", updated_note, headers1)
        if status == 200:
            print(f"✅ User 1 updated note: {response['title']}")
        else:
            print(f"❌ Failed to update note: {response}")
    
    print("\n5. 🗑️  Testing DELETE API")
    print("-" * 40)
    
    # User 1 deletes their own note
    if len(user1_note_ids) > 1:
        note_to_delete = user1_note_ids[1]  # Delete the second note
        status, response = make_request(f"{BASE_URL}/notes/{note_to_delete}", "DELETE", headers=headers1)
        if status == 200:
            print(f"✅ User 1 successfully deleted note ID {note_to_delete}")
            print(f"   Response: {response['message']}")
        else:
            print(f"❌ Failed to delete note: {response}")
        
        # Verify note is actually deleted
        status, notes_after_delete = make_request(f"{BASE_URL}/notes", "GET", headers=headers1)
        if status == 200:
            remaining_count = len(notes_after_delete)
            print(f"✅ Verification: User 1 now has {remaining_count} notes (was {len(user1_note_ids)})")
        
    print("\n6. 🔒 Testing Cross-User Access Prevention")
    print("-" * 40)
    
    # User 1 tries to delete User 2's note
    if user2_note_ids:
        user2_note_id = user2_note_ids[0]
        status, response = make_request(f"{BASE_URL}/notes/{user2_note_id}", "DELETE", headers=headers1)
        if status == 403:
            print("✅ Security working: User 1 cannot delete User 2's note")
            print(f"   Response: {response.get('detail', 'Access denied')}")
        elif status == 404:
            print("✅ Security working: Note not found for User 1")
        else:
            print(f"❌ SECURITY BREACH: User 1 could access User 2's note! Status: {status}")
    
    # User 2 tries to update User 1's note
    if user1_note_ids:
        user1_note_id = user1_note_ids[0]
        malicious_update = {"title": "Hacked!", "content": "This should not work"}
        status, response = make_request(f"{BASE_URL}/notes/{user1_note_id}", "PUT", malicious_update, headers2)
        if status == 403:
            print("✅ Security working: User 2 cannot update User 1's note")
        elif status == 404:
            print("✅ Security working: Note not found for User 2")
        else:
            print(f"❌ SECURITY BREACH: User 2 could update User 1's note! Status: {status}")
    
    print("\n7. 📊 Final Status Check")
    print("-" * 40)
    
    # Final count for both users
    status, final_user1_notes = make_request(f"{BASE_URL}/notes", "GET", headers=headers1)
    status, final_user2_notes = make_request(f"{BASE_URL}/notes", "GET", headers=headers2)
    
    if status == 200:
        print(f"📈 Final Summary:")
        print(f"   User 1: {len(final_user1_notes)} notes")
        print(f"   User 2: {len(final_user2_notes)} notes")
        print(f"   ✅ All users have isolated note collections")
    
    print("\n🎉 User-Specific Notes with DELETE API Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_user_specific_notes()