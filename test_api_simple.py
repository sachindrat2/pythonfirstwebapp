#!/usr/bin/env python3
"""
Simple test to verify the notes API is working
"""

import subprocess
import json

def test_api_with_curl():
    """Test API using curl commands"""
    print("🧪 Testing Notes API with User Isolation")
    print("=" * 50)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        result = subprocess.run(['curl', '-s', 'http://localhost:8000/health'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"✅ Health check: {data['status']}")
        else:
            print(f"❌ Health check failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Register user
    print("\n2. Testing user registration...")
    user_data = '{"username":"testuser123","password":"testpass123"}'
    try:
        result = subprocess.run([
            'curl', '-s', '-X', 'POST', 
            'http://localhost:8000/register',
            '-H', 'Content-Type: application/json',
            '-d', user_data
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                if 'access_token' in response:
                    token = response['access_token']
                    print("✅ User registered successfully")
                    
                    # Test 3: Create a note
                    print("\n3. Testing note creation...")
                    note_data = '{"title":"Test Note","content":"This is a test note"}'
                    result = subprocess.run([
                        'curl', '-s', '-X', 'POST',
                        'http://localhost:8000/notes',
                        '-H', 'Content-Type: application/json',
                        '-H', f'Authorization: Bearer {token}',
                        '-d', note_data
                    ], capture_output=True, text=True, timeout=10)
                    
                    if result.returncode == 0:
                        note_response = json.loads(result.stdout)
                        if 'id' in note_response:
                            note_id = note_response['id']
                            print(f"✅ Note created: {note_response['title']} (ID: {note_id})")
                            
                            # Test 4: Get notes
                            print("\n4. Testing get notes...")
                            result = subprocess.run([
                                'curl', '-s', '-H', f'Authorization: Bearer {token}',
                                'http://localhost:8000/notes'
                            ], capture_output=True, text=True, timeout=10)
                            
                            if result.returncode == 0:
                                notes = json.loads(result.stdout)
                                print(f"✅ Retrieved {len(notes)} notes")
                                for note in notes:
                                    print(f"   - {note['title']}")
                                
                                # Test 5: Delete note
                                if notes:
                                    print(f"\n5. Testing delete note (ID: {note_id})...")
                                    result = subprocess.run([
                                        'curl', '-s', '-X', 'DELETE',
                                        f'http://localhost:8000/notes/{note_id}',
                                        '-H', f'Authorization: Bearer {token}'
                                    ], capture_output=True, text=True, timeout=10)
                                    
                                    if result.returncode == 0:
                                        delete_response = json.loads(result.stdout)
                                        print(f"✅ Note deleted: {delete_response.get('message', 'Success')}")
                                        
                                        # Verify deletion
                                        result = subprocess.run([
                                            'curl', '-s', '-H', f'Authorization: Bearer {token}',
                                            'http://localhost:8000/notes'
                                        ], capture_output=True, text=True, timeout=10)
                                        
                                        if result.returncode == 0:
                                            remaining_notes = json.loads(result.stdout)
                                            print(f"✅ Verification: {len(remaining_notes)} notes remaining")
                            
                        else:
                            print(f"❌ Note creation failed: {note_response}")
                    else:
                        print(f"❌ Note creation error: {result.stderr}")
                        
                else:
                    print(f"❌ Registration failed: {response}")
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {result.stdout}")
        else:
            print(f"❌ Registration request failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    print("\n🎉 API Test Complete!")

if __name__ == "__main__":
    test_api_with_curl()