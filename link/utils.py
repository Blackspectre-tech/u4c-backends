import requests

link_sk = 'ngnc_s_tk_575c47a65aa3f258138b80c1a2bad35bab129a19c0956aabf25e1880fe159561'
link_sk_live = 'ngnc_s_lk_83a36b7503b9801d47c8f449d818c3ee2b1787f7122dbb134843c2075b42a292'
link_tag = 'Blackspectre'
Bid = '161791100802714'
#Retail On-Ramp

# url = "https://api.linkio.world/transactions/v1/onramp"

# payload = {
#     "business_id": Bid,
#     "link_tag": link_tag,
#     "type": "string",
#     "amount": 0, 
#     "vendor_number": "string",
#     "vendor_name": "string",
#     "vendor_bank": "string",
#     "account_number": "string",
#     "bank_name": "string",
#     "network": "polygon",
#     "wallet_address": "string"
# }
# headers = {
#     "accept": "application/json",
#     "ngnc-sec-key": link_sk,
#     "content-type": "application/json"
# }

# response = requests.post(url, json=payload, headers=headers)

# print(response.text)








# #Retail Off-Ramp

# import requests

# url = "https://api.linkio.world/transactions/v1/offramp"

# payload = {
#     "business_id": "string",  
#     "link_tag": "string", 
#     "type": "string", 
#     "amount": 0,  
#     "account_name": "string", 
#     "account_number": "string", 
#     "bank_name": "string", 
#     "network": "string",
#     "wallet_address": "string"
# }
# headers = {
#     "accept": "application/json",
#     "ngnc-sec-key": link_sk,
#     "content-type": "application/json"
# }

# response = requests.post(url, json=payload, headers=headers)

# print(response.text)






#Retail Rates


# url = "https://api.linkio.world/otc/rate_quote"

# params = {
#     "currency": "NGN",
#     "amount": "500000",
#     "trx_type": "onramp"
# }

# headers = {
#     "accept": "application/json",
#     "ngnc-sec-key": link_sk,
#     "content-type": "application/json"
# }

# response = requests.get(url, params=params, headers=headers)
# print(response.text)








''' 
Parameter	Type     Required	 Description
currency	string  	✓	    Fiat currency (e.g. NGN, USD)
amount	    string  	✓	    Amount in the fiat currency
trx_type	string  	✓	    Direction: onramp or offramp 
'''










#Ai codes

# import requests


# url = "https://api.linkio.world/transactions/v1/onramp"

# # 2. Replace placeholders with actual transaction details
# payload = { 
#     "business_id": Bid, 
#     "link_tag": link_tag, 
#     "type": "fiatToCrypto",  # Adjust based on valid transaction types
#     "amount": 5000,          # Must be greater than 0
#     "vendor_number": "1234567890", 
#     "vendor_name": "Vendor Name", 
#     "vendor_bank": "Bank Name", 
#     "account_number": "0123456789", 
#     "bank_name": "Customer Bank Name", 
#     "network": "polygon", 
#     "wallet_address": "0xYourWalletAddress..." 
# }

# headers = { 
#     "accept": "application/json", 
#     "ngnc-sec-key": link_sk, 
#     "content-type": "application/json" 
# }

# response = requests.post(url, json=payload, headers=headers)
# print(response.status_code)
# print(response.json())





#get bank details
import requests

LINKIO_SECRET_KEY = "sk_live_xxxxxxxxx" # Your active key

url = "https://api.linkio.world/transactions/v1/payment_vendors"

# PASS THE MISSING CURRENCY PARAMETER HERE
params = {
    "currency": "NGN"  # Tells Linkio to return Nigerian liquidation banks
}

headers = {
    "accept": "application/json",
    "ngnc-sec-key": link_sk,
    "content-type": "application/json"
}

# Add params=params to the request
response = requests.get(url, params=params, headers=headers)

if response.status_code == 200:
    print("Success! Vendor details retrieved:")
    print(response.json())
else:
    print(f"Error {response.status_code}: {response.text}")

# Grab the first available payment partner from the list
# if vendors_list:
#     first_vendor = vendors_list[0]
    
#     # Map these directly to your next payload:
#     vendor_bank = first_vendor.get("bank_name")
#     vendor_name = first_vendor.get("account_name")
#     vendor_number = first_vendor.get("account_number")
