from web3 import Web3
import os
import secrets
import requests
from .models import Wallet, Transaction


web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/c277d602861042f58ad5e60a563859eb"))

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


def get_crypto_price_in_uzs(coin_id: str) -> float:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': coin_id,
        'vs_currencies': 'uzs'
    }
    response = requests.get(url, params=params)
    return response.json()[coin_id]['uzs']

def send_eth_transaction(to_address: str, amount_eth: float) -> str:
    private_key = os.getenv('ETH_PRIVATE_KEY')
    from_address = web3.eth.account.privateKeyToAccount(private_key).address

    nonce = web3.eth.get_transaction_count(from_address)

    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': web3.to_wei(amount_eth, 'ether'),
        'gas': 21000,
        'gasPrice': web3.to_wei('20', 'gwei')
    }

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    return web3.to_hex(tx_hash)