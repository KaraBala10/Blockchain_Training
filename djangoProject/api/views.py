import json
import random

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from web3 import Web3

from .models import CustomUser
from .utils import perform_transfer

web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER))
contract_path = "/home/karabala/my_repos/Blockchain_Training/project/build/contracts/VirtualCurrency.json"

with open(contract_path) as f:
    contract_json = json.load(f)
    contract_abi = contract_json["abi"]

CONTRACT_ADDRESS = settings.CONTRACT_ADDRESS

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)


@api_view(["POST"])
@permission_classes([AllowAny])  # Allow unauthenticated access
def register_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=HTTP_400_BAD_REQUEST,
        )

    try:
        # Check if username already exists
        if CustomUser.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists."},
                status=HTTP_400_BAD_REQUEST,
            )

        # Create the user
        user = CustomUser.objects.create_user(username=username, password=password)

        # Generate a random VC balance (e.g., between 100 and 1000)
        random_vc_balance = random.randint(100, 1000)

        # Perform the token transfer from the central account to the new user
        tx_hash = perform_transfer(
            private_key=settings.CENTRAL_ACCOUNT_PRIVATE_KEY,
            to_address=user.wallet_address,
            amount=random_vc_balance * (10**18),  # Assuming VC has 18 decimals
        )

        # Create a token for the user
        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Account created successfully!",
                "username": user.username,
                "initial_vc_balance": random_vc_balance,
                "tx_hash": tx_hash,
                "token": token.key,  # Return the token upon registration
            },
            status=HTTP_200_OK,
        )
    except Exception as e:
        return Response({"error": str(e)}, status=HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def balance_view(request):
    try:
        user = request.user
        ether_balance = web3.eth.get_balance(user.wallet_address)
        readable_ether_balance = Web3.from_wei(ether_balance, "ether")
        token_balance = contract.functions.balanceOf(user.wallet_address).call()
        readable_token_balance = Web3.from_wei(token_balance, "ether")

        return Response(
            {
                "ether_balance": readable_ether_balance,
                "token_balance": readable_token_balance,
            },
            status=HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve balance: {str(e)}"},
            status=HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def transfer_view(request):
    to_username = request.data.get("to_username")
    amount = request.data.get("amount")

    if not to_username or not amount:
        return Response(
            {"error": "Recipient username and amount are required."},
            status=HTTP_400_BAD_REQUEST,
        )

    try:
        recipient = CustomUser.objects.get(username=to_username)
        to_address = recipient.wallet_address
        amount_in_wei = int(float(amount) * (10**18))

        sender = request.user
        tx_hash = perform_transfer(sender.private_key, to_address, amount_in_wei)

        return Response(
            {"message": "Transaction successful!", "tx_hash": tx_hash},
            status=HTTP_200_OK,
        )
    except CustomUser.DoesNotExist:
        return Response(
            {"error": "Recipient user does not exist."}, status=HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {"error": f"Transaction failed: {str(e)}"}, status=HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def profile_view(request):
    return Response({"wallet_address": request.user.wallet_address}, status=HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])  # Only admin users can access this endpoint
def list_accounts_view(request):
    """
    Retrieves a list of all user accounts with their ETH and VC balances.
    """
    try:
        users = CustomUser.objects.all()
        accounts = []

        for user in users:
            ether_balance = web3.eth.get_balance(user.wallet_address)
            readable_ether_balance = Web3.from_wei(ether_balance, "ether")

            token_balance = contract.functions.balanceOf(user.wallet_address).call()
            readable_token_balance = Web3.from_wei(token_balance, "ether")

            accounts.append(
                {
                    "username": user.username,
                    "wallet_address": user.wallet_address,
                    "ether_balance": str(readable_ether_balance),
                    "token_balance": str(readable_token_balance),
                }
            )

        return Response(
            {"accounts": accounts},
            status=HTTP_200_OK,
        )

    except Exception as e:
        return Response(
            {"error": f"Failed to retrieve accounts: {str(e)}"},
            status=HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def custom_login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "message": "Login successful!",
                "token": token.key,  # Provide the token to the client
                "user_id": user.id,
                "username": user.username,
            },
            status=200,
        )
    else:
        return Response({"message": "Invalid credentials."}, status=400)
