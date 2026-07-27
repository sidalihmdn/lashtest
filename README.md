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
- **Multiple auth strategies** — Bearer token, Basic auth, API key, OAuth2 client credentials, OAuth2 refresh token, custom token provider
- **Retry with exponential backoff** — configurable per-request with jitter, backoff factor, max backoff, and exception-level retry
- **Request/response hooks** — register `before_request` and `after_response` callbacks on the client
- **Polling utility** — `wait_until()` for eventually-consistent APIs with configurable timeout and interval
- **Snapshot assertions** — `SnapshotStore` and `assert_snapshot()` for golden-file response testing
- **OpenAPI validation** — `OpenAPIValidator` loads a spec and validates responses against it
- **Async support** — `AsyncAPIClient` backed by `httpx` mirrors the synchronous API with `async`/`await`
- **File uploads** — multipart form data with automatic handle cleanup
- **Allure integration** — requests and responses auto-attached as report steps
- **Test decorators** — `@authenticated`, `@title`, `@severity`, `@description`, `@tag`, `@link`
- **Fake data generator** — built-in `fake` for names, emails, phone numbers, addresses
- **CLI runner** — `lashtest run` collects and runs tests with parallel execution, JUnit XML output, and env profiles; `lashtest report` generates HTML reports
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

**Optional extras:**

