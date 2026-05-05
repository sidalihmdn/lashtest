"""
Real-world API test examples using net-test library
Tests against public APIs: JSONPlaceholder and HTTPBin
"""

from lashtest import Client
from lashtest.http import BasicAuth, BearerToken, APIKey


def test_jsonplaceholder_crud():
    """Test CRUD operations on JSONPlaceholder API"""
    print("\n=== Testing JSONPlaceholder CRUD Operations ===\n")
    
    client = Client('https://jsonplaceholder.typicode.com') \
        .with_header('User-Agent', 'net-test/1.0')
    
    # 1. GET - Retrieve a user
    print("1. GET /users/1")
    with client.get('/users/1') as response:
        response.assert_status(200) \
                .assert_ok() \
                .assert_header('Content-Type', 'application/json; charset=utf-8') \
                .assert_json_contains({'id': 1}) \
                .assert_response_time(2.0)
        
        user = response.json()
        print(f"   ✓ Retrieved user: {user['name']}")
        print(f"   ✓ Response time: {response.elapsed:.3f}s")
    
    # 2. GET with query parameters - Search posts by user
    print("\n2. GET /posts?userId=1")
    with client.get('/posts').with_params({'userId': 1}) as response:
        response.assert_status(200) \
                .assert_ok()
        
        posts = response.json()
        print(f"   ✓ Found {len(posts)} posts by user 1")
        assert len(posts) > 0, "User should have posts"
    
    # 3. POST - Create a new post
    print("\n3. POST /posts")
    new_post = {
        'title': 'Test Post from net-test',
        'body': 'This is a test post created by the net-test library',
        'userId': 1
    }
    
    with client.post('/posts').with_body(new_post) as response:
        response.assert_status(201) \
                .assert_json_contains({'userId': 1, 'title': 'Test Post from net-test'})
        
        created_post = response.json()
        post_id = created_post['id']
        print(f"   ✓ Created post with ID: {post_id}")
    
    # 4. PUT - Update the post
    print("\n4. PUT /posts/1")
    updated_post = {
        'id': 1,
        'title': 'Updated Title',
        'body': 'Updated content',
        'userId': 1
    }
    
    with client.put('/posts/1').with_body(updated_post) as response:
        response.assert_status(200) \
                .assert_json_contains({'title': 'Updated Title'})
        
        print("   ✓ Post updated successfully")
    
    # 5. PATCH - Partially update
    print("\n5. PATCH /posts/1")
    with client.patch('/posts/1').with_body({'title': 'Patched Title'}) as response:
        response.assert_status(200)
        print("   ✓ Post patched successfully")
    
    # 6. DELETE - Remove the post
    print("\n6. DELETE /posts/1")
    with client.delete('/posts/1') as response:
        response.assert_status(200)
        print("   ✓ Post deleted successfully")
    
    print("\n✅ All CRUD operations passed!")


def test_httpbin_authentication():
    """Test different authentication methods using HTTPBin"""
    print("\n=== Testing Authentication Methods ===\n")
    
    # 1. Basic Authentication
    print("1. Basic Authentication")
    client = Client('https://httpbin.org')
    
    with client.get('/basic-auth/user/passwd') \
        .with_auth(BasicAuth('user', 'passwd')) as response:
        response.assert_status(200) \
                .assert_json_contains({'authenticated': True, 'user': 'user'})
        print("   ✓ Basic auth successful")
    
    # 2. Bearer Token (simulated)
    print("\n2. Bearer Token")
    with client.get('/bearer') \
        .with_auth(BearerToken('test-token-123')) as response:
        response.assert_status(200) \
                .assert_json_contains({'authenticated': True, 'token': 'test-token-123'})
        print("   ✓ Bearer token auth successful")
    
    print("\n✅ All authentication tests passed!")


def test_httpbin_headers():
    """Test header handling"""
    print("\n=== Testing Headers ===\n")
    
    client = Client('https://httpbin.org')
    
    # Test custom headers
    print("1. Custom headers")
    with client.get('/headers') \
        .with_header('X-Custom-Header', 'CustomValue') \
        .with_header('X-Test-ID', '12345') as response:
        
        response.assert_status(200)
        headers_received = response.json()['headers']
        
        assert 'X-Custom-Header' in headers_received
        assert 'X-Test-Id' in headers_received  # HTTPBin normalizes headers
        print(f"   ✓ Custom headers sent and verified")
    
    # Test user agent
    print("\n2. User-Agent header")
    custom_client = Client('https://httpbin.org') \
        .with_header('User-Agent', 'MyTestBot/2.0')
    
    with custom_client.get('/user-agent') as response:
        response.assert_status(200)
        ua = response.json()['user-agent']
        assert 'MyTestBot/2.0' in ua
        print(f"   ✓ User-Agent: {ua}")
    
    print("\n✅ All header tests passed!")


def test_httpbin_request_data():
    """Test sending different types of data"""
    print("\n=== Testing Request Data ===\n")
    
    client = Client('https://httpbin.org')
    
    # 1. JSON data
    print("1. JSON data")
    json_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'age': 30,
        'active': True
    }
    
    with client.post('/post').with_body(json_data) as response:
        response.assert_status(200)
        received = response.json()['json']
        assert received == json_data
        print("   ✓ JSON data sent and echoed correctly")
    
    # 2. Form data
    print("\n2. Form data")
    form_data = {
        'username': 'testuser',
        'password': 'secret123'
    }
    
    with client.post('/post').with_data(form_data) as response:
        response.assert_status(200)
        received = response.json()['form']
        assert received == form_data
        print("   ✓ Form data sent correctly")
    
    print("\n✅ All request data tests passed!")


