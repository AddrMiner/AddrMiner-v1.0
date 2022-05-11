from tools import *
from UGCPM import *
from GraphCommunity import *
import subprocess
import argparse

def genAddrWithBGP(bgp_prefix,iid_p, bgplen2prefix64,limit=None):
    prefix = bgp_prefix.split("::")[0]
    bgp_len = bgp_prefix.split("/")[1]
    p_len = len(prefix.replace(":",""))
    iid_p = iid_p.split("_") # 16 个
    random.seed(2021)
    if p_len >= 16:
        p = list(prefix.replace(":","")) + iid_p[(p_len-16):]
    else:
        p = list(prefix.replace(":",""))
        try:
            c_p = random.sample(bgplen2prefix64[str(bgp_len)],1)[0]
        except KeyError:
            c_p = '0'*16
        p  = p + list(c_p[p_len:]) + iid_p
    return genAddrByPattern("_".join(p),limit=limit)
    
def std_bgprefix(bgp_prefix):
    prefix_num = bgp_prefix.split("::")[0].count(":")+1
    s_ipv6 = standardize(bgp_prefix.split("/")[0])
    r = ":".join(s_ipv6.split(":")[0:prefix_num])
    r += "::" + bgp_prefix.split("::")[1]
    return r

# Organizational association strategy
def OrgRel(bgp_prefix,patterns,bgplen2prefix64,budget=None):
    bgp_prefix = std_bgprefix(bgp_prefix)
    random.seed(2021)
    new_ipv6 = []
    if budget is not None and budget < len(patterns):
        c_p = random.sample(patterns,budget)
        for iid_p in c_p:
            new_ipv6 += genAddrWithBGP(bgp_prefix,iid_p, bgplen2prefix64,limit=1)
    else:
        for iid_p in patterns:
            new_ipv6 += genAddrWithBGP(bgp_prefix,iid_p, bgplen2prefix64,limit=budget)
    return random.sample(new_ipv6,budget) if budget < len(new_ipv6) else new_ipv6

# Similarity matching strategy
def TopK(ipv6_list, PD, k=5, budget=None):  #kheap
    random.seed(2021)
    import heapq
    p = getPattern(ipv6_list)
    output = []
    for iid_p in PD:
        s = calSimilarity(p, "0_"*16 + iid_p,extra_len=16)
        output.append((s,iid_p))
    output = heapq.nlargest(k,output,key=lambda x:x[0])
    new_ipv6 = []
    for new_p in [p.rsplit("_",16)[0] + '_' +i[1] for i in output]:
        new_ipv6 += genAddrByPattern(new_p,limit=budget)
    return random.sample(new_ipv6,budget) if budget < len(new_ipv6) else new_ipv6


def get_good_p(multi_level, hmin=14.0, hmax=16.0, algorithm="louvain", sst=1e7, types=4, emin=0.4, emax=0.8):
    """
    Args:
        multi_level: [asn, bgp_prefix, std_ipv6, count], where count is the size of std_ipv6(the number of seeds contained)
        hmin: Similarity threshold, below which no undirected edges are constructed
        hmax: Similarity threshold, if exceeded then node merge is performed
        algorithm: The graph community discovery algorithm used:{infomap,gn,lpa,louvain}
        sst: Filter out pattern strings whose space size exceeds sst
        types: Threshold for the number of types of values per half-byte,[1,16]
        emin: Shannon Entropy lower bound (0,1)
        emax: Shannon Entropy upper bound (0,1)
    Return:
        good_dis_p: The better pattern is obtained according to the algorithm and after culling
    """
    # Pattern of leaf nodes
    all_pattern = peakProcess(multi_level,types,emin,emax)
    # Pattern after parallel set optimization
    reduced_pattern = optimization(all_pattern,hmax=hmax) #hmax
    # Calculate the similarity matrix and store it
    matrix = genMatrix(reduced_pattern)
    with open("pk_data/matrix.pk","wb") as f:
        pickle.dump(matrix,f)
    # Most popular pattern mining without seed addresses, to get the final pattern library used and input into the good_dis_p.pk pattern library
    good_dis_p = mppMiming(multi_level,algorithm=algorithm,sst=sst,hmin=hmin) #algorithm, sst, hmin
    return good_dis_p

# def generateTarget(multi_level, PD, bgplen2prefix64, kheap=10,budget=1e6):
#     """
#     Args:
#         multi_level: [asn, bgp_prefix, std_ipv6, count], where count is the size of std_ipv6 (the number of seeds)
#         PD: pattern library
#         kheap: If "TopK" is used, the most similar kheap address pattern is selected
#         budget: Generate address budget (on all prefixes)
#     Return:
#         targetAddrFile: Generate target address file; organize associations:./GeneratedAddresses/OrgRel.list, Similarity matching:./GeneratedAddresses/TopK.list
#     """
#     seed_prefix = list(multi_level['bgp_prefix'])
#     seed_ipv6 = list(multi_level['std_ipv6'])
#     unitprefix_budget = int(budget / len(seed_prefix)) # Number of addresses generated per prefix, for use in organisational association policies
#     unitseed_budget = int(budget / len(seed_ipv6)) # Number of addresses generated per seed set, for use in similarity matching strategies

#     # Organisational association strategy
#     new_ipv6 = []
#     with tqdm(total=len(seed_prefix)) as pbar:
#         for bgp_prefix in seed_prefix:
#             new_ipv6 += OrgRel(bgp_prefix, PD, bgplen2prefix64, unitprefix_budget)
#             pbar.update(1)
#     with open("GeneratedAddresses/OrgRel.list","w") as f:
#         for ipv6 in new_ipv6:
#             f.write(ipv6+"\n") 
    
