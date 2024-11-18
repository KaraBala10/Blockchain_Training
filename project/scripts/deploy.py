from brownie import VirtualCurrency, accounts

# brownie accounts new karabala
# ganache --hardfork berlin --gasPrice 0
# brownie run scripts/deploy.py --network development


def main():
    dev_account = accounts[0]
    account = accounts.load("karabala")
    dev_account.transfer(account.address, "100 ether")

    contract = VirtualCurrency.deploy(1000000, {"from": account})
    contract.mint(account.address, 1000000 * 10**18, {"from": account})
    owner_balance = contract.balanceOf(account.address)

    print(f"Owner's Address: {account.address}")
    print(f"Owner's Private Key: {account.private_key}")
    print(f"Owner's Balance: {owner_balance / 10**18} VC")
