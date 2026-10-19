import requests
from django.conf import settings

import hmac
import hashlib

# Get this from your Linkio dashboard settings
LINK_WEBHOOK_SECRET = LINK_SK = getattr(settings, 'LINKIO_SECRET_KEY')
def verify_webhook_signature(payload_body, signature_header):
    """
    Verifies the HMAC SHA256 signature of the incoming webhook.
    payload_body: The raw bytes of the request body (request.body)
    """
    if not signature_header:
        return False
        
    expected_signature = hmac.new(
        key=LINK_WEBHOOK_SECRET.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Timing-safe comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature_header)








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
























# import requests

# link_sk = ''
# link_sk_live = ''
# link_tag = 'Blackspectre'
# Bid = '161791100802714'
# link_api = "https://api.linkio.world"




# ###########################################################
# # get link supported banks
# def get_supported_banks():

#     url = f"{link_api}/static/v2/payment_banks?currency=NGN"

#     headers = {"ngnc-sec-key": link_sk}

#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         print(response.json())
#         return response.json()
#     else:
#         print(f"Error {response.status_code}: {response.text}")




# # # ###############################################################################################################################
# # #get vendor bank details

# def get_vendors_list(currency = "NGN"):
#     url = f"{link_api}/static/v2/payment_vendors?currency={currency}"


#     headers = {
#         "ngnc-sec-key": link_sk,
#     }

#     # Add params=params to the request
#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         print(response.json())
#         return response.json()
#     else:
#         print(f"Error {response.status_code}: {response.text}")


# ############################################################################################################


# # Retail Rates Onramp
# def get_retail_rates(trx_type):
#     url = f"{link_api}/transactions/v2/retail_rate"

#     headers = {"ngnc-sec-key": link_sk,}
#     params = {
#         'trx_type' : trx_type
#     }
#     response = requests.get(url, params=params, headers=headers)

#     if response.status_code == 200:
#         print(response.json())
#         return response.json()
#     else:
#         print(f"Error {response.status_code}: {response.text}")


# ######################################################


# # Retail Rates Offramp

#     # url = f"{link_api}/transactions/v2/retail_rate"

#     # headers = {"ngnc-sec-key": link_sk,}
#     # params = {
#     #     'trx_type' : trx_type
#     # }
#     # response = requests.get(url, params=params, headers=headers)


#     # if response.status_code == 200:
#     #     print(response.json())
#     #     return response.json()
#     # else:
#     #     print(f"Error {response.status_code}: {response.text}")


# ########################################################


# # #initiate Onramp
# def initiate_onramp(currency,amount,vendor_bank,vendor_number,vendor_name,wallet_address,bank_name,account_number):
#     url = f"{link_api}/transactions/v2/onramp"

#     # payload = {
#     #     "currency": "NGN",
#     #     "amount": "15000",
#     #     "vendor_bank": "Prov Bank",
#     #     "vendor_number": "*****54964",
#     #     "vendor_name": "divine",
#     #     "wallet_address": "0x38d8E9aa8b3699BA4e6bf812933011928eCEefB7",
#     #     "network": "polygon",
#     #     "bank_name": "Access Bank",
#     #     "account_number": "1802677543",
#     #     "stables":"USDC"
#     #     # "routing_number": "<string>",
#     #     # "bank_address": "<string>"
#     # }

#     payload = {
#             "currency": currency,
#             "amount": amount,
#             "vendor_bank": vendor_bank,
#             "vendor_number": vendor_number,
#             "vendor_name": vendor_name,
#             "wallet_address": wallet_address,
#             "network": "polygon",
#             "bank_name": bank_name,
#             "account_number": account_number,
#             "stables":"USDC"
#             # "routing_number": "<string>",
#             # "bank_address": "<string>"
#         }


#     headers = {
#         "ngnc-sec-key": link_sk,
#         "Content-Type": "application/json"
#     }

#     response = requests.post(url, json=payload, headers=headers)

#     if response.status_code == 200:
#         print(response.json())
#         return response.json()
#     else:
#         print(f"Error {response.status_code}: {response.text}")


# #######################################################################################

# # #offramp
# def initiate_offramp(currency,amount,wallet_address,bank_name,account_number,account_name):
#     url = f"{link_api}/transactions/v2/offramp"

#     # payload = {
#     #     "type": "bank",
#     #     "amount": "5000",
#     #     "currency": "NGN",
#     #     "bank_name": "Access Bank", #must be a payout bank supported by link
#     #     "account_number": "1802677543",
#     #     "account_name": "John Doe",
#     #     "wallet_address": "0x38d8E9aa8b3699BA4e6bf812933011928eCEefB7",
#     #     "network": "polygon",
#     #     "stables":"USDC",
#     #     # "routing_number": "<string>",
#     #     # "account_type": "checkings",
#     #     "chargeFeeOnRequest": True
#     # }


#     payload = {
#         "type": "bank",
#         "amount": amount,
#         "currency": currency,
#         "bank_name": bank_name, #must be a payout bank supported by link
#         "account_number": account_number,
#         "account_name": account_name,
#         "wallet_address": wallet_address,
#         "network": "polygon",
#         "stables":"USDC",
#         # "routing_number": "<string>",
#         # "account_type": "checkings",
#         "chargeFeeOnRequest": True
#     }



#     headers = {
#         "ngnc-sec-key": link_sk,
#         "Content-Type": "application/json"
#     }

#     response = requests.post(url, json=payload, headers=headers)

#     if response.status_code == 200:
#         print(response.json())
#         return response.json()
#     else:
#         print(f"Error {response.status_code}: {response.text}")