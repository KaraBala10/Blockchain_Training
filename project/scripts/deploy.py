from brownie import VirtualCurrency, accounts


def main():
    account = accounts[0]
    VirtualCurrency.deploy(1000000, {"from": account, "gas_price": "20 gwei"})
