"""
Pytest-style tests for net-test library
Run with: pytest tests/test_api_client.py -v
"""

import pytest
from lashtest import APIClient as Client
from lashtest.http import BasicAuth, BearerToken
from lashtest.decorators import authenticated


class TestJSONPlaceholderAPI:
    """Test suite for JSONPlaceholder API operations"""

    @pytest.fixture
    def client(self):
        """Create a client instance for each test"""
        return Client('https://jsonplaceholder.typicode.com').with_header("User-Agent", "lashtest-jsonplaceholder-tests/1.0")

    def test_get_single_user(self, client : Client):
        """Test retrieving a single user"""
        with client.get('/users/1') as response:
            response.assert_status(200) \
                    .assert_ok() \
                    .assert_json_contains({'id': 1, 'name': 'Leanne Graham'})

    def test_get_users_list(self, client: Client):
        """Test retrieving list of users"""
        with client.get('/users') as response:
            response.assert_status(200).assert_ok()

            users = response.json()
            assert len(users) == 10
            assert all('id' in user for user in users)

    def test_get_with_query_params(self, client: Client):
        """Test GET request with query parameters"""
        with client.get('/posts') \
            .with_params({'userId': 1}) as response:
            response.assert_status(200)
            posts = response.json()
            # All posts should belong to user 1
            assert all(post['userId'] == 1 for post in posts)

    def test_create_post(self, client):
        """Test POST request to create a resource"""
        new_post = {
            'title': 'Test Post',
            'body': 'This is a test',
            'userId': 1
        }

        with client.post('/posts').with_body(new_post) as response:
            response.assert_status(201) \
                    .assert_json_contains({'userId': 1, 'title': 'Test Post'})
            created = response.json()
            assert 'id' in created

    def test_update_post(self, client):
        """Test PUT request to update a resource"""
        updated_post = {
            'id': 1,
            'title': 'Updated Title',
            'body': 'Updated body',
            'userId': 1
        }

        with client.put('/posts/1').with_body(updated_post) as response:
            response.assert_status(200) \
                    .assert_json_contains({'id': 1, 'title': 'Updated Title'})

    def test_partial_update_post(self, client):
        """Test PATCH request for partial update"""
        with client.patch('/posts/1') \
            .with_body({'title': 'Patched Title'}) as response:

            response.assert_status(200)
            updated = response.json()
            assert updated['title'] == 'Patched Title'

    def test_delete_post(self, client):
        """Test DELETE request"""
        with client.delete('/posts/1') as response:
            response.assert_status(200)

    def test_response_time(self, client):
        """Test that response time is tracked"""
        with client.get('/users/1') as response:
            response.assert_status(200)
            assert response.elapsed > 0
            assert response.elapsed < 5.0  # Should be under 5 seconds


class TestHTTPBinAPI:
    """Test suite for HTTPBin API (authentication, headers, etc.)"""
        
    client = Client('https://httpbin.org').with_header("User-Agent", "lashtest-httpbin-tests/1.0")
    
    @authenticated(BasicAuth(username="testuser", password="testpass"))
    def test_basic_auth_success(self):
        """Test successful basic authentication"""
        with self.client.get('/basic-auth/testuser/testpass') as response:
            response.assert_status(200) \
                    .assert_json_contains({'authenticated': True})
    
    def test_bearer_token(self):
        """Test bearer token authentication"""
        with self.client.get('/bearer') \
            .with_auth(BearerToken('my-secret-token')) as response:
            
            response.assert_status(200) \
                    .assert_json_contains({'authenticated': True, 'token': 'my-secret-token'})
    
    def test_custom_headers(self):
        """Test sending custom headers"""
        with self.client.get('/headers') \
            .with_header('X-Custom-Header', 'TestValue') \
            .with_header('X-Request-ID', '12345') as response:
            
            response.assert_status(200)
            headers = response.json()['headers']
            assert 'X-Custom-Header' in headers
    
    def test_user_agent(self):
        """Test User-Agent header"""
        custom_client = self.client.with_header('User-Agent', 'TestBot/1.0')
        
        with custom_client.get('/user-agent') as response:
            response.assert_status(200)
            assert 'TestBot/1.0' in response.json()['user-agent']
    
    def test_json_payload(self):
        """Test sending JSON payload"""
        payload = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30
        }
        
        with self.client.post('/post').with_body(payload) as response:
            response.assert_status(200)
            received = response.json()['json']
            assert received == payload
    
    def test_form_data(self):
        """Test sending form data"""
        form = {
            'username': 'testuser',
            'password': 'secret'
        }
        
        with self.client.post('/post').with_data(form) as response:
            response.assert_status(200)
            received = response.json()['form']
            assert received == form
    
    def test_status_codes(self):
        """Test different HTTP status codes"""
        test_codes = [200, 201, 204, 400, 404, 500]
        
        for code in test_codes:
            with self.client.get(f'/status/{code}') as response:
                response.assert_status(code)
    
    def test_404_error(self):
        """Test 404 Not Found response"""
        with self.client.get('/status/404') as response:
            response.assert_status(404)
            assert not response.ok
    
    def test_json_response(self):
        """Test JSON response parsing"""
        with self.client.get('/json') as response:
            response.assert_status(200)
            data = response.json()
            assert isinstance(data, dict)
    
    def test_delay_endpoint(self):
        """Test delayed response"""
        with self.client.get('/delay/1') as response:
            response.assert_status(200)
            assert response.elapsed >= 1.0


