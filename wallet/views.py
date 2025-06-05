from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from web3 import Web3
from .models import Wallet, Transaction
from django.conf import settings
import stripe
from .utils import get_eth_price_in_usd, get_btc_price_in_usd, get_exchange_rate, update_wallet_balance
from models import User
import time

stripe.api_key = settings.STRIPE_SECRET_KEY

INFURA_URL = "https://mainnet.infura.io/v3/c277d602861042f58ad5e60a563859eb"
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

class SendTransaction(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        wallet = Wallet.objects.get(user=request.user)
        to_address = request.data.get("to_address")
        amount = float(request.data.get("amount"))
        nonce = w3.eth.get_transaction_count(wallet.address)

        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': w3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': w3.to_wei('50', 'gwei')
        }

        signed_tx = w3.eth.account.sign_transaction(tx, wallet.private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash_hex = tx_hash.hex()

        Transaction.objects.create(
            wallet=wallet,
            to_address=to_address,
            amount=amount,
            tx_hash=tx_hash_hex
        )

        return Response({'status': 'success', 'tx_hash': tx_hash_hex})


class ConvertUzsToEth(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        uzs_amount = float(request.data.get("amount"))
        eth_price = self.get_eth_price_in_uzs()
        eth_amount = uzs_amount / eth_price

        return Response({
            'uzs': uzs_amount,
            'eth': eth_price,
            'converted_eth': round(eth_amount, 8)
        })
    

class BuyCrypto(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usd_amount = float(request.data.get("amount"))
        crypto_type = request.data.get("crypto_type", "eth").lower()
        wallet = Wallet.objects.get(user=request.user)

        price = get_eth_price_in_usd() if crypto_type == "eth" else None
        crypto_amount = usd_amount / price

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(usd_amount * 100),
                    'product_data': {'name': f'Buy {crypto_type.upper()}'},
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://example.com/success/',
            cancel_url='https://example.com/cancel/',
            metadata={
                'user_id': str(request.user.id),
                'crypto_type': crypto_type,
                'crypto_amount': str(crypto_amount)
            }
        )
        return Response({'checkout_url': session.url})

class PaymentWebhook(APIView):
    permission_classes = []

    def post(self, request):
        data = request.data
        user_id = data.get('metadata', {}).get('user_id')
        crypto_type = data.get('metadata', {}).get('crypto_type', 'eth')
        crypto_amount = float(data.get('metadata', {}).get('crypto_amount', 0))

        user = User.objects.get(id=user_id)
        wallet = Wallet.objects.get(user=user)

        Transaction.objects.create(
            wallet=wallet,
            to_address=wallet.address,
            amount=crypto_amount,
            tx_hash=f"BUY-{crypto_type.upper()}-{int(time.time())}"
        )

        return Response({'status': 'ok'})



class BuyCryptoStripe(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        usd_amount = float(request.data.get("amount"))
        crypto_type = request.data.get("crypto", "eth").lower()
        wallet = Wallet.objects.get(user=request.user)

        if crypto_type == "eth":
            price = get_eth_price_in_usd()
        elif crypto_type == "btc":
            price = get_btc_price_in_usd()
        else:
            return Response({"error": "Unsupported crypto type"}, status=400)

        crypto_amount = usd_amount / price

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(usd_amount * 100),
                    'product_data': {'name': f'Buy {crypto_type.upper()}'}
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='https://yourdomain.com/success',
            cancel_url='https://yourdomain.com/cancel',
            metadata={
                'user_id': str(request.user.id),
                'crypto_type': crypto_type,
                'crypto_amount': str(crypto_amount)
            }
        )

        return Response({'checkout_url': session.url})
    

class PaymentWebhook(APIView):
    permission_classes = []

    def post(self, request):
        data = request.data
        user_id = data.get('metadata', {}).get('user_id')
        crypto_type = data.get('metadata', {}).get('crypto_type', 'btc')
        crypto_amount = float(data.get('metadata', {}).get('crypto_amount', 0))

        user = User.objects.get(id=user_id)
        wallet = Wallet.objects.get(user=user)

        Transaction.objects.create(
            wallet=wallet,
            to_address=wallet.address,
            amount=crypto_amount,
            tx_hash=f"BUY-{crypto_type.upper()}-{int(time.time())}"
        )

        return Response({'status': 'ok'})
    


class ExchangeCrypto(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from_coin = request.data.get("from_coin").lower()  # eth
        to_coin = request.data.get("to_coin").lower()      # btc
        amount = float(request.data.get("amount"))         # 0.1

        rate = get_exchange_rate(from_coin, to_coin)
        to_amount = amount * rate

        wallet = Wallet.objects.get(user=request.user)

        Transaction.objects.create(
            wallet=wallet,
            from_address=wallet.address,
            to_address=wallet.address,
            amount=to_amount,
            tx_hash=f"SWAP-{from_coin.upper()}-{to_coin.upper()}-{int(time.time())}"
        )

        return Response({
            "message": "Crypto exchanged successfully",
            "from_coin": from_coin,
            "to_coin": to_coin,
            "rate": rate,
            "converted_amount": to_amount
        })


class GetWalletBalance(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.get(user=request.user)
        update_wallet_balance(wallet)

        return Response({
            'eth_balance': wallet.eth_balance,
            'btc_balance': wallet.btc_balance,
        })

