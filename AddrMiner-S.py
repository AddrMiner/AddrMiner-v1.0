"""
    Probing in BGP-F
"""
from tools import *
from UGCPM import *
from GraphCommunity import *
from generatePD import *
import argparse
import os

#DET
def generateTarget(bgp, ipv6, result, budget=1e6):
    """
    Args:
        PD: pattern library
        budget: limit the number of target addresses
    """
    with open('BGP/BGP-S.pk','rb') as f:
        bgp_s = pickle.load(f)
    
    ipv6_list = bgp_s[bgp]
    with open('./seeds-S.txt','w') as f:
        for addr in ipv6_list:
            f.write(addr.strip()+'\n')
    
    os.system("sudo python3 DynamicScan.py --input=./seeds-S.txt --output={} --budget={} --IPv6={}".format(result, budget,ipv6))

def Start():
    """
    sudo python3 AddrMiner-S.py --prefix=2406:da00:ff00::/48 --output=result --budget=10000 --IPv6=XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX
    """
    parse=argparse.ArgumentParser()
    parse.add_argument('--prefix',type=str,help='BGP prefix')
    parse.add_argument('--output', type=str, default='result', help='output directory name')
    parse.add_argument('--budget',type=int, default=1e6, help='the upperbound of scan times')
    parse.add_argument('--IPv6',type=str, help='local IPv6 address')
    args = parse.parse_args()
    
    print('[+]generate target address..')
    generateTarget(args.prefix, args.IPv6, args.output, budget=args.budget)
 
    

if __name__ == "__main__":
    Start()

