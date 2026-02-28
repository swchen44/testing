import unittest
from app.services.greeting_service import greet


class TestGreetingService(unittest.TestCase):

    def test_greet_contains_message(self):
        result = greet("哈囉")
        self.assertIn("哈囉", result)

    def test_greet_contains_cow(self):
        result = greet("哈囉")
        self.assertIn("(__)", result)


if __name__ == "__main__":
    unittest.main()
