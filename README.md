# lashtest

A Python library for writing expressive, readable API tests with built-in Allure reporting.

[![Release](https://img.shields.io/github/v/release/sidalihmdn/lashtest)](https://github.com/sidalihmdn/lashtest/releases)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

- **Fluent builder API** — chain methods to build requests in one expression
- **Rich assertions** — assert status, JSON body, headers, cookies, response time, JSONPath, JSON Schema, and XML with XPath
- **XML support** — XPath queries with automatic namespace detection for SOAP, RSS, Atom, and SVG
- **Multiple auth strategies** — Bearer token, Basic auth, API key
- **Retry with exponential backoff** — configurable per-request
- **File uploads** — multipart form data with automatic handle cleanup
- **Allure integration** — requests and responses auto-attached as report steps
- **Test decorators** — `@authenticated`, `@title`, `@severity`, `@description`, `@tag`, `@link`
- **Fake data generator** — built-in `fake` for names, emails, phone numbers, addresses
- **CLI runner** — `lashtest run` collects and runs tests, `lashtest report` generates HTML reports
- **SSL auto-detection** — finds the system CA bundle on macOS, Linux, and Windows without configuration

---

## Installation

```bash
pip install lashtest
```

To also install development tools (coverage):

```bash
pip install "lashtest[dev]"
```

**Requirements:** Python 3.9+, and [Allure CLI](https://docs.qameta.io/allure/#_installing_a_commandline) for HTML report generation.

---

## Quick start

```python
from lashtest import APIClient

def test_get_user():
    with APIClient('https://jsonplaceholder.typicode.com').get('/users/1') as response:
        response.assert_status(200) \
                .assert_json_contains({'id': 1}) \
                .assert_response_time(2.0)
```

Run it:

```bash
lashtest run tests/
```

---

## Table of contents

- [Client configuration](#client-configuration)
- [Making requests](#making-requests)
- [Assertions](#assertions)
  - [Status](#status)
  - [JSON body](#json-body)
  - [JSONPath](#jsonpath)
  - [Headers and cookies](#headers-and-cookies)
  - [Performance](#performance)
  - [XML body](#xml-body)
- [Authentication](#authentication)
- [Retry logic](#retry-logic)
- [File uploads](#file-uploads)
- [Test decorators](#test-decorators)
- [Fake data](#fake-data)
- [Allure reporting](#allure-reporting)
- [CLI reference](#cli-reference)
- [Error reference](#error-reference)

---

## Client configuration

`APIClient` is the entry point. All configuration methods return `self` and can be chained.

```python
from lashtest import APIClient
from lashtest.http import BearerToken

client = (
    APIClient('https://api.example.com')
    .with_base_path('/v1')
    .with_auth(BearerToken('my-token'))
    .with_header('X-Request-ID', 'test-suite')
    .with_timeout(10.0)
)
```

| Method | Description |
|---|---|
| `with_base_path(path)` | Prefix applied to every endpoint (must start with `/`) |
| `with_header(key, value)` | Add a default header sent with every request |
| `with_headers(headers)` | Add multiple default headers at once |
| `with_auth(auth)` | Set default authentication (see [Authentication](#authentication)) |
| `with_timeout(seconds)` | Default timeout in seconds (default: `30`) |
| `with_ssl_verification(verify)` | `True`, `False`, or path to a CA bundle file |
| `with_cookies(cookies)` | Set session-level cookies |
| `clear_cookies()` | Remove all session cookies |

### Context manager

Use `APIClient` as a context manager to automatically close the underlying session:

```python
with APIClient('https://api.example.com') as client:
    with client.get('/health') as response:
        response.assert_ok()
```

---

## Making requests

Call `.get()`, `.post()`, `.put()`, `.patch()`, or `.delete()` on the client to get a `Request` builder. Use it as a context manager — it executes the request and yields the `Response`.

```python
# GET with query parameters
with client.get('/users').with_param('page', '2').with_param('limit', '10') as response:
    response.assert_ok()

# POST with JSON body
with client.post('/users').with_json({'name': 'Alice', 'email': 'alice@example.com'}) as response:
    response.assert_status(201)

# PUT with JSON body
with client.put('/users/1').with_json({'name': 'Alice Updated'}) as response:
    response.assert_ok()

# PATCH
with client.patch('/users/1').with_json({'email': 'new@example.com'}) as response:
    response.assert_ok()

# DELETE
with client.delete('/users/1') as response:
    response.assert_status(204)
```

### Request builder methods

All methods return `self` and can be chained before the `with` statement.

| Method | Description |
|---|---|
| `with_header(key, value)` | Add a request-level header |
| `with_param(key, value)` | Add a query string parameter |
| `with_params(params)` | Add multiple query string parameters |
| `with_json(body)` | Set JSON body and `Content-Type: application/json` |
| `with_body(body)` | Set raw body |
| `with_data(data)` | Set form-encoded body |
| `with_auth(auth)` | Override the client-level auth for this request |
| `with_timeout(seconds)` | Override the client-level timeout for this request |
| `with_file(field, path)` | Attach a file for multipart upload (see [File uploads](#file-uploads)) |
| `with_retry(...)` | Configure retry logic (see [Retry logic](#retry-logic)) |

### Accessing the response

The context manager returns a `Response` object:

```python
with client.get('/users/1') as response:
    print(response.status_code)   # int
    print(response.headers)       # dict
    print(response.text)          # str
    print(response.json())        # dict or list
    print(response.elapsed)       # float (seconds)
    print(response.ok)            # bool (True if 2xx)
```

---

## Assertions

All assertion methods return `self`, so they can be chained.

```python
with client.get('/users/1') as response:
    response \
        .assert_status(200) \
        .assert_ok() \
        .assert_header('Content-Type') \
        .assert_json_path('$.name', 'Alice') \
        .assert_response_time(1.5)
```

### Status

```python
response.assert_status(200)   # exact status code
response.assert_ok()          # any 2xx status
```

### JSON body

```python
# Exact match
response.assert_json({'id': 1, 'name': 'Alice'})

# Subset match — only checks specified keys
response.assert_json_contains({'id': 1})

# JSON Schema validation
schema = {
    'type': 'object',
    'properties': {
        'id':   {'type': 'integer'},
        'name': {'type': 'string'},
    },
    'required': ['id', 'name'],
}
response.assert_json_schema(schema)
```

### JSONPath

Uses [JSONPath](https://goessner.net/articles/JsonPath/) expressions via `jsonpath_ng`.

```python
response.assert_json_path('$.id', 1)                    # value match
response.assert_json_path_type('$.id', int)             # type match
response.assert_json_path_exists('$.address.city')      # existence check
```

### Headers and cookies

```python
response.assert_header('Content-Type')                       # header exists
response.assert_header('Content-Type', 'application/json')  # header value match

response.assert_cookie_exists('session_id')
response.assert_cookie_value('theme', 'dark')
```

### Performance

```python
response.assert_response_time(0.5)   # must respond in under 0.5 seconds
```

### XML body

Test APIs that return XML (SOAP, RSS, Atom, SVG, etc.) with XPath expressions and automatic namespace support.

```python
# Basic XPath selection and text assertion
response.assertions.xml.xpath('//book[1]/title').text.eq('Python Guide')

# Count elements
response.assertions.xml.xpath('//book').count.gte(5)

# Assert element exists
response.assertions.xml.xpath('//user[@id="123"]').exists()

# Attribute assertions
response.assertions.xml.xpath('//book[@id="123"]').attribute('author').contains('Smith')

# Collection assertions on multiple nodes via .all()
response.assertions.xml.xpath('//book').all().text.contains('Python')

# First and nth node selection
response.assertions.xml.xpath('//item').first.text.eq('First Item')
response.assertions.xml.xpath('//item').nth(2).text.eq('Second Item')
```

#### Automatic Namespace Support

Namespaces are automatically detected — no configuration needed. Works with:

```python
# SOAP envelope
response.assertions.xml.xpath('//soap:Body').exists()

# Atom feed
response.assertions.xml.xpath('//entry/title').text.eq('Latest Post')

# Default namespace
response.assertions.xml.xpath('//book').count.gte(1)
```

---

## Authentication

Import auth classes from `lashtest.http`:

```python
from lashtest.http import BearerToken, BasicAuth, APIKey
```

### Bearer token

```python
client = APIClient('https://api.example.com').with_auth(BearerToken('eyJhbGci...'))
```

Adds `Authorization: Bearer <token>` to every request.

### Basic auth

```python
client = APIClient('https://api.example.com').with_auth(BasicAuth('username', 'password'))
```

Adds `Authorization: Basic <base64(username:password)>` to every request.

### API key

```python
# Default header name: X-API-KEY
client = APIClient('https://api.example.com').with_auth(APIKey(api_key='secret'))

# Custom header name
client = APIClient('https://api.example.com').with_auth(APIKey(header_name='X-Custom-Key', api_key='secret'))
```

### Per-request override

```python
# Client has no auth, but this one request uses a token
with client.get('/admin').with_auth(BearerToken('admin-token')) as response:
    response.assert_ok()
```

---

## Retry logic

Call `.with_retry()` on any request to enable automatic retries with exponential backoff.

```python
with (
    client.post('/submit')
    .with_json({'data': 'value'})
    .with_retry(max_attempts=3, on_status=[500, 502, 503, 504])
) as response:
    response.assert_ok()
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_attempts` | `int` | — | Maximum number of attempts (required) |
| `on_status` | `list[int]` | `[500, 502, 503, 504]` | Retry on these status codes |
| `raise_on_exhausted` | `bool` | `False` | Raise `MaxRetriesExceededError` after all attempts fail |

**Backoff schedule:** `2^(attempt-1)` seconds — 1 s, 2 s, 4 s, …

```python
from lashtest import MaxRetriesExceededError

try:
    with client.get('/flaky').with_retry(max_attempts=3, raise_on_exhausted=True) as response:
        response.assert_ok()
except MaxRetriesExceededError as e:
    print(f"Failed after {e.retries} attempts, last status: {e.status_code}")
```

---

## File uploads

Use `.with_file(field, path)` for multipart file uploads. File handles are opened and closed automatically.

```python
with client.post('/upload').with_file('document', '/path/to/report.pdf') as response:
    response.assert_status(201)
```

Multiple files:

```python
with (
    client.post('/upload')
    .with_file('avatar', '/path/to/photo.jpg')
    .with_file('resume', '/path/to/cv.pdf')
) as response:
    response.assert_ok()
```

---

## Test decorators

Import decorators from `lashtest.decorators`:

```python
from lashtest.decorators import authenticated, title, severity, description, tag, link
```

### `@authenticated`

Injects authentication into every request made by `self.client` inside the decorated test. The original client is restored after each test, even if the test raises.

**Method-level:**

```python
from lashtest.decorators import authenticated
from lashtest.http import BearerToken

class TestUsers:
    client = APIClient('https://api.example.com')

    @authenticated(BearerToken('my-token'))
    def test_get_profile(self):
        with self.client.get('/profile') as response:
            response.assert_ok()
```

**Class-level** — applies to all `test_*` methods automatically:

```python
@authenticated(BasicAuth('admin', 'secret'))
class TestAdminEndpoints:
    client = APIClient('https://api.example.com')

    def test_list_users(self):
        with self.client.get('/admin/users') as response:
            response.assert_ok()

    def test_delete_user(self):
        with self.client.delete('/admin/users/1') as response:
            response.assert_status(204)
```

### Allure decorators

These are thin wrappers around the corresponding `allure` decorators.

```python
@title("User creation returns 201")
@severity('critical')
@description("Verifies that POST /users creates a new user and returns the created resource.")
@tag('smoke', 'users')
@link('https://jira.example.com/browse/API-42', name='API-42')
def test_create_user():
    ...
```

| Decorator | Description |
|---|---|
| `@title(text)` | Sets the test title in the Allure report |
| `@severity(level)` | `blocker`, `critical`, `normal`, `minor`, `trivial` |
| `@description(text)` | Adds a description to the test in the report |
| `@tag(*tags)` | Marks tests for filtering with `-t` |
| `@link(url, name)` | Links to an external resource (JIRA, docs, etc.) |

---

## Fake data

`fake` provides simple, dependency-free test data generation:

```python
from lashtest.utils import fake

fake.name()                       # 'Alice Martin'
fake.email()                      # 'xktvwqbn@gmail.com'
fake.phone()                      # '+33 6 12 34 56 78'
fake.phone(country_code='+1')     # '+1 6 12 34 56 78'
fake.address()                    # '12 Rue de Rivoli, Paris, France'
```

Use it directly in test payloads:

```python
def test_create_user():
    with client.post('/users').with_json({
        'name':    fake.name(),
        'email':   fake.email(),
        'phone':   fake.phone(),
        'address': fake.address(),
    }) as response:
        response.assert_status(201)
```

---

## Allure reporting

Every request and response is automatically recorded as an Allure step with the body attached as an artifact.

### Viewing reports

**Step 1 — Run tests and collect results:**

```bash
lashtest run tests/ --allure-dir allure-results
```

**Step 2 — Generate and open the HTML report:**

```bash
lashtest report
```

Or using the Allure CLI directly:

```bash
allure serve allure-results
```

### Enhancing reports

```python
from lashtest.decorators import title, severity, description

@title("POST /users returns 201 with valid payload")
@severity('critical')
@description("Ensures the user creation endpoint validates input and returns the created resource.")
def test_create_user():
    with client.post('/users').with_json({'name': fake.name(), 'email': fake.email()}) as response:
        response.assert_status(201).assert_json_path_exists('$.id')
```

---

## CLI reference

### `lashtest run`

Discover and run API tests.

```
Usage: lashtest run [PATH] [OPTIONS]

Arguments:
  PATH  Test directory or file  [default: tests/]

Options:
  -v, --verbose              Enable verbose output
  -r, --allure-dir TEXT      Directory for Allure results  [default: allure-results]
  -t, --tags TEXT            Filter tests by tag (comma-separated)
  --help                     Show this message and exit.
```

**Examples:**

```bash
# Run all tests
lashtest run

# Run a specific file
lashtest run tests/test_users.py

# Filter by tag
lashtest run -t smoke

# Custom results directory with verbose output
lashtest run -r ci-results -v
```

### `lashtest report`

Generate an HTML Allure report from collected results.

```
Usage: lashtest report [RESULTS-DIR] [OUTPUT-DIR]

Arguments:
  RESULTS-DIR  Allure results directory  [default: allure-results]
  OUTPUT-DIR   Output HTML report directory  [default: allure-report]
```

---

## Error reference

All exceptions inherit from `lashtest.APIError`.

| Exception | When raised |
|---|---|
| `APIError` | Base class — catch this to handle any library error |
| `HTTPError` | The server returned an HTTP error response |
| `APITimeoutError` | The request exceeded the configured timeout |
| `APIConnectionError` | Could not connect to the server |
| `InvalidURL` | The URL or endpoint is malformed |
| `JSONDecodeError` | The response body is not valid JSON |
| `AuthenticationError` | Authentication failed |
| `MaxRetriesExceededError` | All retry attempts failed (only when `raise_on_exhausted=True`) |

```python
from lashtest import APIClient, APIError, APITimeoutError, MaxRetriesExceededError

try:
    with APIClient('https://api.example.com').with_timeout(5.0).get('/slow') as response:
        response.assert_ok()
except APITimeoutError as e:
    print(f"Timed out after {e.timeout}s")
except APIError as e:
    print(f"Request failed: {e}")
```

---

## Project structure

Recommended layout for a test project using lashtest:

```
my-api-tests/
├── pyproject.toml
├── conftest.py          # shared fixtures
└── tests/
    ├── test_users.py
    ├── test_products.py
    └── test_auth.py
```

**`conftest.py`:**

```python
import pytest
from lashtest import APIClient
from lashtest.http import BearerToken

@pytest.fixture(scope='session')
def client():
    return (
        APIClient('https://api.example.com')
        .with_base_path('/v1')
        .with_auth(BearerToken('token'))
        .with_timeout(10.0)
    )
```

**`tests/test_users.py`:**

```python
from lashtest.decorators import title, severity, tag
from lashtest.utils import fake

@tag('users', 'smoke')
class TestUsers:

    @title("GET /users returns a list")
    @severity('normal')
    def test_list_users(self, client):
        with client.get('/users') as response:
            response.assert_ok() \
                    .assert_json_path_exists('$[0].id')

    @title("POST /users creates a user")
    @severity('critical')
    def test_create_user(self, client):
        with client.post('/users').with_json({
            'name':  fake.name(),
            'email': fake.email(),
        }) as response:
            response.assert_status(201) \
                    .assert_json_path_exists('$.id')
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

MIT — see [LICENCE](LICENCE).
