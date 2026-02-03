import unittest
from agent.data_consumer import normalize_data, Signal

class TestDataConsumer(unittest.TestCase):
    def test_normalize_sentiment(self):
        data = {"sentiment": "0.8"}
        signal = normalize_data("Sentiment", data)
        self.assertIsInstance(signal, Signal)
        self.assertAlmostEqual(signal.value, 0.8)

    def test_normalize_volatility(self):
        data = {"volatility": "1.2"}
        signal = normalize_data("Volatility", data)
        self.assertIsInstance(signal, Signal)
        self.assertAlmostEqual(signal.value, 1.2)

if __name__ == "__main__":
    unittest.main()
