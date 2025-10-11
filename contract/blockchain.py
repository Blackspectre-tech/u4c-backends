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



erc20_abi = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]

usdc_token_address = '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359'
usdc_contract = w3.eth.contract(address=usdc_token_address, abi =erc20_abi)


def vault_bal():
    # balance = w3.eth.get_balance(CONTRACT_ADDRESS)
    # pol_balance = round(w3.from_wei(balance, 'ether'), 2)

    raw_balance = usdc_contract.functions.balanceOf(CONTRACT_ADDRESS).call()
    decimals = usdc_contract.functions.decimals().call()
    usdc_balance = raw_balance / (10 ** decimals)
    usdc_balance = round(usdc_balance, 2)
    
    return usdc_balance


def platform_wallet_bal():
    # # get balance in Wei
    wallet = config("SAFE_WALLET_ADDRESS")
    # balance_wei = w3.eth.get_balance(wallet)
    # pol = w3.from_wei(balance_wei, 'ether')

    raw_balance = usdc_contract.functions.balanceOf(wallet).call()
    decimals = usdc_contract.functions.decimals().call()
    usdc = raw_balance / (10 ** decimals)

    return round(usdc, 2)


def transaction_details(tx_hash: str):

    try:
        tx_details = w3.eth.get_transaction(tx_hash)
        if tx_details:
            data = dict(tx_details)
            
            # Convert hex values to integers and Wei to MATIC for readability
            # Some fields may be None if the transaction is pending
            if data['blockNumber'] is not None:
                data['blockNumber'] = w3.to_int(data['blockNumber'])
            
            data['gas'] = w3.to_int(data['gas'])
            data['value_matic'] = w3.from_wei(data['value'], 'ether')
            
            return data
        else:
            return None
    except Exception:
        return None

