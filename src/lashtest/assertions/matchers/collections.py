from ..errors import AssertionFailure
from ..matchers.equality import ValueAssertions


class CollectionAssertions:
    def __init__(self, collection:list, description:str=None):
        self.collection = collection
        self.description = description
    
    
    @property
    def length(self):
        """Assert that the collection has the expected length."""
        return ValueAssertions(len(self.collection), description=self.description)

    def empty(self):
        """Assert that the collection is empty."""
        if self.collection:
            raise AssertionFailure(f"Expected {self.description} to be empty, but it has {len(self.collection)} items.")
        return self
    
    def not_empty(self):
        """Assert that the collection is not empty."""
        if not self.collection:
            raise AssertionFailure(f"Expected {self.description} to not be empty, but it is.")
        return self

    def contains(self, item):
        """Assert that the collection contains the specified item."""
        if item not in self.collection:
            raise AssertionFailure(f"Expected {self.description} to contain '{item}', but it does not.")
        return self
    
    def not_contains(self, item):
        """Assert that the collection does not contain the specified item."""
        if item in self.collection:
            raise AssertionFailure(f"Expected {self.description} to not contain '{item}', but it does.")
        return self
    
    def contains_all(self, items:list):
        """Assert that the collection contains all the specified items."""
        for item in items:
            if item not in self.collection:
                raise AssertionFailure(f"Expected {self.description} to contain '{item}', but it does not.")
        return self
    
    def contains_any(self, items:list):
        """Assert that the collection contains at least one of the specified items."""
        for item in items:
            if item in self.collection:
                return self
        raise AssertionFailure(f"Expected {self.description} to contain at least one of {items}, but it does not.")
    
    def contains_one_of(self, items:list):
        """Assert that the collection contains exactly one of the specified items."""
        for item in items:
            if item in self.collection:
                return self
        raise AssertionFailure(f"Expected {self.description} to contain exactly one of {items}, but it does not.")
    
    def all_match(self, predicate):
        """Assert that all items in the collection match the given predicate function."""
        for item in self.collection:
            if not predicate(item):
                raise AssertionFailure(f"Expected all items in {self.description} to match the predicate, but found an item that does not: '{item}'")
        return self
    
    def any_match(self, predicate):
        """Assert that at least one item in the collection matches the given predicate function."""
        for item in self.collection:
            if predicate(item):
                return self
        raise AssertionFailure(f"Expected at least one item in {self.description} to match the predicate, but none did.")