# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2025-05-05

### Added

- `APIClient` — fluent HTTP client with method chaining for `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
- `Request` builder — per-request configuration for headers, query params, body, auth, timeout, files, and retry
- `Response` — rich assertion API with 13 chainable assertion methods
- `with_base_path()` — optional path prefix applied to all requests on a client
- `with_retry()` — automatic retries with exponential backoff, configurable status codes, and optional `MaxRetriesExceededError`
- `with_file()` — multipart file upload with automatic file handle lifecycle management
- `BasicAuth`, `BearerToken`, `APIKey` — pluggable authentication strategies
- Per-request auth override via `Request.with_auth()`
- JSON body assertions: `assert_json`, `assert_json_contains`, `assert_json_schema`
- JSONPath assertions: `assert_json_path`, `assert_json_path_type`, `assert_json_path_exists`
- Header and cookie assertions: `assert_header`, `assert_cookie_exists`, `assert_cookie_value`
- Performance assertion: `assert_response_time`
- `@authenticated` decorator — method-level and class-level authentication injection with automatic client restore
- `@title`, `@severity`, `@description`, `@tag`, `@link` — Allure report decorators
- Allure integration — requests and responses automatically recorded as steps with body attachments
- Retry steps recorded in Allure report
- `fake` — built-in fake data generator for names, emails, phone numbers, and addresses
- `find_system_ca_bundle()` — automatic SSL CA bundle detection on macOS, Linux, and Windows
- `lashtest run` CLI command — pytest-based test runner with Allure results output and tag filtering
- `lashtest report` CLI command — Allure HTML report generation
- `get_logger()` — `NullHandler`-based logger for the `lashtest` namespace
- Full exception hierarchy: `APIError`, `HTTPError`, `APITimeoutError`, `APIConnectionError`, `InvalidURL`, `JSONDecodeError`, `AuthenticationError`, `MaxRetriesExceededError`
- `__tracebackhide__ = True` on all assertion methods for clean pytest output
- Context manager support on both `APIClient` and `Request`
- Comprehensive unit test suite covering all modules
