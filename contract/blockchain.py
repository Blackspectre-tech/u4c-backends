from web3 import Web3
import json
from decouple import config

ALCHEMY_HTTP = config("ALCHEMY_HTTP")
ALCHEMY_WS = config("ALCHEMY_WS")
OWNER_PRIVATE_KEY = config("OWNER_PRIVATE_KEY")
w3 = Web3(Web3.HTTPProvider(ALCHEMY_HTTP))
# use wss if you need web socket event subscriptions: Web3(Web3.WebsocketProvider(ALCHEMY_WS))

# Load ABI (store ABI json file in your repo)
with open("contract/contract.json") as f:
    CONTRACT_ABI = json.load(f)

CONTRACT_ADDRESS = Web3.to_checksum_address(config("CONTRACT_ADDRESS"))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)

def owner_address():
    return w3.eth.account.from_key(OWNER_PRIVATE_KEY).address










def send_owner_tx(txn_func, tx_args: dict | None = None):
    """Signs & sends a tx from the owner account (Polygon)."""
    from_addr = owner_address()
    nonce = w3.eth.get_transaction_count(from_addr, "pending")

    # Base transaction fields
    base = {
        "from": from_addr,
        "nonce": nonce,
        "gasPrice": w3.eth.gas_price,  # current gas price from provider
        "chainId": getattr(w3.eth, "chain_id", 137),  # try provider chain_id, fallback to 137
    }
    if tx_args:
        base.update(tx_args)

    # Build tx
    built = txn_func.build_transaction(base)

    # Estimate gas and add buffer
    try:
        gas_estimate = w3.eth.estimate_gas(built)
        gas_with_buffer = int(gas_estimate * 1.2)
        built["gas"] = gas_with_buffer
    except Exception as e:
        # fallback default if estimate fails (adjust as needed)
        gas_with_buffer = built.get("gas", 500_000)
        built["gas"] = gas_with_buffer
        print("Gas estimation failed, using fallback:", e)

    print(f"Estimated gas: {gas_estimate if 'gas_estimate' in locals() else 'n/a'}, using: {built['gas']}")

    # Sign transaction
    if not OWNER_PRIVATE_KEY:
        raise RuntimeError("OWNER_PRIVATE_KEY is not set or is empty. Cannot sign transaction.")
    signed = w3.eth.account.sign_transaction(built, private_key=OWNER_PRIVATE_KEY)

    # Robustly extract raw tx bytes (try multiple attribute/key names)
    raw_tx = None
    # common attribute names used by eth-account/web3 versions
    if hasattr(signed, "rawTransaction"):
        raw_tx = getattr(signed, "rawTransaction")
    elif hasattr(signed, "raw_transaction"):
        raw_tx = getattr(signed, "raw_transaction")
    elif isinstance(signed, dict):
        # some versions may return a dict-like; try common keys
        raw_tx = signed.get("rawTransaction") or signed.get("raw_transaction") or signed.get("rawTx") or signed.get("raw_tx")
    else:
        # last resort: try 'raw' attribute
        raw_tx = getattr(signed, "raw", None)

    if raw_tx is None:
        # helpful debug output — do NOT print private key in production
        raise RuntimeError(
            "Could not find raw transaction on signed object. "
            f"Signed object type: {type(signed)}. Available attrs/keys: {dir(signed) if not isinstance(signed, dict) else list(signed.keys())}"
        )

    # Send raw transaction
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    return tx_hash.hex()














# def send_owner_tx(txn_func, tx_args: dict | None = None):
#     """Signs & sends a tx from the owner account (Polygon)."""
#     from_addr = owner_address()
#     nonce = w3.eth.get_transaction_count(from_addr, "pending")

#     # Base transaction fields
#     base = {
#         "from": from_addr,
#         "nonce": nonce,
#         "gasPrice": w3.eth.gas_price,  # current gas price from Polygon RPC
#         "chainId": 137,  # Polygon mainnet
#         # "chainId": 80001,  # Polygon Mumbai testnet
#     }
#     if tx_args:
#         base.update(tx_args)

#     # First build tx without gas limit
#     built = txn_func.build_transaction(base)

#     # Estimate gas from RPC node
#     gas_estimate = w3.eth.estimate_gas(built)

#     # Add buffer (20% extra)
#     gas_with_buffer = int(gas_estimate * 1.2)
#     built["gas"] = gas_with_buffer

#     print(f"Estimated gas: {gas_estimate}, using: {gas_with_buffer}")

#     # Sign & send
#     signed = w3.eth.account.sign_transaction(built, private_key=OWNER_PRIVATE_KEY)
#     tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

#     return tx_hash.hex()

def vault_bal():
    balance = w3.eth.get_balance(CONTRACT_ADDRESS)
    return w3.from_wei(balance, 'ether')

def platform_wallet_bal():
    # get balance in Wei
    balance_wei = w3.eth.get_balance(config("PLATFORM_WALLET_ADDRESS"))
    balance = w3.from_wei(balance_wei, 'ether')
    return float(f"{balance:.2f}")

#print(contract.functions.platformWallet().call())


# def send_owner_tx(txn_func, tx_args: dict | None = None):
#     """Signs & sends a tx from the owner account."""
#     from_addr = owner_address()
#     #nonce = w3.eth.get_transaction_count(from_addr)
#     nonce = w3.eth.get_transaction_count(from_addr, "pending")
#     base = {
#         "chainId": 137,  # for Polygon mainnet
#         "from": from_addr,
#         "nonce": nonce,
#         "gas": 300_000,
#         "gasPrice": w3.eth.gas_price,
#         # Optionally set chainId if your RPC needs it:
#         # "chainId": 11155111,  # sepolia
#     }
#     if tx_args:
#         base.update(tx_args)

#     built = txn_func.build_transaction(base)
#     signed = w3.eth.account.sign_transaction(built, private_key=OWNER_PRIVATE_KEY)
#     tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
#     return tx_hash.hex()


