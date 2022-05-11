"""
    Undirected graph creation + pattern mining:
    inputfile: seeds./data/seeds.csv 
    outputfile: apttern liabrary ./pk_data/dis_p.pk
    process:
        Step1: BSPR gets pattern strings under different networks
        Step2: Parallel set optimization
        Step3: Similarity calculation
        Step4: Apply the graph community discovery algorithm to get patterns
        Step5: Input to the pattern library
"""
from tools import *
import time 
import datetime 
from GraphCommunity import *
import infomap

def dataloader(seeds_path, ipasn_path):
    data = pd.read_csv(seeds_path,encoding= 'utf-8')
    data = handle(data,ipasn_dbpath=ipasn_path) #new
    tmp = data.groupby(['asn'])['std_ipv6'].apply(list)
    asn_level = tmp.reset_index()
    asn_level['count'] = asn_level['std_ipv6'].map(lambda x:len(x))
    tmp = data.groupby(['asn','bgp_prefix'])['std_ipv6'].apply(list)
    multi_level = tmp.reset_index()
    multi_level['count'] = multi_level['std_ipv6'].map(lambda x:len(x))

    return multi_level


def find(x, pre):
    r = x
    while pre[r]!=r:
        r = pre[r]
    return r

def join(x, y, pre):
    fx = find(x,pre)
    fy = find(y,pre)
    if fx!=fy:
        pre[fx] = fy

def FindBestSplit(ipv6_list, h_rate=0.1):
    V = []
    for ipv6 in ipv6_list:
        V.append((calIIDEntropy(ipv6,16), ipv6))
    V = sorted(V, key=lambda x:x[0])
    Vmax = max([i[0] for i in V])
    Vmin = min([i[0] for i in V])
    newleafs = []
    tmpleafs = []
    for i in range(1,len(V)):
        if (V[i][0]-V[i-1][0]) > h_rate * (Vmax-Vmin):
            newleafs. append(tmpleafs)
            tmpleafs = []
        tmpleafs.append(V[i][1])
    newleafs.append(tmpleafs)
#     print(len(newleafs))
    return newleafs


def peakProcess(multi_level,types=4,emin=0.4,emax=0.8):
    """
    Vertex processing stage
    Args:
        multi_level: [asn, bgp_prefix, std_ipv6, count]
        types: Threshold for the number of types of values per half-byte,[1,16]
        emin: Shannon Entropy lower bound (0,1)
        emax: Shannon Entropy upper bound (0,1)
    Return:
        all_pattern: Patterns mined
    """
    all_leafs = []
    with tqdm(total=len(multi_level)) as pbar:
        for leafs in multi_level['std_ipv6']:
            for h_rate in [0.1, 0.08, 0.05]:
                tmp = FindBestSplit(leafs, h_rate)
                if len(tmp) == 1: continue
                else: break
            all_leafs += tmp
            pbar.update(1)
    hdbscan_leafs = []
    K = 4 # /K*16
    with tqdm(total=len(all_leafs)) as pbar:
        for leaf in all_leafs:
            tmp = {'std_ipv6':leaf}
            tmp = pd.DataFrame(tmp)
            tmp['prefixK'] = tmp['std_ipv6'].map(lambda x:"".join(x.split(":")[1:K]))
            tmp = tmp.groupby('prefixK')['std_ipv6'].apply(list).reset_index()
            for ipv6_list in tmp['std_ipv6']:
                hdbscan_leafs.append(ipv6_list)
            pbar.update(1)
    final_leafs = [c for c in hdbscan_leafs if len(c) > 1]
    print("[+]get all leaf nodes' pattern")
    time.sleep(0.5)
    all_pattern = []
    pattern2ipv6 = {}
    with tqdm(total=len(final_leafs)) as pbar:
        for ipv6_list in final_leafs:
            p = getPattern(ipv6_list,types=types,emin=emin,emax=emax)
            all_pattern.append(p)
            pattern2ipv6[p] = ipv6_list
            pbar.update(1)

    return all_pattern

