import secrets

from django.conf import settings
from web3 import Web3
from web3.middleware import geth_poa_middleware

from .models import CustomUser

web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER))
web3.middleware_onion.inject(geth_poa_middleware, layer=0)

CONTRACT_ABI = settings.CONTRACT_ABI
CONTRACT_ADDRESS = settings.CONTRACT_ADDRESS
CONTRACT = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)


def create_user_account(username, password):
    account = web3.eth.account.create(secrets.token_hex(16))
    user = CustomUser.objects.create_user(
        username=username,
        password=password,
        wallet_address=account.address,
        private_key=account.key.hex(),
    )
    return user


def perform_transfer(
    central_private_key, from_address, to_address, amount, sender_private_key
):
    try:
        central_account = web3.eth.account.from_key(central_private_key)
        central_address = central_account.address
        sender_nonce = web3.eth.get_transaction_count(from_address)
        approve_tx = CONTRACT.functions.approve(
            central_address, amount
        ).build_transaction(
            {
                "from": from_address,
                "gas": 200000,
                "gasPrice": web3.to_wei("0", "gwei"),
                "nonce": sender_nonce,
                "chainId": 1337,
            }
        )
        signed_approve_tx = web3.eth.account.sign_transaction(
            approve_tx, sender_private_key
        )
        web3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
        nonce = web3.eth.get_transaction_count(central_address)
        transaction = CONTRACT.functions.transferFrom(
            from_address, to_address, amount
        ).build_transaction(
            {
                "from": central_address,
                "gas": 200000,
                "gasPrice": web3.to_wei("0", "gwei"),
                "nonce": nonce,
                "chainId": 1337,
            }
        )
        signed_transaction = web3.eth.account.sign_transaction(
            transaction, central_private_key
        )
        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        return tx_hash.hex()
    except Exception as e:
        print(f"Transaction failed: {str(e)}")
        raise


def mint_tokens(private_key, recipient_address, amount_in_vc):
    try:
        sender_account = web3.eth.account.from_key(private_key)
        amount_in_contract_scale = int(amount_in_vc)
        gas_price = web3.eth.gas_price
        nonce = web3.eth.get_transaction_count(sender_account.address)
        transaction = CONTRACT.functions.mint(
            recipient_address, amount_in_contract_scale
        ).build_transaction(
            {
                "from": sender_account.address,
                "gas": 2000000,
                "gasPrice": gas_price,
                "nonce": nonce,
                "chainId": 1337,
            }
        )
        signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        return tx_hash.hex()
    except Exception as e:
        print(f"Error minting tokens: {str(e)}")
        raise
