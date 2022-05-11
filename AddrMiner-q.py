"""
    Detection addresses:
    input: pattern library
    output: active addresses
    process: Similarity matching strategy or Organizational association strategy
"""
from tools import *
from UGCPM import *
from GraphCommunity import *
import subprocess, os,json, time
import argparse
from generatePD import *
from tqdm import tqdm


def Start():
    target = 0
    result = 0
    parse=argparse.ArgumentParser()
    parse.add_argument('--output', type=str, default='result', help='output directory name')
    parse.add_argument('--budget',type=int, default=1e6, help='the upperbound of scan times of each prefix')
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
    print("AddrMiner begin")
    multi_level = dataloader("./data/seeds.csv", "./data/ipasn.dat")

    PD = getPD()
  
    multi_level['prefix_len'] = multi_level['bgp_prefix'].map(lambda x:x.split("/")[1])

    bgplen2prefix64 = getBgplen2prefix64(multi_level)

    # # step 1
    # os.system("python3 partition.py")

    # # step 2
    # os.system("python3 generatePD.py")
    
    # # step 3
    print("[+] begin to generate and detect targets")
    # Import bgp prefixes with sufficient seed address 
    with open('BGP/BGP-S.pk','rb') as f:
        bgp_s = pickle.load(f)
    
    limit = min(500,len(bgp_s))


    with tqdm(total=3*limit) as pbar:
        # sufficient seeds
        num=0
        ipv6_list = []
        for bgp in bgp_s:
            ipv6_list.extend(bgp_s[bgp])
            pbar.update(1)
            num+=1
            if num==limit:break

        with open('./seeds-S.txt','w') as f:
            for addr in ipv6_list:
                f.write(addr.strip()+'\n')
        # few seeds
        num=0
        with open('BGP/BGP-F.pk','rb') as f:
            bgp_f = pickle.load(f)
        # Similarity matching strategy
        new_ipv6_F = []
        for bgp in bgp_f:
            ipv6_list = bgp_f[bgp]
            new_ipv6_F += TopK(ipv6_list, PD, args.kheap, args.budget) 
            num+=1
            pbar.update(1)
            if num==limit:break
        # no seeds
        num = 0
        with open('BGP/BGP-N.pk','rb') as f:
            bgp_n = pickle.load(f)
        # Organizational association strategy
        new_ipv6_N = []
        for bgp in bgp_n:
            new_ipv6_N += OrgRel(bgp, PD, bgplen2prefix64, args.budget)
            num+=1
            pbar.update(1)
            if num==limit:break
        time.sleep(0.5)
        pbar.close()
        print("This will take several minutes")

        print('[+]Sufficient seed scenario: Running AddrMiner-S')
        os.system("sudo python3 DynamicScan.py --input=./seeds-S.txt --output={} --budget={} --IPv6={}".format(args.output, args.budget*limit,args.IPv6))

        with open("./result/target-S.txt", 'r') as f:
            target += len(f.readlines())
        
        with open("./result/result-S.txt", 'r') as f:
            result += len(f.readlines())

        hitrate = result / target
        print('target {}\nresult {}\nhit_rate {}\n'.format(target,result,hitrate))


        print('[+]Few seed scenario: Running AddrMiner-F')
        with open("result/target-F.txt","w") as f:
            for ipv6 in new_ipv6_F:
                f.write(ipv6+"\n") 
        
        activeAddr = Scan(new_ipv6_F,args.IPv6,args.output,0)
        target_f = len(new_ipv6_F)
        result_f = len(activeAddr)

        target += len(new_ipv6_F)
        result += len(activeAddr)

        hitrate = result_f / target_f
        print('target {}\nresult {}\nhit_rate {}\n'.format(target_f,result_f,hitrate))

        print('[+]No seed scenario: Running AddrMiner-N')
        activeAddr = Scan(new_ipv6_N,args.IPv6,args.output,0)
        target_n = len(new_ipv6_N)
        result_n = len(activeAddr)

        target += len(new_ipv6_N)
        result += len(activeAddr)
        hitrate = result_n / target_n
        print('target {}\nresult {}\nhit_rate {}\n'.format(target_n,result_n,hitrate))

    hitrate = result / target
    print("[+] end")
    print('generate target addresses: {}\ndiscover IPv6 active addresses: {}\nhit_rate {}\n'.format(
        target, result, hitrate))



if __name__ == "__main__":
    """
    sudo python3 AddrMiner.py --output=result --budget=100 --IPv6=XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX
    """
    Start()
