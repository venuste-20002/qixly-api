#!/usr/bin/env python3
"""
Debug script for Paypack integration
Run this to test Paypack authentication and payment initiation
"""

import os
import sys
sys.path.append('.')

from src.config import settings
from src.helpers.payment import get_paypack_access_token, create_payment, PaymentSchemaPush

def test_paypack_auth():
    """Test Paypack authentication"""
    print("🔐 Testing Paypack Authentication...")
    print(f"Base URL: {settings.PAYPACK_BASE_URL}")
    print(f"Client ID: {settings.PAYPACK_CLIENT_ID}")
    print(f"Client Secret: {'*' * len(settings.PAYPACK_CLIENT_SECRET) if settings.PAYPACK_CLIENT_SECRET else 'None'}")

    try:
        token = get_paypack_access_token()
        print(f"✅ Authentication successful! Token: {token[:20]}...")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False

def test_payment_creation():
    """Test payment creation"""
    print("\n💳 Testing Payment Creation...")

    # Test data
    test_payment = PaymentSchemaPush(
        amount=1000,  # 1000 RWF
        reference="250788123456",
        network="paypack",
        phone_number="250788123456",
        app_transaction_id="test-123"
    )

    print(f"Payment Data: {test_payment.model_dump()}")

    try:
        result = create_payment(test_payment)
        print(f"✅ Payment creation successful!")
        print(f"Response: {result}")
        return True
    except Exception as e:
        print(f"❌ Payment creation failed: {e}")
        return False

def check_env_vars():
    """Check if required environment variables are set"""
    print("🔍 Checking Environment Variables...")

    required_vars = [
        'PAYPACK_CLIENT_ID',
        'PAYPACK_CLIENT_SECRET',
        'PAYPACK_BASE_URL',
        'PAYPACK_WEBHOOK_SECRET'
    ]

    missing = []
    for var in required_vars:
        value = getattr(settings, var, None)
        if not value:
            missing.append(var)
            print(f"❌ {var}: Not set")
        else:
            print(f"✅ {var}: Set ({len(str(value))} chars)")

    if missing:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing)}")
        print("Please set these in your .env file")
        return False

    return True

if __name__ == "__main__":
    print("🐛 Paypack Integration Debug Tool")
    print("=" * 50)

    # Check environment
    if not check_env_vars():
        sys.exit(1)

    print()

    # Test authentication
    auth_ok = test_paypack_auth()

    if auth_ok:
        # Test payment creation
        payment_ok = test_payment_creation()
        if payment_ok:
            print("\n🎉 All tests passed! Paypack integration should be working.")
        else:
            print("\n❌ Payment creation failed. Check the logs above for details.")
    else:
        print("\n❌ Authentication failed. Cannot proceed with payment tests.")

    print("\n💡 If tests fail, check:")
    print("   1. Your Paypack credentials in .env")
    print("   2. Network connectivity to Paypack API")
    print("   3. Paypack service status")
    print("   4. Application logs for detailed error messages")
