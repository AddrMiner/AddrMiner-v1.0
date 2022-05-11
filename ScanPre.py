#!/usr/bin/python3.6
# encoding:utf-8
from AddrsToSeq import InputAddrs
from Definitions import Stack
from DHC import SpaceTreeGen, OutputSpaceTree
from copy import deepcopy
import math
import pdb

def ScanPre(root):
    """
    Preparation for the start of the dynamic scan

    Args:
        root: Root node of a spatial tree
    """

    InitializeDS(root)
    InitializeTS(root)


def InitializeDS(node, parent_stack = Stack(), beta=16):
    """
    Initialize the DS of node node

    Args：
        node：Current DS nodes to be initialised
        parent_stack：DS of the parent node           
        beta：The base of each dimension of the vector
    """    
    
    # pdb.set_trace()
    parent=node.parent
    stack = deepcopy(parent_stack) # Note that you have to make a copy of the DS of the parent node
    if parent !=None:
        stack.push(parent.diff_delta)

    vecDim = int(128 / math.log(beta, 2))

    for delta in range(1, vecDim + 1):        
        if node.Steady(delta) and stack.find(delta) == False:
            stack.push(delta)

    if not node.isLeaf():
        for child in node.childs:
            InitializeDS(child, stack, beta)
    else:
        for delta in range(1, vecDim + 1):
            if stack.find(delta) == False:
                stack.push(delta)
    
    node.DS = stack
    # pdb.set_trace()


def InitializeTS(node):
    """
    TS initialisation of all leaf nodes (SS and NDA are initialised at node creation)

    Args：
        node：Current TS nodes to be initialised
    """

    # pdb.set_trace()

    if node.isLeaf():
        delta = node.DS.pop()
        # print(node.node_id)
        # print(delta)
        # node.last_pop = delta
        # node.last_pop_value = node.TS[delta - 1]
        # print("leaf node :{}".format(node.global_node_id))
        node.ExpandTS(delta)
    else:
        for child in node.childs:
            InitializeTS(child)    
    # pdb.set_trace()
    


if __name__ == '__main__':
    IPS=InputAddrs(input="data1.csv")
    root=SpaceTreeGen(IPS,16,16)
    ScanPre(root)
    OutputSpaceTree(root)