# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
## [v0.2.0] - 2026-05-15

### ADDED

- Added xml support (`e2b0f9c`)
- Add comprehensive XML assertions DSL with XPath support and auto namespace detection  ## Overview Implement a production-ready XML assertion framework for testing XML-based APIs (SOAP, RSS, Atom, etc.) with seamless integration into the existing assertion facade.  ## Features  ### Core XML Assertions - XPathSelection API for querying and asserting on XML nodes - Fluent chain-able assertion methods mirroring existing patterns (count, text, attribute, exists) - AllNodesSelection for collection-based assertions on multiple nodes via .all() - Integration with existing ValueAssertions, StringAssertions, CollectionAssertions  ### Error Handling - Graceful error handling for invalid XML (XMLSyntaxError, UnicodeDecodeError) - Detailed error messages for invalid XPath expressions - Available attributes display when accessing missing attributes - Helpful error context with XPath expressions in error messages  ### Namespace Support - Automatic detection of all namespaces in XML document - Transparent namespace handling in XPath queries - Support for default namespaces (converted to usable prefix) - Support for prefixed namespaces and nested declarations - Works with real-world formats: SOAP, Atom/RSS, SVG  ### API Design - response.assertions.xml.xpath('//element') - main entry point - .count - returns ValueAssertions for comparisons (eq, gte, lte, gt, lt) - .text - returns StringAssertions for text content assertions - .attribute('name') - returns StringAssertions for attribute assertions - .exists() - asserts at least one node exists - .first - selects first node (property) - .nth(n) - selects nth node with 1-based indexing - .all() - returns AllNodesSelection for collection assertions  ## Files Added - src/lashtest/assertions/xml/xml_assertions.py - Main XML assertions class with namespace detection - src/lashtest/assertions/xml/xpath_selection.py - XPath selection and result handling - src/lashtest/assertions/xml/namespace.py - Placeholder for future namespace utilities - src/lashtest/assertions/xml/schema.py - Placeholder for future schema validation - tests/test_xml_assertions.py - Integration tests with real public APIs - tests/test_xml_error_handling.py - Error scenario tests - tests/unit/test_xml_assertions.py - 47 unit tests covering all XML functionality - tests/unit/test_xml_namespace_detection.py - Namespace detection tests  ## Files Modified - src/lashtest/assertions/facade.py - Added .xml property to AssertionsFacade - src/lashtest/assertions/errors.py - Error types already defined  ## Test Coverage - 47 unit tests for XPath selection, counting, text/attribute extraction - 10+ namespace detection tests with real-world formats (SOAP, Atom, RSS) - 10+ error handling tests for invalid XML/XPath scenarios - Integration tests with W3Schools, HTTPBin, GitHub, Hacker News APIs  ## Breaking Changes None  ## Backward Compatibility ✅ Fully backward compatible - new feature only  ## Example Usage  ```python # Basic XPath and text assertion response.assertions.xml.xpath('//book[1]/title').text.eq('Python Guide')  # Count elements response.assertions.xml.xpath('//book').count.gte(5)  # Attribute assertions response.assertions.xml.xpath('//book[@id="123"]').attribute('author').contains('Smith')  # Collection assertions on multiple nodes response.assertions.xml.xpath('//book').all().text.contains('Python')  # With automatic namespace support response.assertions.xml.xpath('//soap:Body').exists() response.assertions.xml.xpath('//entry/title').text.eq('Latest Post') (`4e64d10`)

### FIXED

- Fixed an issue with the changelog generation (`6ff37fa`)
- Fixed an issuer with commit.link in the cliff.toml (`0b68e1f`)
- Fixed an issue with the release branch workflow (`1d21dbf`)

## [v0.1.0] - 2026-05-05


