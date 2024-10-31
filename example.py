from web3 import web3
import time

# verbindungsaufbau zur binance smart chain
w3 = web3(web3.httpprovider("https://bsc-dataseed.binance.org/"))  # nutze deine bsc-node-url

# adressen und private keys
central_wallet_address = "0xyourcentralwalletaddress"
central_wallet_private_key = "yourcentralwalletprivatekey"
usdt_contract_address = "0x55d398326f99059ff775485246999027b3197955"  # usdt auf bsc

# smart contract für usdt einrichten (erc20 interface)
usdt_contract = w3.eth.contract(address=usdt_contract_address, abi=[
    {
        "constant": true,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceof",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "success", "type": "bool"}],
        "type": "function"
    }
])

# mindestwert für bnb-bestand
bnb_threshold = 0.1  # 0,1 bnb für gas-kosten

# funktion zur überprüfung des bnb-guthabens
def check_bnb_balance(address):
    balance = w3.eth.get_balance(address) / (10 ** 18)
    return balance

# funktion zum ausführen der user-transaktion
def process_user_transaction(user_wallet_address, amount_usdt):
    # bnb-gebühr berechnen
    gas_price = w3.eth.gas_price
    gas_limit = 21000  # standard-gaslimit für einfache transaktionen
    gas_fee_bnb = gas_limit * gas_price / (10 ** 18)  # in bnb

    # prüfen, ob die zentrale wallet genug bnb für die gasgebühr hat
    central_balance = check_bnb_balance(central_wallet_address)
    if central_balance < gas_fee_bnb:
        print("unzureichendes bnb-guthaben in der zentralen wallet.")
        return

    # user-transaktion vorbereiten
    tx = {
        'to': user_wallet_address,
        'value': w3.toWei(amount_usdt, 'ether'),
        'gas': gas_limit,
        'gasprice': gas_price,
        'nonce': w3.eth.gettransactioncount(central_wallet_address),
    }

    # transaktion signieren und senden
    signed_tx = w3.eth.account.sign_transaction(tx, central_wallet_private_key)
    tx_hash = w3.eth.sendrawtransaction(signed_tx.rawtransaction)
    print(f"user transaction hash: {tx_hash.hex()}")

    # umwandlung und abzug des usdt-betrags (um die gasgebühren zu decken)
    gas_fee_usdt = convert_bnb_to_usdt(gas_fee_bnb)
    deduct_usdt_from_user(user_wallet_address, gas_fee_usdt)

# funktion zum umrechnen von bnb in usdt
def convert_bnb_to_usdt(bnb_amount):
    # beispiel-umrechnung; in der realität würde ein api-aufruf zur kursabfrage genutzt werden
    bnb_to_usdt_rate = 220  # beispielkurs: 1 bnb = 220 usdt
    return bnb_amount * bnb_to_usdt_rate

# funktion zum abziehen von usdt vom user-wallet
def deduct_usdt_from_user(user_wallet_address, usdt_amount):
    # umrechnung des usdt-betrags in wei
    usdt_amount_wei = int(usdt_amount * (10 ** 18))
    
    # usdt-transaktion zur zentralen wallet vorbereiten
    tx = usdt_contract.functions.transfer(
        central_wallet_address,
        usdt_amount_wei
    ).buildtransaction({
        'from': user_wallet_address,
        'gas': 60000,  # geschätztes gas für token-transfer
        'gasprice': w3.eth.gas_price,
        'nonce': w3.eth.gettransactioncount(user_wallet_address)
    })

    # transaktion signieren und senden
    signed_tx = w3.eth.account.sign_transaction(tx, central_wallet_private_key)
    tx_hash = w3.eth.sendrawtransaction(signed_tx.rawtransaction)
    print(f"usdt fee deduction transaction hash: {tx_hash.hex()}")

# hauptüberwachungsfunktion
def main():
    while true:
        # beispiel-user wallet und transaktionsbetrag
        user_wallet_address = "0xuserwalletaddress"
        amount_usdt = 1  # beispiel: 1 usdt senden

        # überprüfen und verarbeiten
        process_user_transaction(user_wallet_address, amount_usdt)
        
        # wartezeit zwischen den transaktionen (in sekunden)
        time.sleep(300)

# skript starten
if __name__ == "__main__":
    main()
