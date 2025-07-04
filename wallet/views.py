from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from web3 import Web3
from .models import Wallet, Transaction
from django.conf import settings
import stripe
from .utils import *
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
        from_coin = request.data.get("from_coin").lower()  
        to_coin = request.data.get("to_coin").lower()      
        amount = float(request.data.get("amount"))         

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


class ConvertToUZS(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        coin = request.data.get("coin", "eth").lower()
        amount = float(request.data.get("amount"))
        wallet = Wallet.objects.get(user=request.user)

        if coin == "eth" and wallet.eth_balance < amount:
            return Response({"error": "Yetarli ETH mavjud emas"}, status=400)
        if coin == "btc" and wallet.btc_balance < amount:
            return Response({"error": "Yetarli BTC mavjud emas"}, status=400)

        price = get_crypto_price_in_uzs(coin)
        uzs_value = amount * price

        if coin == "eth":
            wallet.eth_balance -= amount
        else:
            wallet.btc_balance -= amount
        wallet.save()

        return Response({
            "message": f"{amount} {coin.upper()} = {round(uzs_value, 2)} UZS",
            "converted": uzs_value
        })


class SendCrypto(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        coin = request.data.get("coin", "eth").lower()
        to_address = request.data.get("to_address")
        amount = float(request.data.get("amount"))
        wallet = Wallet.objects.get(user=request.user)

        if coin != "eth":
            return Response({"error": "Hozircha faqat ETH qo‘llab-quvvatlanadi"}, status=400)
        if wallet.eth_balance < amount:
            return Response({"error": "Balansda yetarli ETH yo‘q"}, status=400)

        tx_hash = send_eth_transaction(to_address, amount)
        wallet.eth_balance -= amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            to_address=to_address,
            amount=amount,
            tx_hash=tx_hash
        )

        return Response({"status": "yuborildi", "tx_hash": tx_hash})


class SendBTC(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        to_address = request.data.get("to_address")
        amount = float(request.data.get("amount"))
        wallet = Wallet.objects.get(user=request.user)

        if wallet.btc_balance < amount:
            return Response({"error": "Yetarli BTC mavjud emas"}, status=400)

        tx_hash = send_btc_transaction(to_address, amount)
        wallet.btc_balance -= amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            to_address=to_address,
            amount=amount,
            tx_hash=tx_hash
        )

        return Response({"status": "Yuborildi", "tx_hash": tx_hash})


class SyncWalletBalance(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.get(user=request.user)

        eth_balance = get_eth_balance_from_chain(wallet.address)
        btc_balance = get_btc_balance_from_chain(wallet.btc_address)

        wallet.eth_balance = eth_balance
        wallet.btc_balance = btc_balance
        wallet.save()

        return Response({
            "eth_balance": eth_balance,
            "btc_balance": btc_balance
        })


class TransactionHistory(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = Wallet.objects.get(user=request.user)
        txs = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        return Response([
            {
                "tx_hash": tx.tx_hash,
                "amount": tx.amount,
                "to": tx.to_address,
                "from": tx.from_address,
                "date": tx.created_at
            } for tx in txs
        ])
