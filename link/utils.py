import requests
from django.conf import settings

import hmac
import hashlib

# Get this from your Linkio dashboard settings
LINKIO_WEBHOOK_SECRET = getattr(settings, 'LINKIO_WEBHOOK_KEY')

def verify_linkio_webhook(request):
    """
    Verifies that the incoming webhook is genuinely from Linkio by checking 
    the 'bridge-webhook-secret' header against your configured Webhook Secret.
    """
    # Django's request.headers dictionary automatically handles case-insensitivity,
    # so 'bridge-webhook-secret' will match 'Bridge-Webhook-Secret' or 'BRIDGE-WEBHOOK-SECRET'.
    incoming_secret = request.headers.get('bridge-webhook-secret')
    
    if not incoming_secret:
        print("Webhook Error: No bridge-webhook-secret header provided")
        return False
        
    # We use hmac.compare_digest instead of `==` for string comparison.
    # This prevents "timing attacks" where hackers guess tokens based on response times.
    is_valid = hmac.compare_digest(incoming_secret, LINKIO_WEBHOOK_SECRET)
    
    if not is_valid:
        print("Webhook Error: Secret token mismatch")
        
    return is_valid






# Fetch from settings, fallback to provided keys for development
LINK_SK = getattr(settings, 'LINKIO_SECRET_KEY')
# LINK_SK = "ngnc_s_lk_83a36b7503b9801d47c8f449d818c3ee2b1787f7122dbb134843c2075b42a292"
LINK_API = "https://api.linkio.world"

def _get_headers():
    return {
        "ngnc-sec-key": LINK_SK,
        "Content-Type": "application/json"
    }

def _handle_request(method, url, **kwargs):
    """Helper to handle requests and return (data, status_code) safely."""
    try:
        response = requests.request(method, url, headers=_get_headers(), **kwargs)
        return response.json(), response.status_code
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}, 503

def get_supported_banks(currency="NGN"):
    url = f"{LINK_API}/static/v2/payment_banks"
    return _handle_request("GET", url, params={"currency": currency})

def get_vendors_list(currency="NGN"):
    url = f"{LINK_API}/static/v2/payment_vendors"
    return _handle_request("GET", url, params={"currency": currency})

def get_retail_rates(trx_type):
    # Handles both 'onramp' and 'offramp' via the trx_type param
    url = f"{LINK_API}/transactions/v2/retail_rate"
    return _handle_request("GET", url, params={'trx_type': trx_type})

def initiate_onramp(payload):
    url = f"{LINK_API}/transactions/v2/onramp"
    return _handle_request("POST", url, json=payload)

def initiate_offramp(payload):
    url = f"{LINK_API}/transactions/v2/offramp"
    # Ensure type is set to bank as per your original code
    payload['type'] = payload.get('type', 'bank')
    payload['chargeFeeOnRequest'] = payload.get('chargeFeeOnRequest', True)
    return _handle_request("POST", url, json=payload)

# Fetch full transaction details (Onramp or Offramp)
def fetch_transaction(trx_ref):
    url = f"{LINK_API}/transactions/v2/fetch_transaction"
    return _handle_request("GET", url, params={'transaction_reference': trx_ref})

# Fetch the specific payout settlement status (Offramp only)
def get_payout_status(trx_ref):
    url = f"{LINK_API}/transactions/v2/direct_ramp/payout/status"
    return _handle_request("GET", url, params={'trx_reference': trx_ref})


def verify_account_number(account_number, bank_code):
    # verify user account number
    url = f"{LINK_API}/accounts/v2/verify_account_number"
    return _handle_request("GET", url, params={'account_number': account_number, 'bank_code': bank_code})


def get_deposit_wallets():
    url = f"{LINK_API}/static/v2/payment_wallets"
    return _handle_request("GET", url,)



# data, status = get_deposit_wallets()

# print(f"data: {data}")
