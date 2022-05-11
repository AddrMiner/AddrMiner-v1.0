"""
    无向图创建+模式挖掘:
    inputfile: 种子地址./data/seeds.csv 
    outputfile: 模式库 ./pk_data/dis_p.pk
    process:
        Step1: BSPR得到不同网络下的模式字符串
        Step2: 并查集优化
        Step3: 相似度计算
        Step4: 应用图社区发现算法得到模式
        Step5: 输入到模式库中
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
    顶点处理阶段
    Args:
        multi_level: [asn, bgp_prefix, std_ipv6, count], 其中count为std_ipv6的size, 即包含的种子数量
        types: 每个半字节取值种类个数阈值,[1,16]
        emin: Shannon熵下界 (0,1)
        emax: Shannon熵上界 (0,1)
    Return:
        all_pattern: 挖掘到的模式
    """
    all_leafs = []
    with tqdm(total=len(multi_level)) as pbar:
        for leafs in multi_level['std_ipv6']:
            # 怎么自动找跃变区域
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
        all_pattern: BSPR得到的所有模式字符串
        hmax:相似度阈值,并查集优化时若超过此值,则将两个节点进行合并
    Return:
        reduced_pattern: 优化后得到的模式字符串
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
                if calSimilarity(iid_p, mpp) >= hmax:   #相似度阈值hmax
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
                        if score >= hmax:  #相似度阈值
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
    无种子地址的most popular pattern挖掘
    Args:
        algorithm: 采用的图发现算法:{infomap,gn,lpa,louvain}
        sst: 过滤掉空间大小超过sst的模式字符串
        hmin: 相似度阈值
    Return:
        good_dis_p: 最后采用的模式库
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
    #超参数设置
    hmax = 16.0
    hmin = 14.0
    algorithm = "louvain"
    sst = 1e7
    #数据载入
    seeds_path = "data/seeds.csv"
    ipasn_path = "data/ipasn.dat"
    multi_level = dataloader(seeds_path, ipasn_path)
    #叶子节点的pattern
    all_pattern = peakProcess(multi_level)
    #并查集优化后的pattern
    reduced_pattern = optimization(all_pattern,hmax=16.0) #hmax
    #计算相似度矩阵，并进行存储
    matrix = genMatrix(reduced_pattern)
    with open("pk_data/matrix.pk","wb") as f:
        pickle.dump(matrix,f)
    #无种子地址的most popular pattern挖掘, 得到最后采用的模式库，并输入到good_dis_p.pk模式库中
    good_dis_p = mppMiming(multi_level,algorithm="louvain",sst=1e7,hmin=14.0) #algorithm, sst, hmin
    


