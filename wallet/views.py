from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from web3 import Web3
from .models import Wallet, Transaction
from django.conf import settings

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