import random
import string
from .names import names, surnames, fr_streets, email_providers
from typing import Literal, Optional, Dict, Any

class fake:
    """Fake generator for testing purposes
    generate unique data for testing
    """
    @staticmethod
    def name() -> str:
        return f"{random.choice(names)} {random.choice(surnames)}"

    @staticmethod
    def email() -> str:
        return f"{''.join(random.choices(string.ascii_lowercase, k=8))}@{random.choice(email_providers)}"

    @staticmethod
    def phone(country_code: str = '+33') -> str:
        return f"{country_code}{random.randint(1000000000, 9999999999)}"

    @staticmethod
    def address() -> str:
        return "{street}, {city}, {country}".format(
            street=random.choice(fr_streets),
            city=random.choice(['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice']),
            country='France'
        )