def optimization(all_pattern, hmax=16.0):
    """
    Args:
        all_pattern: All pattern strings obtained by BSPR
        hmax:Similarity threshold, if this value is exceeded during merge set optimization, the two nodes are merged
    Return:
        reduced_pattern: Optimised resulting pattern string
    """
    most_popular = '0_0_0_0_0_0_0_0_0_0_0_0_0_0_0_0'
    most_popular_p = []
    for i in range(0,16):
        tmp = most_popular.split("_")
        tmp[i] = '?'
        most_popular_p.append("_".join(tmp))

    other_p = []
    with tqdm(total = len(all_pattern)) as pbar:
        for p in all_pattern:
            iid_p = "_".join(p.split("_")[16:])
            flag = False
            for mpp in most_popular_p:
                if calSimilarity(iid_p, mpp) >= hmax:   # Similarity Threshold hmax
                    flag = True
                    break
            if not flag: other_p.append(iid_p)
            pbar.update(1)
    
    choosed_p = other_p
    p_len = len(choosed_p)
    pre = list(range(0,p_len))
    visited = [0] * p_len
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    time.sleep(0.8)
    with tqdm(total = (p_len*(p_len-1))/2) as pbar:
        for i in range(0,p_len):
            if visited[i] == 1:
                pbar.update(p_len - (i+1))
            else:    
                visited[i] = 1
                for j in range(i+1,p_len):
                    if visited[j] == 1:
                        pass
                    else:
                        score = calSimilarity(choosed_p[i], choosed_p[j])
                        if score >= hmax:  # Similarity Threshold
                            join(i,j,pre)
                            visited[j] = 1
                    pbar.update(1)
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print('Merge')
    time.sleep(0.8)
    d = {}
    with tqdm(total = p_len) as pbar:
        for i in range(0, p_len):
            r = find(i,pre)
            if r in d.keys():
                d[r] = mergePattern(d[r], choosed_p[i])
            else:
                d[r] = choosed_p[i]
            pbar.update(1)
    reduced_pattern = list(d.values())
    import pickle
    with open("pk_data/reduced_pattern.pk","wb") as f:
        pickle.dump(reduced_pattern, f)
    
    return reduced_pattern



def mppMiming(multi_level,algorithm="louvain",sst=1e7,hmin=14.0):
    """
    The most popular pattern mining without seed addresses
    Args:
        algorithm: The graph discovery algorithm used:{infomap,gn,lpa,louvain}
        sst: Filter out pattern strings whose space size exceeds sst
        hmin: Similarity Threshold
    Return:
        good_dis_p: Final adopted pattern library
    """
    t = multi_level[['asn','bgp_prefix']].groupby('asn')['bgp_prefix'].apply(list).reset_index()
    t['prefix_count'] = t['bgp_prefix'].map(len)
    t['prefix_count'].describe()
    lsp = []
    for prefixes in t['bgp_prefix']:
        if len(prefixes) > 2:
            lsp += random.sample(prefixes,1)
    with open("pk_data/lsp.pk","wb") as f:
        pickle.dump(lsp,f)
    most_popular = '0_0_0_0_0_0_0_0_0_0_0_0_0_0_0_0'
    low_p = []
    for i in range(most_popular.count('0')):
        t = most_popular.split("_")
        t[i] = '?'
        low_p.append("_".join(t))

    with open("pk_data/matrix.pk","rb") as f:
        matrix = pickle.load(f)
    
    with open("pk_data/reduced_pattern.pk","rb") as f:
        reduced_pattern = pickle.load(f)
    
    good_dis_p = GraphCommunityDiscoveryAlgorithm(pattern=reduced_pattern,matrix=matrix,algorithm=algorithm,sst=sst,hmin=hmin)

    with open("pk_data/good_dis_p.pk","wb") as f:
        pickle.dump(good_dis_p,f)
    
    return good_dis_p
    
if __name__ == "__main__":
    # Hyperparameter setting
    hmax = 16.0
    hmin = 14.0
    algorithm = "louvain"
    sst = 1e7
    # load data
    seeds_path = "data/seeds.csv"
    ipasn_path = "data/ipasn.dat"
    multi_level = dataloader(seeds_path, ipasn_path)
    # pattern of lead node
    all_pattern = peakProcess(multi_level)
    # Pattern after parallel set optimization
    reduced_pattern = optimization(all_pattern,hmax=16.0) #hmax
    # Calculate the similarity matrix and store it
    matrix = genMatrix(reduced_pattern)
    with open("pk_data/matrix.pk","wb") as f:
        pickle.dump(matrix,f)
    # Most popular pattern mining without seed addresses, to get the final pattern library used and input into the good_dis_p.pk pattern library
    good_dis_p = mppMiming(multi_level,algorithm="louvain",sst=1e7,hmin=14.0) #algorithm, sst, hmin
    


