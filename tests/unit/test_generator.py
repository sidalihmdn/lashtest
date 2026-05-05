"""Unit tests for lashtest.utils.generator.fake"""

import re
import pytest
from lashtest.utils.generator import fake


class TestFakeName:

    def test_returns_string(self):
        assert isinstance(fake.name(), str)

    def test_contains_two_words(self):
        parts = fake.name().split()
        assert len(parts) == 2

    def test_different_values_generated(self):
        names = {fake.name() for _ in range(20)}
        assert len(names) > 1  # not always the same value


class TestFakeEmail:

    def test_returns_string(self):
        assert isinstance(fake.email(), str)

    def test_contains_at_symbol(self):
        assert '@' in fake.email()

    def test_has_valid_format(self):
        email = fake.email()
        assert re.match(r'^[a-z]{8}@.+\..+$', email), f"Invalid email format: {email}"

    def test_different_values_generated(self):
        emails = {fake.email() for _ in range(20)}
        assert len(emails) > 1


class TestFakePhone:

    def test_returns_string(self):
        assert isinstance(fake.phone(), str)

    def test_default_country_code(self):
        assert fake.phone().startswith('+33')

    def test_custom_country_code(self):
        assert fake.phone(country_code='+1').startswith('+1')

    def test_different_values_generated(self):
        phones = {fake.phone() for _ in range(20)}
        assert len(phones) > 1


class TestFakeAddress:

    def test_returns_string(self):
        assert isinstance(fake.address(), str)

    def test_contains_france(self):
        assert 'France' in fake.address()

    def test_contains_city(self):
        cities = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice']
        address = fake.address()
        assert any(city in address for city in cities)

    def test_has_three_comma_separated_parts(self):
        parts = fake.address().split(', ')
        assert len(parts) == 3

    def test_different_values_generated(self):
        addresses = {fake.address() for _ in range(20)}
        assert len(addresses) > 1
