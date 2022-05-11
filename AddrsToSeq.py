#!/usr/bin/python3.6
# encoding:utf-8
import math, ipaddress
from copy import deepcopy
# import pdb
# import ptvsd
# ptvsd.enable_attach(('219.243.212.103',3000))
# ptvsd.wait_for_attach()

"""
Load IPv6 addresses from a file and convert the IPv6 addresses into an ordered vector sequence
"""

class AddrVecList(list):
    """
    Address vector list, inherited from built-in list type, overloaded with >= and <= operators for easy comparison when sorting
    """

    def __init__(self):
        list.__init__([])

    # Overloading the >= operator
    def __ge__(self, value):
        ge = True
        for i in range(len(self)):
            if self[i] < value[i]:
                ge = False
                break
        return ge

    # Overloading the <= operator
    def __le__(self, value):
        le = True
        for i in range(len(self)):
            if self[i] > value[i]:
                le = False
                break
        return le

# def InputAddrs(input='files/source.hex', beta=16):
def InputAddrs(input='data.csv', beta=16):
    """
    Load a list of IPv6 addresses from the input file and convert it to an ordered sequence of address vectors

    Args：
        input：Files with all seed addresses stored (.hex: without colon; .txt: with colon, compressible)
        beta: The base of each dimension of the address vector

    Return:
        V：Ordered sequence of address vectors
    """

    IPv6 = []
    count = 0
    for line in open(input):
        if line != '':
            IPv6.append(line)
            count += 1
    IPv6 = [addr.strip('\n') for addr in IPv6]
    
    if input[-3:] == 'txt':
    # Convert all IPv6 addresses to uncompressed form
        for i in range(len(IPv6)):
            IPv6[i] = ipaddress.IPv6Address(IPv6[i])
            IPv6[i] = IPv6[i].exploded
            IPv6[i] = IPv6[i].replace(':','')

    V = AddrsToSeq(IPv6, math.log(beta, 2))
    return V


def AddrsToSeq(addr=[], m=4, lamda=128):
    """
    Converting a standard IPv6 address list into an ordered vector list

    Args：
        addr：A standardized list of IPv6 addresses, each element of which is a colonless hexadecimal representation of the IPv6 address
        m：The length of the binary number represented by each dimension of the address vector
        lamda：Total length of IPv6 address (default is 128)

    Returns：
        A two-dimensional list of IPv6 address vectors obtained by conversion.
        Each element in each one-dimensional list represents the decimal value of an IPv6 address vector in one dimension
    """

    if lamda % m != 0:
        print('!!EXCEPTION: lamda % m != 0')
        exit()
    V = AddrVecList()
    # V = []  # Address vector list
    # N = []  # A list of integers corresponding to addresses for easy sorting
    for i in range(len(addr)):
        if addr[i] == '':
            break
        # addr_hex = addr[i].replace(':','')
        N = int(addr[i], 16)   # Converting IPv6 addresses (strings) to their corresponding integer values
        v = []  # Value of each address vector (list of integers)
        for delta in range(1, int(lamda/m + 1)):
            x1 = int(2 ** (m*(lamda/m - delta)))    # Note that the result needs to be explicitly converted to an integer
            x2 = N % int(x1 * (2 ** m))
            x3 = N % x1
            v.append(int((x2 - x3)/x1))
        V.append(v)
    V = sorted(V)
    return V


def SeqToAddrs(seq):
    """
    Converting a list of address vectors to a collection of IPv6 addresses (strings)

    Args：
        seq：List of address vectors representing the scan space (may have dimensions that are Expanded)

    Return：
        addr_list：List of IPv6 addresses (in compressed form)
    """

    if seq == []:
        return set()

    m = int(128/len(seq[0])) # The length of the binary number represented by each dimension of the address vector
    seq = deepcopy(seq)
    value = 0   # The integer value corresponding to the address     
    # addr_set = set()
    addr_list = []
    a_vec = seq[0]  # An address vector to determine which dimension has been Expanded
                    # (All vectors in the list are of the same dimension by Expand)
    vec_dim = len(a_vec)   # Dimension of the address vector

    for i in range(vec_dim):
        if a_vec[i] == -1: # i dimension is Expanded, need to add address to the list
            seq = SeqExpand(seq, i, m)

    for vector in seq:
        for v_i in vector:
            value = value * (2 ** m) + v_i
        addr = ipaddress.IPv6Address(value)
        # addr_set.add(str(addr))
        addr_list.append(str(addr))
        value = 0

    # return addr_set
    return addr_list


def get_rawIP(IP):
    # Standard IP -> hex IP
    seglist=IP.split(':')
    if seglist[0]=='':
        seglist.pop(0)
    if seglist[-1]=='':
        seglist.pop()
    sup=8-len(seglist)
    if '' in seglist:
        sup+=1
    ret=[]
    for i in seglist:
        if i=='':
            for j in range(0,sup):
                ret.append('0'*4)
        else:
            ret.append('{:0>4}'.format(i))
    rawIP=''.join(ret)
    assert(len(rawIP)==32)
    return rawIP

    
def SeqExpand(seq, idx, m=4):
 
    new_seq = []
    for vector in seq:
        for v in range(2 ** m):
            vector[idx] = v
            new_seq.append(deepcopy(vector))
    
    return new_seq

if __name__ == '__main__':
    # IPv6 = ["2c0f:ffd8:0030:ac1d:0000:0000:0000:0146","2001:0000:0000:0000:0000:0000:1f0d:4004"]
    # for i in range(len(IPv6)):
    #     IPv6[i]=IPv6[i].replace(":","")
    # V = AddrsToSeq(IPv6)
    # print(SeqToAddrs(V))
    # # pdb.set_trace()

    # V = InputAddrs()
    # if V == None:
    #     print("V is none!")
    # else:
    #     for v in V:
    #         print(v)
    InputAddrs("data.csv")
