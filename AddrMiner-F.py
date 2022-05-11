"""
    Probing in BGP-F
"""
from tools import *
from UGCPM import *
from GraphCommunity import *
from generatePD import *
import argparse

def generateTarget(PD, bgp, kheap, budget=1e6):
    """
    Args:
        PD: 地址模式库
        budget: 生成地址预算
    """
    with open('BGP/BGP-F.pk','rb') as f:
        bgp_f = pickle.load(f)
    
    ipv6_list = bgp_f[bgp]
    #相似度匹配策略
    new_ipv6 = []
    new_ipv6 += TopK(ipv6_list, PD, kheap, budget) 
    with open("result/target-F.txt","w") as f:
        for ipv6 in new_ipv6:
            f.write(ipv6+"\n") 

def Start():
    """
    sudo python3 AddrMiner-F.py --prefix=2a01:7c8:d000::/36 --output=result --budget=10000 --IPv6=2001:da8:ff:212::10:3
    """
    parse=argparse.ArgumentParser()
    parse.add_argument('--prefix',type=str,help='BGP prefix')
    parse.add_argument('--output', type=str, default='result', help='output directory name')
    parse.add_argument('--budget',type=int, default=1e6, help='the upperbound of scan times')
    parse.add_argument('--IPv6',type=str, help='local IPv6 address')
    parse.add_argument('--hmin',type=float, default=14.0, help='similarity threshold')
    parse.add_argument('--hmax',type=float, default=16.0, help='similarity threshold')
    parse.add_argument('--algorithm',type=str, default='louvain', help='graph community discovery algorithm')
    parse.add_argument('--sst',type=int,default=1e7,help="mode space upper limit")
    parse.add_argument('--types',type=int,default=4,help='nibble value type threshold')
    parse.add_argument('--emin',type=float,default=0.4,help='Shannon entropy lower bound,(0,1)')
    parse.add_argument('--emax',type=float,default=0.8,help='Shannon entropy upper bound,(0,1)')
    parse.add_argument('--kheap',type=int,default=10,help='The number of similar addresses selected by topk strategy')
    args = parse.parse_args()

    multi_level = dataloader("./data/seeds.csv", "./data/ipasn.dat")

    PD = getPD()
  
    multi_level['prefix_len'] = multi_level['bgp_prefix'].map(lambda x:x.split("/")[1])
    
    print('[+]generate target address..')
    generateTarget(PD, args.prefix, args.kheap, budget=args.budget)

    activeAddr = Scan("./result/target-F.txt",args.output+"/result-F.txt", args.IPv6)
    with open(args.output+"/result-F.txt",'wb') as f:
        for addr in activeAddr:
            f.write(addr.encode())
            f.write('\n'.encode())
    print('[+]Over!')

    with open("./result/target-F.txt", 'r') as f:
        target_Fnum = len(f.readlines())
    
    result_Fnum = len(activeAddr)
    hitrate_F = result_Fnum / target_Fnum
    print('target {}\nresult {}\nhit_rate {}\n'.format(target_Fnum,result_Fnum,hitrate_F))

if __name__ == "__main__":
    Start()

