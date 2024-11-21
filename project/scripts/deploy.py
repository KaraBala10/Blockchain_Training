import os
import re
import shutil

from brownie import VirtualCurrency, accounts

# brownie accounts new karabala
# ganache --hardfork berlin --gasPrice 0
# brownie run scripts/deploy.py --network development


def update_contract_address_in_settings(contract_address):
    """Update CONTRACT_ADDRESS in settings.py"""
    # Define the path to settings.py
    settings_path = os.path.join(
        os.getcwd(), "djangoProject", "djangoProject", "settings.py"
    )

    # Read the settings.py file
    with open(settings_path, "r") as file:
        settings = file.read()

    # Check if CONTRACT_ADDRESS exists and update or add it
    if "CONTRACT_ADDRESS" in settings:
        settings = re.sub(
            r'CONTRACT_ADDRESS = ".*?"',
            f'CONTRACT_ADDRESS = "{contract_address}"',
            settings,
        )
    else:
        settings += f'\nCONTRACT_ADDRESS = "{contract_address}"\n'

    # Write the updated content back to settings.py
    with open(settings_path, "w") as file:
        file.write(settings)

    print(f"Updated CONTRACT_ADDRESS in settings.py to: {contract_address}")


def move_contract_json():
    """Move VirtualCurrency.json to the Django project directory"""
    source_path = os.path.join(
        os.getcwd(), "build", "contracts", "VirtualCurrency.json"
    )
    target_dir = os.path.join(os.getcwd(), "djangoProject", "build", "contracts")

    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)

    # Copy the JSON file to the target directory
    target_path = os.path.join(target_dir, "VirtualCurrency.json")
    shutil.copy(source_path, target_path)

    print(f"Moved {source_path} to {target_path}")


def main():
    # Load the account
    password = os.getenv("BROWNIE_PASSWORD", "!@#")
    if not password:
        raise ValueError("Environment variable BROWNIE_PASSWORD is not set.")

    dev_account = accounts[0]
    account = accounts.load("karabala", password=password)
    dev_account.transfer(account.address, "100 ether")

    # Deploy the contract
    contract = VirtualCurrency.deploy(1000000, {"from": account})
    contract.mint(account.address, 1000000 * 10**18, {"from": account})
    owner_balance = contract.balanceOf(account.address)

    print(f"Owner's Address: {account.address}")
    print(f"Owner's Private Key: {account.private_key}")
    print(f"Owner's Balance: {owner_balance / 10**18} VC")
    print(f"Contract Address: {contract.address}")

    # Update settings.py with the contract address
    update_contract_address_in_settings(contract.address)

    # Move the contract JSON file to the Django project
    move_contract_json()