#     # Similarity matching strategy
#     new_ipv6 = []
#     with tqdm(total=len(seed_prefix)) as pbar:
#         for ipv6_list in seed_ipv6:
#             new_ipv6 += TopK(ipv6_list, PD, kheap, unitseed_budget) 
#             pbar.update(1)
#     with open("GeneratedAddresses/TopK.list","w") as f:
#         for ipv6 in new_ipv6:
#             f.write(ipv6+"\n") 

def Scan(addr_set, source_ip, output_file, tid):
    """
    Detecting active addresses in the addr_set address set using a scanning tool

    Args：
        addr_set：Set of addresses to be scanned
        source_ip
        output_file
        tid:Thread id of the scan

    Return：
        active_addrs：set of active addresses
    """

    scan_input = output_file + '/zmap/scan_input_{}.txt'.format(tid)
    scan_output = output_file + '/zmap/scan_output_{}.txt'.format(tid)

    with open(scan_input, 'w', encoding = 'utf-8') as f:
        for addr in addr_set:
            f.write(addr + '\n')

    active_addrs = set()
    command = 'sudo zmap --ipv6-source-ip={} --ipv6-target-file={} -M icmp6_echoscan -p 80 -q -o {}'\
    .format(source_ip, scan_input, scan_output)
    print('[+]Scanning {} addresses...'.format(len(addr_set)))
    t_start = time.time()
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # ret = p.poll()
    while p.poll() == None:
        pass

    if p.poll() is 0:
        # with open(output_file, 'a', encoding='utf-8') as f:
        # time.sleep(1)
        for line in open(scan_output):
            if line != '':
                active_addrs.add(line[0:len(line) - 1])
                    # f.write(line)
            
    print('[+]Over! Scanning duration:{} s'.format(time.time() - t_start))
    print('[+]{} active addresses detected!'
        .format(len(active_addrs)))
    return active_addrs

# def Scan(scan_input, scan_output, source_ip):
#     """
#     Detecting active addresses in the addr_set address set using a scanning tool

#     Args：
#         scan_input: Target address file to be scanned
#         scan_output: Active address output file
#         source_ip: ipv6 addresses

#     Return：
#         active_addrs：set of active addresses
#     """

#     active_addrs = set()
#     command = 'sudo zmap --ipv6-source-ip={} --ipv6-target-file={} -M icmp6_echoscan -p 80 -q -o {}'\
#     .format(source_ip, scan_input, scan_output)
#     print('[+]Start scanning!')
#     t_start = time.time()
#     p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
#     # ret = p.poll()
#     while p.poll() == None:
#         pass
#     if p.poll() is 0:
#         # with open(output_file, 'a', encoding='utf-8') as f:
#         # time.sleep(1)
#         for line in open(scan_output):
#             if line != '':
#                 active_addrs.add(line[0:len(line) - 1])
#                     # f.write(line)
#     print('[+]Over! Scanning duration:{} s'.format(time.time() - t_start))
#     print('[+]{} active addresses detected!'
#         .format(len(active_addrs)))
#     return list(active_addrs)

def getBgplen2prefix64(multi_level):
    bgplen2prefix64 = {}

    for index,row in multi_level.iterrows():
        bgplen = row[4]
        ipv6_list = row[2]
        if int(bgplen) >= 64:
            continue
        for ipv6 in ipv6_list:
            try:
                bgplen2prefix64[bgplen].append("".join(ipv6.split(":")[:4]))
            except KeyError:
                bgplen2prefix64[bgplen] = ["".join(ipv6.split(":")[:4])]
    
    return bgplen2prefix64

def getPD(pdpath="./pk_data/good_dis_p.pk"):
    most_popular = '0_0_0_0_0_0_0_0_0_0_0_0_0_0_0_0'
    most_popular_p = []
    for i in range(0,16):
        tmp = most_popular.split("_")
        tmp[i] = '?'
        most_popular_p.append("_".join(tmp))
    with open(pdpath,'rb') as f:
        good_p = pickle.load(f)
    
    PD = good_p + most_popular_p
    return PD

if __name__ == "__main__":
    """
    sudo python3 generatePD.py 
    """
    parse=argparse.ArgumentParser()
    parse.add_argument('--hmin',type=float, default=14.0, help='similarity threshold')
    parse.add_argument('--hmax',type=float, default=16.0, help='similarity threshold')
    parse.add_argument('--algorithm',type=str, default='louvain', help='graph community discovery algorithm')
    parse.add_argument('--sst',type=int,default=1e7,help="mode space upper limit")
    parse.add_argument('--types',type=int,default=4,help='nibble value type threshold')
    parse.add_argument('--emin',type=float,default=0.4,help='Shannon entropy lower bound,(0,1)')
    parse.add_argument('--emax',type=float,default=0.8,help='Shannon entropy upper bound,(0,1)')
    parse.add_argument('--kheap',type=int,default=10,help='The number of similar addresses selected by topk strategy')
    args = parse.parse_args()

    print('[+]data loading..')
    multi_level = dataloader("./data/seeds.csv", "./data/ipasn.dat")
    print('[+]undirected graph creation, get pattern library..')
    get_good_p(multi_level,
            hmin=args.hmin,
            hmax=args.hmax,
            algorithm=args.algorithm,
            sst=args.sst,
            types=args.types,
            emin=args.emin,
            emax=args.emax)