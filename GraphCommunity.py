"""
    图社区发现算法
"""
import networkx as nx
from networkx.algorithms import community #  
import itertools
import community as community_louvain
import time
from tools import *
import pickle

def Matrix2Array(matrix,hmin):
    """
    Args:
        matrix: 相似度矩阵
        hmin: 相似度阈值
    Return:
        edge_list: 最后根据阈值hmin选取的无向边list, item: (i,j,matrix[i][j])
    """
    edge_list =  []
    time.sleep(0.5)
    with tqdm(total = len(matrix)) as pbar:
        for i in range(0,len(matrix)):
            for j in range(i+1,len(matrix)):
                if matrix[i][j] > hmin:
                    edge_list.append((i,j,matrix[i][j]))
            pbar.update(1)
    return edge_list

def do_infomap(G):
    # https://cloud.tencent.com/developer/article/1606056
    # https://github.com/mapequation/infomap/tree/master/examples/python
    import infomap # v1.0
    import datetime
    import time
    exist_node = set()
    infomapWrapper = infomap.Infomap("--two-level -f undirected") # infomap -h 命令行可以查看
    for u, v, w in G.edges(data=True):
        infomapWrapper.addLink(u,v,w['weight'])
        exist_node.add(u)
        exist_node.add(v)
    time.sleep(0.5)
#     print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    infomapWrapper.run() # 聚类运算
#     print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    # 有多少聚类数
#     print("Found {} modules with codelength: {}".format(infomapWrapper.numTopModules(), infomapWrapper.codelength))
    label2nodes = {}
    for node in infomapWrapper.nodes:
        if node.module_id not in label2nodes.keys():
            label2nodes[node.module_id] = []
        label2nodes[node.module_id].append(node.node_id)
    return list(label2nodes.values())
#     node2label = {}
#     count = 0
#     for node in infomapWrapper.nodes:
#         node2label[node.node_id] = node.module_id
#         count += 1
#     print(count,len(node2label),len(exist_node))
#     return node2label # 返回有社区的节点序号到标签的映射

#     # 
#     class2ipv6 = {}
#     for node in infomapWrapper.nodes:
#         if node.module_id not in class2ipv6.keys():
#             class2ipv6[node.module_id] = []
#         class2ipv6[node.module_id].append(reduced_pattern[node.node_id])

def do_gn(G,k=18):
    # k 指定想要的社区
#     G = nx.Graph()
#     G.add_weighted_edges_from(Matrix2Array(matrix))
    comp = community.girvan_newman(G) # GN算法
    limited = itertools.takewhile(lambda c: len(c) <= k, comp) # 层次感迭代器
    for communities in limited:
        b = list(sorted(c) for c in communities)
    return b

def do_lpa(G):
#     G = nx.Graph()
#     G.add_weighted_edges_from(Matrix2Array(matrix))
    # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.label_propagation.label_propagation_communities.html
    return list(community.label_propagation_communities(G)) # Yields sets of the nodes in each community.

def do_louvain(G):
    # 安装 pip install python-louvain
    # https://python-louvain.readthedocs.io/en/latest/api.html
    # G = nx.Graph()
    # G.add_weighted_edges_from(Matrix2Array(matrix))
    # https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.label_propagation.label_propagation_communities.html
    partition = community_louvain.best_partition(G)
    label2nodes = {}
    for k,v in partition.items():
        if v not in label2nodes.keys():
            label2nodes[v] = []
        label2nodes[v].append(k)
    return list(label2nodes.values())

def GraphCommunityDiscoveryAlgorithm(pattern, matrix, algorithm="louvain", sst=1e7, hmin=14.0):
    """
    Args:
        pattern: 模式字符串
        matrix: 基于pattern计算得到的相似度矩阵
        algorithm: 采用的图社区发现算法, {infomap,gn,lpa,louvain}
        sst: 过滤掉空间大小超过sst的模式字符串
        hmin: 相似度阈值
    Return:
        good_dis_p: 最后采用的模式库
    """
    func = {"louvain":do_louvain,"gn":do_gn,"lpa":do_lpa,"infomap":do_infomap}

    G = nx.Graph()
    G.add_weighted_edges_from(Matrix2Array(matrix,hmin))

    node2label = func[algorithm](G)  
    class2ipv6 = {}
    for module_id in range(len(node2label)):
        if module_id not in class2ipv6: class2ipv6[module_id] = []
        for node_id in node2label[module_id]:
            class2ipv6[module_id].append(pattern[node_id])
    
    # pd.Series([len(v) for k,v in class2ipv6.items()]).describe()
    discovered_pattern = []
    for key,value in class2ipv6.items():
        s = value[0]
        for i in range(1,len(value)):
            s = mergePattern(s,value[i])
        discovered_pattern.append((len(value),s))
    discovered_pattern = sorted(discovered_pattern,key=lambda x:x[0],reverse=True)
    good_dis_p = [i[1] for i in discovered_pattern if calSpace(i[1]) < sst] #空间阈值

    return good_dis_p


if __name__ == "__main__":
    with open("pk_data/reduced_pattern.pk","rb") as f:
        reduced_pattern = pickle.load(f)
    with open("pk_data/matrix.pk","rb") as f:
        matrix = pickle.load(f)
    
    good_dis_p = GraphCommunityDiscoveryAlgorithm(reduced_pattern,matrix,algorithm="gn",sst=1e9)
    print(good_dis_p)
    
