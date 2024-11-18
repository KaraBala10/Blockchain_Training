import json
import secrets
from pathlib import Path

from django.conf import settings
from web3 import Web3
from web3.middleware import geth_poa_middleware

from .models import CustomUser

web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
contract_path = BASE_DIR / "project" / "build" / "contracts" / "VirtualCurrency.json"

if not contract_path.exists():
    raise FileNotFoundError(f"ملف العقد الذكي غير موجود في المسار: {contract_path}")

with open(contract_path) as f:
    contract_json = json.load(f)
    contract_abi = contract_json["abi"]

CONTRACT_ADDRESS = settings.CONTRACT_ADDRESS

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)


def create_user_account(username, password):
    account = web3.eth.account.create(secrets.token_hex(16))
    user = CustomUser.objects.create_user(
        username=username,
        password=password,
        wallet_address=account.address,
        private_key=account.key.hex(),
    )
    return user


def perform_transfer(private_key, to_address, amount):
    try:
        account = web3.eth.account.from_key(private_key)
        transaction = contract.functions.transfer(to_address, amount).build_transaction(
            {
                "from": account.address,
                "gas": 2000000,
                "maxPriorityFeePerGas": 0,
                "nonce": web3.eth.get_transaction_count(account.address),
                "chainId": 1337,
            }
        )
        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        return tx_hash.hex()
    except Exception as e:
        print(f"Transaction failed: {str(e)}")
        raise


def fund_account(sender_private_key, recipient_address, amount_in_ether):
    try:
        sender_account = web3.eth.account.from_key(sender_private_key)
        amount_in_wei = web3.to_wei(amount_in_ether, "ether")
        transaction = {
            "to": recipient_address,
            "value": amount_in_wei,
            "gas": 21000,
            "maxPriorityFeePerGas": 0,
            "nonce": web3.eth.get_transaction_count(sender_account.address),
            "chainId": 1337,
        }
        signed_transaction = web3.eth.account.sign_transaction(
            transaction, sender_private_key
        )
        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        print(f"Transaction successful! Tx Hash: {web3.to_hex(tx_hash)}")
        return tx_hash.hex()
    except Exception as e:
        print(f"Error funding account: {str(e)}")
        raise


sender_private_key = (
    "0xf816e89b73ba11812c01f5380444c29b8d0212e620ae9e50d86c0e47d982ec66"
)
recipient_address = "0x0Cb52b7Df2ba1E9155a202201C65a0463755bE02"
amount_in_ether = 10
# fund_account(sender_private_key, recipient_address, amount_in_ether)


def fund_account_with_vc(sender_private_key, recipient_address, amount_in_vc):
    try:
        # Retrieve sender account and compute amount in wei
        sender_account = web3.eth.account.from_key(sender_private_key)
        amount_in_wei = int(amount_in_vc * (10**18))

        # Debugging: Print details
        print(f"Sender Address: {sender_account.address}")
        print(f"Recipient Address: {recipient_address}")
        print(f"Amount in Wei: {amount_in_wei}")

        # Check sender balance
        sender_balance = contract.functions.balanceOf(sender_account.address).call()
        print(f"Sender VC Balance: {sender_balance / (10 ** 18)}")
        if sender_balance < amount_in_wei:
            raise ValueError("Sender does not have enough VC tokens for the transfer.")

        # Build the transaction
        nonce = web3.eth.get_transaction_count(sender_account.address)
        print(f"Nonce: {nonce}")
        transaction = contract.functions.transfer(
            recipient_address, amount_in_wei
        ).build_transaction(
            {
                "from": sender_account.address,
                "gas": 2000000,
                "maxPriorityFeePerGas": 0,
                "nonce": nonce,
                "chainId": 1337,
            }
        )
        signed_transaction = web3.eth.account.sign_transaction(
            transaction, sender_private_key
        )
        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        print(f"Transaction sent! Tx Hash: {web3.to_hex(tx_hash)}")

        # Wait for receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Transaction Receipt: {receipt}")

        return tx_hash.hex()
    except Exception as e:
        print(f"Error funding account with VC: {str(e)}")
        raise


amount_in_vc = 100
# fund_account_with_vc(sender_private_key, recipient_address, amount_in_vc)
