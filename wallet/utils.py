from web3 import Web3
import secrets
import requests
from .models import Wallet, Transaction


def create_eth_wallet():
    account = Web3().eth.account.create(secrets.token_hex(32))
    return account.address, account.key.hex()

def get_eth_price_in_usd():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'ethereum',
        'vs_currencies': 'uzs'
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["ethereum"]["uzs"]


def get_btc_price_in_usd():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin',
        'vs_currencies': 'uzs'
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["bitcoin"]["uzs"]

def get_exchange_rate(from_coin: str, to_coin: str) -> float:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': from_coin,
        'vs_currencies': to_coin
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if from_coin in data and to_coin in data[from_coin]:
        return data[from_coin][to_coin]
    
    raise ValueError(f"Exchange rate for {from_coin} to {to_coin} not found.")

def update_wallet_balance(wallet: Wallet):
    eth_price = get_eth_price_in_usd()
    btc_price = get_btc_price_in_usd()

    eth_tx = Transaction.objects.filter(wallet=wallet, tx_hash__cointains='ETH')
    btc_tx = Transaction.objects.filter(wallet=wallet, tx_hash__cointains='BTC')

    wallet.eth_balance = sum(tx.amount for tx in eth_tx)
    wallet.btc_balance = sum(tx.amount for tx in btc_tx)
    wallet.save()