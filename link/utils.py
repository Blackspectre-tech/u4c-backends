import requests

link_sk = 'ngnc_s_tk_575c47a65aa3f258138b80c1a2bad35bab129a19c0956aabf25e1880fe159561'
link_sk_live = 'ngnc_s_lk_83a36b7503b9801d47c8f449d818c3ee2b1787f7122dbb134843c2075b42a292'
link_tag = 'Blackspectre'
Bid = '161791100802714'
link_api = "https://api.linkio.world"




###########################################################
# get link supported banks
def get_supported_banks():

    url = f"{link_api}/static/v2/payment_banks?currency=NGN"

    headers = {"ngnc-sec-key": link_sk}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")




# # ###############################################################################################################################
# #get vendor bank details

def get_vendors_list(currency = "NGN"):
    url = f"{link_api}/static/v2/payment_vendors?currency={currency}"


    headers = {
        "ngnc-sec-key": link_sk,
    }

    # Add params=params to the request
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")


############################################################################################################


# Retail Rates Onramp
def get_retail_rates(trx_type):
    url = f"{link_api}/transactions/v2/retail_rate"

    headers = {"ngnc-sec-key": link_sk,}
    params = {
        'trx_type' : trx_type
    }
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")


######################################################


# Retail Rates Offramp

    # url = f"{link_api}/transactions/v2/retail_rate"

    # headers = {"ngnc-sec-key": link_sk,}
    # params = {
    #     'trx_type' : trx_type
    # }
    # response = requests.get(url, params=params, headers=headers)


    # if response.status_code == 200:
    #     print(response.json())
    #     return response.json()
    # else:
    #     print(f"Error {response.status_code}: {response.text}")


########################################################


# #initiate Onramp
def initiate_onramp(currency,amount,vendor_bank,vendor_number,vendor_name,wallet_address,bank_name,account_number):
    url = f"{link_api}/transactions/v2/onramp"

    # payload = {
    #     "currency": "NGN",
    #     "amount": "15000",
    #     "vendor_bank": "Prov Bank",
    #     "vendor_number": "*****54964",
    #     "vendor_name": "divine",
    #     "wallet_address": "0x38d8E9aa8b3699BA4e6bf812933011928eCEefB7",
    #     "network": "polygon",
    #     "bank_name": "Access Bank",
    #     "account_number": "1802677543",
    #     "stables":"USDC"
    #     # "routing_number": "<string>",
    #     # "bank_address": "<string>"
    # }

    payload = {
            "currency": currency,
            "amount": amount,
            "vendor_bank": vendor_bank,
            "vendor_number": vendor_number,
            "vendor_name": vendor_name,
            "wallet_address": wallet_address,
            "network": "polygon",
            "bank_name": bank_name,
            "account_number": account_number,
            "stables":"USDC"
            # "routing_number": "<string>",
            # "bank_address": "<string>"
        }


    headers = {
        "ngnc-sec-key": link_sk,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")


#######################################################################################

# #offramp
def initiate_offramp(currency,amount,wallet_address,bank_name,account_number,account_name):
    url = f"{link_api}/transactions/v2/offramp"

    # payload = {
    #     "type": "bank",
    #     "amount": "5000",
    #     "currency": "NGN",
    #     "bank_name": "Access Bank", #must be a payout bank supported by link
    #     "account_number": "1802677543",
    #     "account_name": "John Doe",
    #     "wallet_address": "0x38d8E9aa8b3699BA4e6bf812933011928eCEefB7",
    #     "network": "polygon",
    #     "stables":"USDC",
    #     # "routing_number": "<string>",
    #     # "account_type": "checkings",
    #     "chargeFeeOnRequest": True
    # }


    payload = {
        "type": "bank",
        "amount": amount,
        "currency": currency,
        "bank_name": bank_name, #must be a payout bank supported by link
        "account_number": account_number,
        "account_name": account_name,
        "wallet_address": wallet_address,
        "network": "polygon",
        "stables":"USDC",
        # "routing_number": "<string>",
        # "account_type": "checkings",
        "chargeFeeOnRequest": True
    }



    headers = {
        "ngnc-sec-key": link_sk,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")







































# Ai suggestion

# #Retail Off-Ramp
# import requests

# url = "https://api.linkio.world/transactions/v2/offramp"

# payload = {
#     "type": "bank",               # 👈 REQUIRED: Typically "bank" or "crypto" depending on the endpoint variant
#     "business_id": "<string>",    # 👈 REQUIRED by Linkio's v2 offramp schema
#     "link_tag": "<string>",       # 👈 REQUIRED by Linkio's v2 offramp schema
#     "amount": "20",
#     "currency": "NGN",
#     "bank_name": "<string>",
#     "account_number": "<string>",
#     "account_name": "<string>",
#     "wallet_address": "<string>",
#     "network": "<string>",
#     "routing_number": "<string>",
#     "account_type": "checkings",
#     "chargeFeeOnRequest": True,
#     "stables": "USDC"
# }

# headers = {
#     "ngnc-sec-key": "ngnc_s_tk_575c47a65aa3f258138b80c1a2bad35bab129a19c0956aabf25e1880fe159561",
#     "Content-Type": "application/json"
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










# Grab the first available payment partner from the list
# if vendors_list:
#     first_vendor = vendors_list[0]
    
#     # Map these directly to your next payload:
#     vendor_bank = first_vendor.get("bank_name")
#     vendor_name = first_vendor.get("account_name")
#     vendor_number = first_vendor.get("account_number")





