# Paypack Only Integration TODO

- [x] Add Paypack settings to config.py (PAYPACK_CLIENT_ID, PAYPACK_CLIENT_SECRET, PAYPACK_BASE_URL, PAYPACK_WEBHOOK_SECRET)
- [x] Update PaymentService enum to only include PAYPACK = "paypack"
- [x] Keep PaypackCashinSchema in payment.py
- [x] Keep token management: get_access_token function in payment.py
- [x] Update PaymentController __init__ to only accept PaypackCashinSchema
- [x] Keep paypack_cashin method in PaymentController
- [x] Update PaymentController __call__ to only handle PAYPACK case
- [x] Update create_payment function to only handle PAYPACK
- [x] Update PaymentTransactionCallbackSchema to handle Paypack webhook payload
- [x] Update payment_callback_controller to handle Paypack payload
- [x] Update NetworkRegexSchema to only include paypack
- [x] Update phone_network_action to return "paypack" for all Rwandan numbers
- [x] Remove MTN and Airtel schemas and related code
- [x] Test the integration
