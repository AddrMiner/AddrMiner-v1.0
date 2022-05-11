from Definitions import Stack,TreeNode
from AddrsToSeq import AddrVecList,InputAddrs
import math
from copy import deepcopy

'''
Using DHC algorithm to form a spatial tree
'''

lamada=128

def SpaceTreeGen(IPS, delta=16,beta=16):
    '''
    Spatial tree generation

    Args:
        delta: Base
        beta: Upper limit of the number of addresses in a leaf node

    Return：
        root：root node of tree
    '''
    root=TreeNode(IPS)
    DHC(root,beta,delta)

    return root
    
def DHC(node,beta,delta):
    '''
    Hierarchical clustering algorithm

    Args；
        node：The current node to be clustered
        beta：Upper limit on the number of vectors in a leaf node
        delta: base
    '''
    vecnum=len(node.iplist)
    if vecnum<=beta:
        return
    # Record the dimension in which the value with the smallest entropy value that is not zero among all vectors of the current node is located
    best_position=node.get_splitP(delta)
    if best_position==-1:
        return

    node.diff_delta=best_position
    dic_key_ips=SplitVecSeq(node,best_position)
    for key in dic_key_ips:
        new_node=TreeNode(dic_key_ips[key],_partent=node)
        node.childs.append(new_node)
    for child in node.childs:
        DHC(child,beta,delta)

        

def SplitVecSeq(node,best_position):
    '''
    Split node.iplist into different lists
    return dictionary form {"1","{ip1,ip2}}"}
    '''
    dic_key_ips={}
    for ip in node.iplist:
        if ip[best_position-1] in dic_key_ips:
            dic_key_ips[ip[best_position-1]].append(ip)
        else:
            dic_key_ips[ip[best_position-1]]=[ip]
    return dic_key_ips


def OutputSpaceTree(root):
    """
    Hierarchical traversal of the output space tree

    Args：
        root：root node of tree
    """

    print('******LEVEL 1******')
    childs = root.childs
    root.OutputNode()
    # OutputNode(root, V)
    level = 2
    while childs != []:
        print('******LEVEL %d******' % level)
        while childs != [] and childs[0].level == level:
            child = childs.pop(0)
            childs.extend(child.childs)
            child.OutputNode()
            # OutputNode(child, V)
        level += 1

if __name__ == "__main__":
    IPS=InputAddrs(input="data1.csv")
    root=SpaceTreeGen(IPS,16,16)
    OutputSpaceTree(root)
