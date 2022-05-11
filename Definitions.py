#!/usr/bin/python3.6
# encoding:utf-8
from copy import deepcopy
import math


class Stack(object):
    """
    Stack class (data type of DS)
    """
    
    def __init__(self):
        self.stack = []

    def push(self, v):
        self.stack.append(v)

    def pop(self):
        if self.stack:
            return self.stack.pop(-1)
        else:
            raise LookupError('Stack is empty!')

    def is_empty(self):
        return bool(self.stack)

    def top(self):
        if self.stack:
            return self.stack[-1]
        else:
            raise LookupError('Stack is empty!')

    def find(self, v):
        return v in self.stack

class TreeNode:
    '''
    Nodes of the space tree
    '''
    global_node_id=0
    def __init__(self,iplist,_partent=None):
        if _partent==None:
            self.level=1
        else:
            self.level=_partent.level+1
        self.iplist=iplist    
        self.parent=_partent
        self.childs=[]
        TreeNode.global_node_id+=1
        self.node_id=TreeNode.global_node_id
        self.diff_delta = 0   
        self.DS=Stack()
        self.TS=[]    
        self.SS=set() 
        self.NDA=0   
        self.AAD=0.0  
        self.last_pop=0 
        self.last_pop_value=0


    def isLeaf(self):
        return self.childs==[]
    
    def Steady(self,delta):
        """
        Determine if all vector sequences in the node have the same value in dimension delta

        Args：
            delta：Dimensions to be judged

        Return：
            same：True when the entropy of the vector sequence in the node is 0 in the delta dimension
        """
        same=True
        l=len(self.iplist)
        if l==0:
            print("the node {}  iplist has no seeds".format(self.global_node_id))
            exit()
        else:
            v1=self.iplist[0]
            for v2 in self.iplist:
                if v1[delta-1]!=v2[delta-1]:
                    same=False
                    break
        return same
    

    # Calculate the entropy value on each dimension
    def get_entropy(self,i):
        info_d={} # Count the frequency of each dimension and save it in the dictionary. eg:('1'.2)
        for ip in self.iplist:
            if ip[i] in info_d:
                info_d[ip[i]]=info_d[ip[i]]+1
            else:
                info_d[ip[i]]=1
        entropy=0.0
        p=0.0
        size=len(self.iplist)
        if size==0:
            exit()
        for key in info_d:
            p=float(info_d[key])/size
            entropy=entropy+(-p*math.log(p))
        return entropy


    # Find the appropriate split point (the return value is the dimension value and the latitude value minus one to take the corresponding value)): the entropy value is not zero and up to the minimum
    def get_splitP(self,delta):
        best_entropy,best_postion=float("Inf"),-2  
        for i in range(int(128/math.log(delta,2))):
            entropy=self.get_entropy(i)
            if entropy==0:
                continue
            else:
                if best_entropy>entropy:
                        best_entropy=entropy
                        best_postion=i
        return best_postion+1


    def ExpandTS(self, delta):
        """
        Do Expand operation on TS of node

        Args：
            delta：Current dimensions that need to be Expanded
        """
        if self.TS==[]: # The TS of the leaf node is initially a subsequence of the corresponding address vector
            for ip in self.iplist:
                self.TS.append(deepcopy(ip))
        self.last_pop=delta

        for v in self.TS:
            v[delta-1]=-1

        # Delete duplicate members in TS
        self.TS = list(set([tuple(v) for v in self.TS]))
        self.TS = [list(v) for v in self.TS]


    def  OutputNode(self):
        """
        Output information about a node

        Args:
            node: Current Node
            V： Address vector sequence 
        """

        if self.diff_delta == 0:
            print('[leaf]', end = ' ')
        print('Node ID: ',self.node_id)
        print('[+]{} Address(es):'.format(len(self.iplist)))
        for i in self.iplist:
            print(i)
        if self.diff_delta != 0:
            print('[+]Lowest variable dim:%d' % self.diff_delta) 
        print('[+]Parent:', end = ' ')
        if self.parent == None:
            print('None')
        else:
            print(self.parent.node_id)
        print('[+]Childs:', end = ' ')
        if self.childs == []:
            print('None')
        else:
            for child in self.childs:
                print(child.node_id, end = ' ')
            print()
        print('[+]DS:')
        print(self.DS.stack)
        print('[+]TS:')
        if self.TS == []:
            print('None')
        else:
            for v in self.TS:
                print(v)
        print('[+]SS:')
        if self.SS == []:
            print('None')
        else:
            for v in self.SS:
                print(v)
        print('[+]NDA:', self.NDA)
        print('\n')

def Intersection(l1,l2):
    '''
    Calculate the duplicate elements of two lists
    '''
    intersection=[v for v in l1 if v in l2]
    return intersection