class TestClientConfiguration:
    """Test client configuration and chainable methods"""
    
    def test_client_with_default_headers(self):
        """Test setting default headers on client"""
        client = Client('https://httpbin.org') \
            .with_header('X-API-Key', 'test-key') \
            .with_header('X-Client-Version', '1.0')
        
        with client.get('/headers') as response:
            response.assert_status(200)
            headers = response.json()['headers']
            assert 'X-Api-Key' in headers or 'X-API-Key' in headers
    
    def test_request_header_override(self):
        """Test overriding client headers per request"""
        client = Client('https://httpbin.org') \
            .with_header('X-Default', 'default-value')
        
        with client.get('/headers') \
            .with_header('X-Override', 'override-value') as response:
            
            response.assert_status(200)
            headers = response.json()['headers']
            assert 'X-Override' in headers
    
    def test_timeout_configuration(self):
        """Test timeout configuration"""
        client = Client('https://httpbin.org') \
            .with_timeout(5)
        
        with client.get('/delay/1') as response:
            response.assert_status(200)
    
    def test_context_manager(self):
        """Test using client as context manager"""
        with Client('https://httpbin.org') as client:
            with client.get('/get') as response:
                response.assert_status(200)


class TestResponseAssertions:
    """Test response assertion methods"""
    
    @pytest.fixture
    def client(self):
        return Client('https://httpbin.org').with_header("User-Agent", "lashtest-httpbin-tests/1.0")
    
    def test_assert_status(self, client):
        """Test status code assertion"""
        with client.get('/status/200') as response:
            response.assert_status(200)
    
    def test_assert_ok(self, client):
        """Test OK status assertion"""
        with client.get('/get') as response:
            response.assert_ok()
    
    def test_assert_header(self, client):
        """Test header assertion"""
        with client.get('/get') as response:
            response.assert_header('Content-Type')
    
    def test_assert_json_contains(self, client: Client):
        """Test JSON contains assertion"""
        with client.post('/post') \
            .with_body({'name': 'Test', 'value': 123}) as response:
            
            response.assert_json_path('$.json.name', 'Test') \
                    .assert_json_path('$.json.value', 123)
    
    def test_assert_response_time(self, client):
        """Test response time assertion"""
        with client.get('/delay/1') as response:
            response.assert_response_time(3.0)  # Should be under 3 seconds
    
    def test_chained_assertions(self, client):
        """Test chaining multiple assertions"""
        with client.get('/get') as response:
            response.assert_status(200) \
                    .assert_ok() \
                    .assert_header('Content-Type') \
                    .assert_response_time(5.0)


class TestRealWorldScenario:
    """Integration test simulating real API testing workflow"""
    
    def test_user_workflow(self):
        """Test a complete user workflow"""
        client = Client('https://jsonplaceholder.typicode.com').with_header("User-Agent", "lashtest-jsonplaceholder-tests/1.0")
        
        # Step 1: Get all users
        with client.get('/users') as response:
            response.assert_status(200)
            users = response.json()
            first_user_id = users[0]['id']
        
        # Step 2: Get specific user details
        with client.get(f'/users/{first_user_id}') as response:
            response.assert_status(200)
            user = response.json()
            assert user['id'] == first_user_id
        
        # Step 3: Get user's posts
        with client.get('/posts') \
            .with_params({'userId': first_user_id}) as response:
            
            response.assert_status(200)
            posts = response.json()
            assert len(posts) > 0
            assert all(p['userId'] == first_user_id for p in posts)
        
        # Step 4: Create a new post for the user
        new_post = {
            'title': 'Integration Test Post',
            'body': 'Created during integration test',
            'userId': first_user_id
        }
        
        with client.post('/posts').with_body(new_post) as response:
            response.assert_status(201)
            created_post = response.json()
            assert 'id' in created_post
        
        print(f"✓ Completed workflow for user {first_user_id}")


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
