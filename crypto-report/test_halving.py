#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/crypto-report/src')
from crypto_reporter import get_btc_onchain

data = get_btc_onchain()
print("BTC onchain data:")
for k, v in data.items():
    print(f"  {k}: {v}")
