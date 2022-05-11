#!/usr/bin/python3.6
# encoding:utf-8
from Definitions import Intersection
from AddrsToSeq import InputAddrs, SeqToAddrs
from DHC import SpaceTreeGen, OutputSpaceTree
from ScanPre import ScanPre
from ActiveScan import Scan
from copy import deepcopy
import argparse
import time
import psutil
import os
import datetime

"""
sudo python3 DynamicScan.py --input=./data.csv --output=/result.txt --budget=500  --IPv6=XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX --delta=16 --beta=16
"""

def DynamicScan(root, budget, source_ip, output_dir):
    """
    动态扫描空间树

    Args：
        root：root node of tree 
        V：Seed address vector sequence
        budget：Upper limit of scanning overhead (maximum number of addresses to be scanned)
        source_ip：Host source IPv6 address
        output_dir：Output file directory

    Return：
        R：Active address sets found by scanning (each member is a real IPv6 address string)
        P：Collection of detected alias prefixes
        budget：Number of remaining scans
    """
    # OutputSpaceTree(root,V)
    # R = set()
    R = set()
    T = set()
    init_budget = deepcopy(budget)
    active_file = output_dir + '/result-S.txt'
    target_file = output_dir + '/target-S.txt'
    xi = [] # Queue of nodes to be scannedξ
    InitializeNodeQueue(root, xi)
    xi, budget, R, T = Scan_Feedback(xi, init_budget, budget, R, T, source_ip, output_dir, target_file)
    
    while budget > 0:
        xi_h = TakeOutFrontSegment(xi, int(0.1 * len(xi))+1)  # Nodes to be scanned per iteration
        ReplaceDescendants(xi, xi_h)
        xi_h, budget, R, T = Scan_Feedback(xi_h, init_budget, budget, R, T, source_ip, output_dir, target_file)
        xi = MergeSort(xi_h, xi) 
    
    # print("begin to store the ip address in {} and {}".format(active_file,target_file))
    with open(active_file, 'w', encoding='utf-8') as f:
        for addr in R:
            f.write(addr + '\n')
    with open(target_file, 'w', encoding='utf-8') as f:
        for target in T:
            f.write(target + '\n')
    hit_rate = float(len(R))/(init_budget - budget)
    return R, init_budget - budget, len(R), hit_rate


def InitializeNodeQueue(root, xi):
    """
    Hierarchical traversal of the spatial tree, initializing the node queue ξ as a leaf node of the spatial tree

    Args：
        root:
        xi：queueξ
    """
    # pdb.set_trace()
    q = []
    q.append(root)
    while q != []:
        node = q.pop(0)
        if node.childs != []:
            q += node.childs
        else:
            xi.append(node)


def Scan_Feedback(xi, init_budget, budget, R, T, source_ip, output_dir, target_file):
    """
    Perform a scan of all nodes in queue xi and reorder the queue based on the density of active addresses obtained from the scan

    Args：
        xi：node queueξ
        init_budget:Scanning upper limit
        budget：Number of scans remaining
        R：Collection of active addresses found by scanning
        T
        V:Set of seed address vectors
        source_ip
        output_dir
        target_file

    Return:
        xi: The reordered node queue ξ
        budget: Number of scans remaining after one iteration of scanning
        R：Updated collection of active addresses
        T：Collection of predicted addresses
    """

    # pdb.set_trace()

    TS_addr_union = list()
    SS_addr_union = list()
    for i in range(len(xi)):
        # if i % 100 == 0:
        #     print(i)
        node = xi[i]
        TS_addr_union += SeqToAddrs(node.TS)
        # print(node.TS)
        SS_addr_union += list(node.SS)

    C = set(TS_addr_union).difference(set(SS_addr_union)) # The set of addresses to be scanned this time
    budget -= len(C)
    if budget <= 0:
        C = LimitBudget(budget, C)
        budget = 0

    T.update(C)
    # with open(target_file, 'a', encoding='utf-8') as f:
    #     for target in C:
    #         f.write(target + '\n')
    active_addrs = set(Scan(C, source_ip, output_dir, 0))   # Scan and get the active address set

    R.update(active_addrs)
    # print('[+]Hit rate:{}   Remaining scan times:{}\n'
    #    .format(float(len(R)/(init_budget - budget)), budget))

    for i in range(len(xi)):
        # if(i % 100 == 0):
        #     print(i)
        node = xi[i]
        node.SS = set(SeqToAddrs(node.TS))
        new_active_addrs = active_addrs.intersection(node.SS)
        node.NDA += len(new_active_addrs)
        node.AAD = float(node.NDA)/len(node.SS)
        delta = node.DS.pop()
        node.ExpandTS(delta)

    xi = sorted(xi, key=lambda node: node.AAD, reverse=True)
    
    return xi, budget, R, T


def TakeOutFrontSegment(xi, m):
    """
    Extract the first m nodes in the node queue xi as the target node queue for the next scan

    Args：
        xi: Queue to be split
        m：Number of nodes in the new target queue

    Return：
        xi_h：New target queue
    """

    # xi_h = deepcopy(xi[:m])
    # pdb.set_trace()

    if m <= len(xi):
        xi_h = xi[:m]
        del xi[:m]
    else:
        xi_h = xi[:]
        del xi[:]

    return xi_h


