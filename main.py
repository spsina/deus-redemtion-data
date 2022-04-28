import time
from webbrowser import get
import web3
from abi import twap_abi, dei_pool_abi
from pprint import pprint

w3 = web3.Web3(web3.HTTPProvider("https://rpc.ankr.com/fantom"))
dei_pool = w3.eth.contract(w3.toChecksumAddress("0x9bd5cc542bc922e95ba41c0702555e830f2c1cb4"), abi=dei_pool_abi)
twap_contract = w3.eth.contract(w3.toChecksumAddress("0x1Bc270B2bE5c361784044ccE3f55c896fB5Fdf5A"), abi=twap_abi)

def get_redeemed_and_can_collect():
    data = open("data.csv")
    content = data.readlines()[1:]

    redeemed = []
    can_collect = []
    
    for line in content:
        line_data = line.split(",")
        if line_data[-2] == "\"Redeem Fractional DEI\"":
            tx_hash = line_data[4].replace("\"", "")
            redeemed.append(tx_hash)
            _time = int(line_data[2].replace("\"", ""))
            _now = int(time.time())
            diff = _now - _time
            if (diff > 28800):
                can_collect.append(line_data[4].replace("\"", ""))

    redeemed = list(set(redeemed))
    can_collect = list(set(can_collect))
    return redeemed, can_collect

redeemed, can_collect = get_redeemed_and_can_collect()
to_be_collected = []
for collector in can_collect:
    positions = dei_pool.functions.getUnRedeemedPositions(w3.toChecksumAddress(collector)).call()
    total_usd = 0
    total_deus = 0
    for position in positions:
        amount, __time = position
        amount = int(amount)
        __time = int(__time)

        if __time == 0: continue

        deus_twap = twap_contract.functions.twap(w3.toChecksumAddress("0xde5ed76e7c05ec5e4572cfc88d1acea165109e44"), 10**18, __time, 28800).call()
        
        total_usd += amount
        total_deus += int((amount * 10 ** 18)/ int(deus_twap))

    to_be_collected.append({
        'address': collector,
        'amount_usd': total_usd,
        'amount_deus': total_deus
    })

pprint(to_be_collected)

        