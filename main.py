import json
import time
from webbrowser import get
import web3
from abi import twap_abi, dei_pool_abi
from pprint import pprint

w3 = web3.Web3(web3.HTTPProvider("https://rpc.ankr.com/fantom"))
dei_pool = w3.eth.contract(w3.toChecksumAddress("0x9bd5cc542bc922e95ba41c0702555e830f2c1cb4"), abi=dei_pool_abi)
twap_contract = w3.eth.contract(w3.toChecksumAddress("0x1Bc270B2bE5c361784044ccE3f55c896fB5Fdf5A"), abi=twap_abi)

def get_tx_data():
    data = open("data.csv")
    content = data.readlines()[1:]

    redeemed = []
    can_collect = []

    collected_collateral = []
    
    for line in content:
        line_data = line.split(",")
        from_address = line_data[4].replace("\"", "")
        status = line_data[14].replace("\"", "")
        if status == "Reverted":
            continue
        method = line_data[-2]
        if method == "\"Redeem Fractional DEI\"":    # redeemed dei
            redeemed.append(from_address)
            _time = int(line_data[2].replace("\"", ""))
            _now = int(time.time())
            diff = _now - _time
            if (diff > 28800):  # can collect
                can_collect.append(line_data[4].replace("\"", ""))
        elif method == "\"Collect Collateral\"": # collected usdc
            collected_collateral.append(from_address)

    redeemed = list(set(redeemed))
    can_collect = list(set(can_collect))
    collected_collateral = list(set(collected_collateral))
    un_collected = list(set(redeemed) - set(collected_collateral))
    return redeemed, can_collect, collected_collateral, un_collected


def to_be_collected_deus(can_collect):
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

        return to_be_collected

def to_be_collected_collateral(un_collected):
    usdc_uncollected = []
    for not_collected in un_collected:
        amount = dei_pool.functions.redeemCollateralBalances(w3.toChecksumAddress(not_collected)).call()
        amount = int(amount)
        usdc_uncollected.append({
            'address': not_collected,
            'amount': amount
        })

    return usdc_uncollected

redeemed, can_collect, collected_collateral, un_collected = get_tx_data()

summery = {
    "totalRedeemedCount": len(redeemed),
    "totalCollectedCollateralCount": len(collected_collateral),
    "totalCanCollectDeusCount": len(can_collect),
    "redeemedAddresses": redeemed,
    "toBeCollectedDeus": to_be_collected_deus(can_collect),
    "toBeCollectedUSDC": to_be_collected_collateral(un_collected)
}

print(summery)