```bash
# Async support
pip install httpx

# OpenAPI validation
pip install openapi-spec-validator pyyaml

# Parallel test execution
pip install pytest-xdist
```

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
- [Hooks](#hooks)
- [Polling](#polling)
- [Snapshot assertions](#snapshot-assertions)
- [OpenAPI validation](#openapi-validation)
- [Async client](#async-client)
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
# Fluent API (same style as XML assertions)
response.assertions.json.path('$.books[0].title').text.eq('Python Guide')
response.assertions.json.path('$.books[*]').count.gte(1)
response.assertions.json.path('$.books[*].title').all().text.contains('Python Guide')
response.assertions.json.path('$.address.city').exists()

# Backward compatible wrappers
response.assert_json_path('$.id', 1)
response.assert_json_path_type('$.id', int)
response.assert_json_path_exists('$.address.city')
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
from lashtest.http import BearerToken, BasicAuth, APIKey, OAuth2ClientCredentials, OAuth2RefreshToken, CustomTokenProvider
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

### OAuth2 client credentials

Fetches and caches an access token using the client-credentials flow. Refreshes automatically when the token expires.

```python
from lashtest.http import OAuth2ClientCredentials

client = APIClient('https://api.example.com').with_auth(
    OAuth2ClientCredentials(
        token_url='https://auth.example.com/oauth/token',
        client_id='my-client',
        client_secret='my-secret',
        scope='read write',   # optional
    )
)
```

### OAuth2 refresh token

Uses an existing refresh token to obtain (and cache) a fresh access token.

```python
from lashtest.http import OAuth2RefreshToken

client = APIClient('https://api.example.com').with_auth(
    OAuth2RefreshToken(
        token_url='https://auth.example.com/oauth/token',
        client_id='my-client',
        client_secret='my-secret',
        refresh_token='<long-lived-refresh-token>',
    )
)
```

### Custom token provider

Supply any callable that returns the current token string. Useful for reading tokens from a vault or a custom cache.

```python
from lashtest.http import CustomTokenProvider

def get_token():
    return vault_client.read_secret('api/token')['data']['value']

client = APIClient('https://api.example.com').with_auth(
    CustomTokenProvider(get_token)
)

# Custom header and scheme
client = APIClient('https://api.example.com').with_auth(
    CustomTokenProvider(get_token, header_name='X-Auth-Token', scheme='')
)
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
| `backoff_factor` | `float` | `1.0` | Multiplier for the exponential delay |
| `max_backoff` | `float` | `60.0` | Upper bound on the computed delay (seconds) |
| `jitter` | `bool` | `False` | Add a random 0–1 s fraction to each delay to avoid thundering-herd |
| `retry_on_exceptions` | `bool` | `False` | Also retry on connection/timeout exceptions, not just status codes |

**Backoff schedule:** `backoff_factor * 2^(attempt-1)` seconds, capped at `max_backoff` — 1 s, 2 s, 4 s, …

```python
from lashtest import MaxRetriesExceededError

try:
    with client.get('/flaky').with_retry(max_attempts=3, raise_on_exhausted=True) as response:
        response.assert_ok()
except MaxRetriesExceededError as e:
    print(f"Failed after {e.retries} attempts, last status: {e.status_code}")
```

Advanced retry with jitter and exception handling:

```python
with (
    client.post('/submit')
    .with_json({'data': 'value'})
    .with_retry(
        max_attempts=5,
        on_status=[429, 500, 502, 503, 504],
        backoff_factor=0.5,
        max_backoff=30.0,
        jitter=True,
        retry_on_exceptions=True,
    )
) as response:
    response.assert_ok()
```

---

## Hooks

Register callbacks that run before every request or after every response on a client.

```python
def log_request(request):
    print(f"--> {request.method} {request.endpoint}")

def log_response(request, response):
    print(f"<-- {response.status_code}")

client = (
    APIClient('https://api.example.com')
    .add_hook('before_request', log_request)
    .add_hook('after_response', log_response)
)
```

| Event | Callback signature | Description |
|---|---|---|
| `"before_request"` | `fn(request: Request)` | Called before each request is sent |
| `"after_response"` | `fn(request: Request, response: Response)` | Called after each response is received |

---

## Polling

Use `wait_until()` to poll a condition function repeatedly until it returns a truthy value. Designed for eventually-consistent APIs where a resource may not be immediately available after creation.

```python
from lashtest.utils.polling import wait_until

client = APIClient('https://api.example.com')

def job_is_done():
    with client.get('/jobs/42') as r:
        return r.json().get('status') == 'done'

# Raises PollingTimeoutError if not satisfied within 60 s
wait_until(job_is_done, timeout=60, interval=2)

# Return None instead of raising
result = wait_until(job_is_done, timeout=30, raises=False)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `condition` | `Callable[[], T]` | — | Zero-argument callable; polling stops when it returns a truthy value |
| `timeout` | `float` | `30.0` | Maximum seconds to wait |
| `interval` | `float` | `1.0` | Seconds between attempts |
| `raises` | `bool` | `True` | Raise `PollingTimeoutError` on timeout (pass `False` to return `None`) |
| `description` | `str` | `None` | Optional label included in the timeout error message |

---

## Snapshot assertions

Snapshot assertions compare a response body against a file stored on disk. On first run the snapshot file is created; subsequent runs compare against it.

### Using `SnapshotStore`

```python
from lashtest.assertions.snapshot import SnapshotStore

snapshots = SnapshotStore()   # files stored in .lashtest_snapshots/

def test_user_profile():
    with APIClient('https://api.example.com').get('/users/1') as r:
        snapshots.assert_json(
            'user_profile',
            r.json(),
            ignore=['updated_at', 'created_at'],   # ignore dynamic keys
        )
```

### Using `assert_snapshot()` on the response

```python
with client.get('/users/1') as r:
    r.assert_snapshot('user_profile')

# Ignore dynamic fields
with client.get('/users/1') as r:
    r.assert_snapshot('user_profile', ignore=['updated_at'])

# Update the stored snapshot
with client.get('/users/1') as r:
    r.assert_snapshot('user_profile', update=True)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — | Snapshot identifier (used as the file stem) |
| `ignore` | `list[str]` | `None` | Dict keys to redact recursively before comparison |
| `update` | `bool` | `False` | Overwrite the stored snapshot instead of comparing |
| `snapshot_dir` | `str` | `".lashtest_snapshots"` | Directory where snapshot files are stored |

---

## OpenAPI validation

`OpenAPIValidator` loads an OpenAPI 3.x spec and validates that responses conform to it.

```bash
pip install openapi-spec-validator pyyaml   # required extras
```

```python
from lashtest import APIClient
from lashtest.openapi import OpenAPIValidator

validator = OpenAPIValidator('openapi.yaml')   # or a URL

def test_get_user():
    with APIClient('https://api.example.com').get('/users/1') as r:
        validator.assert_response('/users/{id}', 'GET', 200, r)
```

The validator also lets you inspect the schema directly:

```python
schema = validator.get_response_schema('/users/{id}', 'GET', 200)
```

---

## Async client

`AsyncAPIClient` is a fully async counterpart to `APIClient`, backed by `httpx`.

```bash
pip install httpx   # required
```

```python
import asyncio
from lashtest.core.async_client import AsyncAPIClient
from lashtest.http import BearerToken

async def test_async():
    async with AsyncAPIClient('https://api.example.com') as client:
        client.with_base_path('/v1').with_auth(BearerToken('my-token'))

        async with client.get('/users/1') as response:
            response.assert_status(200)
            response.assert_json_contains({'id': 1})

asyncio.run(test_async())
```

The async request builder supports the same chainable methods as the synchronous `Request`: `with_header`, `with_param`, `with_params`, `with_json`, `with_body`, `with_data`, `with_auth`, `with_timeout`.

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
  -p, --parallel INTEGER     Run tests in parallel using N workers (requires pytest-xdist)
  --junit-xml TEXT           Write a JUnit XML report to the given path
  --env TEXT                 Load environment variables from a named profile file
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

# Run tests in parallel with 4 workers
lashtest run -p 4

# Write a JUnit XML report
lashtest run --junit-xml report.xml

# Load a staging environment profile
lashtest run --env staging
```

#### Environment profiles

The `--env` flag loads environment variables from a dotenv-style file before running tests. Two naming conventions are supported, both looked up in the current working directory:

- `lashtest.{profile}.env` (e.g. `lashtest.staging.env`)
- `.env.{profile}` (e.g. `.env.staging`)

```ini
# lashtest.staging.env
BASE_URL=https://staging.api.example.com
API_KEY=staging-secret
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
| `PollingTimeoutError` | `wait_until()` timed out without the condition becoming true |
| `SnapshotMismatchError` | Response body does not match the stored snapshot |

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