def ReplaceDescendants(xi, xi_h):
    """
    After a new scan, if a node has the same DS as its parent node in the xi and xi_h 
    queue, the node and all its sibling nodes need to be deleted and their parent nodes
    inserted

    Args：
        xi：Queue of nodes that are not scanned, but will not be scanned in the next scan
        xi_h：Queue of nodes that will be scanned next
    """

    # pdb.set_trace()

    new_nodes = set()   # The set of nodes that will be added to the queue
    for node in xi_h:
        if node.parent == None:
            break   
        if node.parent.DS.stack == node.DS.stack:
            node.parent.TS = node.TS
            new_nodes.add(node.parent)

    complete_queue = set(xi_h + xi)
    # xi_h_set = set(xi_h)
    # xi_set = set(xi)    # Convert the priority queue into a set of nodes first to facilitate subsequent merge and intersection operations
    count = 0
    # prevent new_nodes from being modified during traversal，RuntimeError: Set changed size during iteration
    xiugai_nodes = new_nodes.copy()
    for node in xiugai_nodes:
        # childs = set(node.cohilds)
        count += 1
        #if count % 100 == 0:
        #    print("new node {}".format(count))
        childs = set(node.childs)
        retired = complete_queue.intersection(childs)
        # retired = Intersection(childs, complete_queue)
        for retired_node in retired:
            node.SS = node.SS.union(retired_node.SS) 
            # node.SS  = list(node.SS) + list(retired_node.SS)
            node.NDA += retired_node.NDA
        # node.SS = set(node.SS)
        node.AAD = float(node.NDA)/len(node.SS)

        # Nodes that need to be removed from the two queues and the new_nodes collection respectively
        xi_h_remove = Intersection(retired, xi_h)
        xi_remove = Intersection(retired, xi)
        new_nodes_remove = Intersection(retired, new_nodes)
        for v in xi_h_remove:
            xi_h.remove(v)
        for v in xi_remove:
            xi.remove(v)
        for v in new_nodes_remove:
            new_nodes.remove(v)

    for new_node in new_nodes:
        xi_h.append(new_node)


def MergeSort(xi_h, xi):
    """
    Merge two ordered queues of nodes into one

    Args：
        xi_h：queue 1
        xi：queue 2

    Return：
        queue：Merged ordered queues
    """

    queue = []
    i1 = 0
    i2 = 0
    while i1 < len(xi_h) or i2 < len(xi):
        if i1 >= len(xi_h):
            queue += xi[i2:]
            break
        elif i2 >= len(xi):
            queue += xi_h[i1:]
            break
        elif xi_h[i1].AAD >= xi[i2].AAD:
            queue.append(xi_h[i1])
            i1 += 1
        else:
            queue.append(xi[i2])
            i2 += 1

    return queue


def LimitBudget(budget, C):
    """
    Delete addresses in C that are over budget

    Args:
        budget: The opposite of the number of addresses over budget
        C：The next set of target addresses to be scanned

    Return:
        C：The set of processed destination addresses
    """

    C = list(C)
    del C[:-budget]
    return set(C)

def Start():
    parse=argparse.ArgumentParser()
    parse.add_argument('--input', type=str, help='input IPv6 addresses')
    parse.add_argument('--output',type=str,help='output directory name')
    parse.add_argument('--budget',type=int,help='the upperbound of scan times')
    parse.add_argument('--IPv6',type=str,help='local IPv6 address')
    parse.add_argument('--delta', type=int, default =16, help='the base of address')
    parse.add_argument('--beta',type=int,default=16,help='the max of node ')
    args=parse.parse_args()
    # args.input = '/home/sgl/6density_no_APD/files/source_copy.hex'
    # args.output = '/home/sgl/6density_no_APD/files2'
    # args.budget = 50000
    # args.IPv6 = '2001:da8:ff:212::20:5'

    # IPS=InputAddrs(input="data1.csv")
    # root=SpaceTreeGen(IPS,16,16)
    # OutputSpaceTree(root)
    # print("ipv6 addres to sec begining")
    # print(args.input)
    V = InputAddrs(input=args.input, beta=args.delta)
    # print("ipv6 addres to sec over")
    # print("SpaceTreeGen beginning")
    root = SpaceTreeGen(V, delta=args.delta, beta=args.beta)
    # print("SpaceTreeGen over")
    ScanPre(root)
    # OutputSpaceTree(root,V)
    # print('Space tree generated with {} seeds!'.format(len(V)))    
    R, target_len, result_len, hit_rate = DynamicScan(root, args.budget, args.IPv6, args.output)
    # print('Over!')
    # hit_rate = float(len(R))/(init_budget - budget)
    # return init_budget - budget, len(R), hit_rate
    return target_len, result_len, hit_rate


if __name__ == '__main__':
    target, result, hit_rate = Start()
    # print("target {}".format(target))
    # print("result {}".format(result))
    # print("hit_rate {}".format(hit_rate))


    