def test_httpbin_response_types():
    """Test different response types and status codes"""
    print("\n=== Testing Response Types ===\n")
    
    client = Client('https://httpbin.org')
    
    # 1. JSON response
    print("1. JSON response")
    with client.get('/json') as response:
        response.assert_status(200) \
                .assert_ok()
        json_data = response.json()
        assert isinstance(json_data, dict)
        print("   ✓ JSON response parsed")
    
    # 2. HTML response
    print("\n2. HTML response")
    with client.get('/html') as response:
        response.assert_status(200)
        html = response.text
        assert '<html>' in html.lower()
        print("   ✓ HTML response received")
    
    # 3. Different status codes
    print("\n3. Testing status codes")
    test_codes = [200, 201, 400, 404, 500]
    
    for code in test_codes:
        with client.get(f'/status/{code}') as response:
            response.assert_status(code)
            print(f"   ✓ Status {code} verified")
    
    print("\n✅ All response type tests passed!")


def test_performance():
    """Test response time tracking"""
    print("\n=== Testing Performance Tracking ===\n")
    
    client = Client('https://httpbin.org')
    
    # Test delay endpoint
    print("1. Testing 1-second delay")
    with client.get('/delay/1') as response:
        response.assert_status(200)
        elapsed = response.elapsed
        print(f"   ✓ Request took {elapsed:.3f}s")
        
        # Should be roughly 1 second (allow some tolerance)
        response.assert_response_time(2.0)  # Should be under 2 seconds
    # Test response time assertion
    print("\n2. Testing response time assertion")
    with client.get('/delay/0') as response:
        response.assert_response_time(2.0)  # Should be under 2 seconds
        print(f"   ✓ Response time assertion passed ({response.elapsed:.3f}s)")
    
    print("\n✅ Performance tests passed!")


def test_advanced_scenarios():
    """Test advanced real-world scenarios"""
    print("\n=== Testing Advanced Scenarios ===\n")
    
    client = Client('https://httpbin.org')
    
    # 1. Multiple requests with shared client
    print("1. Multiple requests with shared configuration")
    api_client = Client('https://httpbin.org') \
        .with_header('X-API-Version', 'v1') \
        .with_header('X-Client-ID', 'test-client-123') \
        .with_timeout(10)
    
    endpoints = ['/get', '/status/200', '/headers']
    for endpoint in endpoints:
        with api_client.get(endpoint) as response:
            response.assert_ok()
        print(f"   ✓ {endpoint} successful")
    
    # 2. Override client defaults per request
    print("\n2. Per-request header override")
    with api_client.get('/headers') \
        .with_header('X-Request-Specific', 'override-value') as response:
        
        response.assert_status(200)
        headers = response.json()['headers']
        assert 'X-Request-Specific' in headers
        print("   ✓ Request-specific header added")
    
    # 3. Chain multiple assertions
    print("\n3. Chained assertions")
    with client.get('/get').with_params({'test': 'value'}) as response:
        response.assert_status(200) \
                .assert_ok() \
                .assert_header('Content-Type', 'application/json') \
                .assert_response_time(3.0)
        print("   ✓ All chained assertions passed")
    
    print("\n✅ Advanced scenario tests passed!")


def test_error_handling():
    """Test error scenarios"""
    print("\n=== Testing Error Handling ===\n")
    
    client = Client('https://httpbin.org')
    
    # 1. 404 Not Found
    print("1. Testing 404 response")
    with client.get('/status/404') as response:
        response.assert_status(404)
        print("   ✓ 404 handled correctly")
    
    # 2. 500 Server Error
    print("\n2. Testing 500 response")
    with client.get('/status/500') as response:
        response.assert_status(500)
        print("   ✓ 500 handled correctly")
    
    # 3. Invalid JSON
    print("\n3. Testing HTML response (not JSON)")
    with client.get('/html') as response:
        response.assert_status(200)
        try:
            json_data = response.json()
            if json_data is None:
                print("   ✓ Invalid JSON returns None (expected)")
        except:
            print("   ✓ Invalid JSON handled")
    
    print("\n✅ Error handling tests passed!")


def test_context_manager():
    """Test context manager functionality"""
    print("\n=== Testing Context Manager ===\n")
    
    print("1. Using client context manager")
    with Client('https://httpbin.org') as client:
        with client.get('/get') as response:
            response.assert_status(200)
        print("   ✓ Client context manager works")
    
    print("\n2. Request context manager (current usage)")
    client = Client('https://httpbin.org')
    with client.get('/status/200') as response:
        response.assert_ok()
    print("   ✓ Request context manager works")
    
    print("\n✅ Context manager tests passed!")


if __name__ == '__main__':
    """Run all tests"""
    print("=" * 60)
    print("RUNNING REAL-WORLD API TESTS")
    print("=" * 60)
    
    try:
        test_jsonplaceholder_crud()
        test_httpbin_authentication()
        test_httpbin_headers()
        test_httpbin_request_data()
        test_httpbin_response_types()
        test_performance()
        test_advanced_scenarios()
        test_error_handling()
        test_context_manager()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise
