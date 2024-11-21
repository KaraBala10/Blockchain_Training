from brownie import accounts


def main():
    # we will set this variables inside .env file
    private_key = "0xa73b7e3cb494cccf5dc667fd9e37772e4b2de1c85f65c9d7b3e1d0bced9e34c6"
    account_name = "karabala"
    password = "!@#"

    # Add the account using the private key
    account = accounts.add(private_key)

    # Save the account with the specified name and password
    account.save(account_name, password=password)

    print(
        f"Account '{account_name}' with address {account.address} has been created and saved."
    )
