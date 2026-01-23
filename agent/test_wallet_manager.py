import unittest
from agent.wallet_manager import can_spend, get_daily_spend

class TestWalletManager(unittest.TestCase):
    def test_can_spend(self):
        self.assertTrue(can_spend(1))
        self.assertFalse(can_spend(100000))

    def test_get_daily_spend(self):
        spend = get_daily_spend()
        self.assertIsInstance(spend, float)

if __name__ == "__main__":
    unittest.main()
