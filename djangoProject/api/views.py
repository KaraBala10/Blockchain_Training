import random

from django.conf import settings
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from web3 import Web3

from .models import CustomUser
from .utils import mint_tokens, perform_transfer

web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER))

CONTRACT_ABI = settings.CONTRACT_ABI
CONTRACT_ADDRESS = settings.CONTRACT_ADDRESS

CONTRACT = web3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=HTTP_400_BAD_REQUEST,
        )

    try:
        if CustomUser.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists."},
                status=HTTP_400_BAD_REQUEST,
            )

        user = CustomUser.objects.create_user(username=username, password=password)

        random_vc_balance = random.randint(100, 1000)

        tx_hash = perform_transfer(
            private_key=settings.CENTRAL_ACCOUNT_PRIVATE_KEY,
            to_address=user.wallet_address,
            amount=random_vc_balance,
        )

        token, created = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Account created successfully!",
                "username": user.username,
                "initial_vc_balance": random_vc_balance,
                "tx_hash": tx_hash,
                "token": token.key,
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
        token_balance = CONTRACT.functions.balanceOf(user.wallet_address).call()
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
        sender = request.user
        from_address = sender.wallet_address
        sender_private_key = sender.private_key
        amount_in_wei = int(float(amount) * (10**18))
        central_private_key = settings.CENTRAL_ACCOUNT_PRIVATE_KEY
        tx_hash = perform_transfer(
            central_private_key,
            from_address,
            to_address,
            amount_in_wei,
            sender_private_key,
        )
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
@permission_classes([AllowAny])
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

            token_balance = CONTRACT.functions.balanceOf(user.wallet_address).call()
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
                "token": token.key,
                "user_id": user.id,
                "username": user.username,
            },
            status=200,
        )
    else:
        return Response({"message": "Invalid credentials."}, status=400)


@api_view(["POST"])
@permission_classes([AllowAny])
def mint_tokens_view(request):
    print(f"Authenticated user: {request.user}")
    print(f"Token used: {request.auth}")

    recipient_username = request.data.get("recipient_username")
    amount = request.data.get("amount")

    if not recipient_username or not amount:
        return Response(
            {"error": "Recipient username and amount are required."},
            status=HTTP_400_BAD_REQUEST,
        )

    try:
        recipient = CustomUser.objects.get(username=recipient_username)
        recipient_address = recipient.wallet_address
        amount_in_vc = float(amount)

        tx_hash = mint_tokens(
            private_key=settings.CENTRAL_ACCOUNT_PRIVATE_KEY,
            recipient_address=recipient_address,
            amount_in_vc=amount_in_vc,
        )

        return Response(
            {
                "message": "Tokens minted successfully!",
                "tx_hash": tx_hash,
                "recipient_username": recipient_username,
                "amount": amount_in_vc,
            },
            status=HTTP_200_OK,
        )
    except CustomUser.DoesNotExist:
        return Response(
            {"error": "Recipient user does not exist."},
            status=HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return Response(
            {"error": f"Minting failed: {str(e)}"},
            status=HTTP_400_BAD_REQUEST,
        )
