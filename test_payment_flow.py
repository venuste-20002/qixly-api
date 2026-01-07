#!/usr/bin/env python3
"""
Comprehensive test script for the complete payment flow
Tests: Authentication → Cart → Payment → Paypack Integration → Webhook
"""

import json
import time
import requests
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test user credentials (you'll need to provide these)
TEST_EMAIL = "test@example.com"  # Replace with actual test user email
TEST_PASSWORD = "testpassword"   # Replace with actual test user password

# Test data
TEST_PHONE = "250788123456"  # Valid Rwandan phone number
TEST_CARD_VARIANT_ID = "your-card-variant-id"  # Replace with actual card variant ID

class PaymentFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.cart_id = None
        self.transaction_id = None

    def log(self, message: str, level: str = "INFO"):
        """Simple logging"""
        print(f"[{level}] {message}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, headers: Dict = None) -> Dict:
        """Make HTTP request with proper error handling"""
        url = f"{BASE_URL}{API_PREFIX}{endpoint}"
        default_headers = {"Content-Type": "application/json"}

        if self.token:
            default_headers["Authorization"] = f"Bearer {self.token}"

        if headers:
            default_headers.update(headers)

        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=default_headers)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=default_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            self.log(f"{method} {endpoint} -> {response.status_code}")

            if response.status_code >= 400:
                self.log(f"Error response: {response.text}", "ERROR")
                response.raise_for_status()

            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {e}", "ERROR")
            raise

    def test_authentication(self) -> bool:
        """Test user login and get token"""
        self.log("🔐 Testing Authentication...")

        try:
            data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }

            response = self.make_request("POST", "/auth/login", data)

            if "access_token" in response:
                self.token = response["access_token"]
                self.user_id = response.get("user", {}).get("id")
                self.log("✅ Authentication successful!")
                return True
            else:
                self.log("❌ Authentication failed - no access token", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ Authentication failed: {e}", "ERROR")
            return False

    def test_add_to_cart(self) -> bool:
        """Test adding items to cart"""
        self.log("🛒 Testing Add to Cart...")

        try:
            data = {
                "card_variant_id": TEST_CARD_VARIANT_ID,
                "quantity": 1
            }

            response = self.make_request("POST", "/cart/add", data)

            if response.get("success"):
                self.cart_id = response.get("cart_id")
                self.log("✅ Item added to cart successfully!")
                return True
            else:
                self.log("❌ Failed to add item to cart", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ Add to cart failed: {e}", "ERROR")
            return False

    def test_payment_flow(self) -> bool:
        """Test the complete payment flow"""
        self.log("💳 Testing Payment Flow...")

        try:
            data = {
                "phone_number": TEST_PHONE,
                "coupon_codes": []  # Empty array for no coupons
            }

            response = self.make_request("POST", "/sales/create-from-cart", data)

            # Check if payment was initiated
            if "payment_response" in response:
                payment_response = response["payment_response"]
                self.transaction_id = response.get("transaction_id")

                self.log("✅ Payment initiated successfully!")
                self.log(f"Transaction ID: {self.transaction_id}")
                self.log(f"Payment Response: {payment_response}")

                # Check if Paypack accepted the payment request
                if "errors" not in payment_response:
                    self.log("✅ Paypack accepted payment request!")
                    return True
                else:
                    self.log(f"❌ Paypack rejected payment: {payment_response['errors']}", "ERROR")
                    return False
            else:
                self.log("❌ Payment initiation failed", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ Payment flow failed: {e}", "ERROR")
            return False

    def test_webhook_simulation(self) -> bool:
        """Test webhook callback simulation"""
        self.log("🔄 Testing Webhook Simulation...")

        if not self.transaction_id:
            self.log("❌ No transaction ID available for webhook test", "ERROR")
            return False

        try:
            # Simulate successful payment webhook
            webhook_data = {
                "event": "cashin:success",
                "data": {
                    "ref": self.transaction_id,
                    "amount": 1000,  # Test amount
                    "fee": 0,
                    "client": "test-client-id",
                    "timestamp": "2024-01-01T12:00:00.000Z"
                }
            }

            response = self.make_request("POST", "/payments/webhook", webhook_data)

            if response.get("status") == "success":
                self.log("✅ Webhook processed successfully!")
                return True
            else:
                self.log("❌ Webhook processing failed", "ERROR")
                return False

        except Exception as e:
            self.log(f"❌ Webhook test failed: {e}", "ERROR")
            return False

    def run_full_test(self) -> bool:
        """Run the complete payment flow test"""
        self.log("🚀 Starting Complete Payment Flow Test")
        self.log("=" * 50)

        tests = [
            ("Authentication", self.test_authentication),
            ("Add to Cart", self.test_add_to_cart),
            ("Payment Flow", self.test_payment_flow),
            ("Webhook Simulation", self.test_webhook_simulation),
        ]

        results = []
        for test_name, test_func in tests:
            self.log(f"\n📋 Running: {test_name}")
            success = test_func()
            results.append((test_name, success))

            if not success and test_name in ["Authentication", "Add to Cart"]:
                self.log(f"❌ Critical test '{test_name}' failed. Stopping test suite.", "ERROR")
                break

        # Summary
        self.log("\n" + "=" * 50)
        self.log("📊 TEST RESULTS SUMMARY:")

        all_passed = True
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
            if not success:
                all_passed = False

        if all_passed:
            self.log("\n🎉 ALL TESTS PASSED! Payment integration is working correctly!")
        else:
            self.log("\n⚠️  Some tests failed. Check the logs above for details.")

        return all_passed

def main():
    print("🧪 Payment Flow Integration Test")
    print("This script will test your complete payment flow from authentication to webhook")
    print()

    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
        else:
            print("❌ Server not responding. Please start your FastAPI server first.")
            return
    except:
        print("❌ Cannot connect to server. Please start your FastAPI server first.")
        print("Run: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")
        return

    print("\n⚠️  IMPORTANT: Please update the test credentials in this script:")
    print(f"   - TEST_EMAIL: {TEST_EMAIL}")
    print(f"   - TEST_PASSWORD: {TEST_PASSWORD}")
    print(f"   - TEST_CARD_VARIANT_ID: {TEST_CARD_VARIANT_ID}")
    print()

    tester = PaymentFlowTester()
    success = tester.run_full_test()

    if success:
        print("\n🎉 Payment integration test completed successfully!")
        print("Your Paypack payment flow is working correctly.")
    else:
        print("\n❌ Payment integration test failed.")
        print("Please check the error messages above and fix any issues.")

if __name__ == "__main__":
    main()
