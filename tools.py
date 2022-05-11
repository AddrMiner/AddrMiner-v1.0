"""
    Necessary processing functions and tools
"""
import numpy as np
import seaborn as sns
import pandas as pd
import ipaddress
from tqdm import tqdm
import hdbscan
import math
import pickle
import random
from collections import Counter
from scipy import stats
from random import shuffle

# Standardising ipv6 addresses
def standardize(ipv6=""):
    try:
        t = ipaddress.ip_address(ipv6.strip())
        return t.exploded
    except ValueError:
        return None

def calIIDEntropy(ipv6,base=None):
    x = "".join(ipv6.split(":")[4:])
    d = Counter(x)
    if base == None:
        base = len(d)
    e = 0.0
    for c,ctn in d.items():
        _p = float(ctn)/len(x)
        e += -1 * _p * math.log(_p,base)
    return e

# Pre-processing of addresses: normalisation, extraction of ASN and BGP prefixes
def handle(data, ipasn_dbpath):
    data['std_ipv6'] = data['ipv6'].map(standardize)

    import pyasn
    asndb = pyasn.pyasn(ipasn_dbpath) # 105967

    data['asn'] = data['std_ipv6'].map(lambda x:np.nan if asndb.lookup(x)[0] == None else asndb.lookup(x)[0])
    data['bgp_prefix'] = data['std_ipv6'].map(lambda x:np.nan if asndb.lookup(x)[1] == None else asndb.lookup(x)[1])
    return data

def calEntropy(x,base=None):
    d = Counter(x)
    if base == None:
        base = len(d)
    e = 0.0
    for c,ctn in d.items():
        _p = float(ctn)/len(x)
        e += -1 * _p * math.log(_p,base)
    return e

# Use of type and entropy judgements
def getPattern(ipv6_list,types=4,emin=0.4,emax=0.8):
    """
    Args:
        ipv6_list: ipv6 addresses
        types: Threshold for the number of types of values per half-byte,[1,16]
        emin: Shannon Entropy lower bound (0,1)
        emax: Shannon entropy upper bound (0,1)
    Return:
        pattern: address pattern
    """
    pattern = []
    # Iterate to get the full value of each half-byte bit (character to number type conversion)
    R = [] 
    for i in range(32):
        t = []
        for ipv6 in ipv6_list:
            ipv6 = ipv6.replace(":","") 
            t.append(ipv6[i])
        R.append(t)
    # Calculating Shannon entropy
    e_list = []
    for i in range(32):
        e = calEntropy(R[i],base=16)
        e = round(e,3)
        e_list.append(e)
    length = len(ipv6_list)
    # Generating pattern strings
    for i in range(32):
        # The dictionary format for the number of values of each half-byte bit in the address set
        d = Counter(R[i]) 
        if len(d)==1:
            # single pattern
            pattern.append(list(d.keys())[0])
        elif len(d) <= types and e_list[i] < emin:
            # Use list pattern
            choosed_v = []
            for k,v in d.items():
                if v > length/32:
                    choosed_v.append(k)
            choosed_v = sorted(choosed_v)# This must be sorted
            pattern.append("[" + "".join(choosed_v) +"]")  
        else:
            if e_list[i] > emax:
                # wildcard pattern
                pattern.append("?")
            else:
                # range pattern
                a = min(list(d.keys()))
                b = max(list(d.keys()))
                if a == '0' and b == 'f':
                    pattern.append("?")
                else:
                    pattern.append("[%s-%s]" % (a,b))
    # Scan the pattern string from left to right and determine if it is merged into dict
    # Note that each element of the vector that needs to be passed in is an int/float, the ones in R[0] are char
    # Using the Spearman correlation coefficient
    return "_".join(pattern)

def getSet(symbol):
    c_set = "0123456789abcdef"
    if symbol[0] =='?':
        return set(list(c_set))
    if symbol[0] == '[':
        if len(symbol) == 5 and symbol[2] == '-':
            t1 = symbol[1]
            t2 = symbol[3]
            return set(list(c_set[int(t1,16):int(t2,16)+1]))
        return set(list(symbol[1:-1]))
    return set(symbol)

def setSet(s):
    c_set = "0123456789abcdef"
    if len(s) == 1:
        return ''.join(s)
    if len(s) == len(c_set):
        return '?'
    t1 = min(s)
    t2 = max(s)
    test_s = set(list(c_set[int(t1,16):int(t2,16)+1]))
    if test_s == s and (int(t2,16) - int(t1,16))>1:
        return '[%s-%s]' % (t1,t2)
    else:
        s = sorted(list(s))
        return '[' + ''.join(s) + ']'

def mergePattern(pattern1,pattern2,length=0):
    new_pattern = []
    p1 = pattern1.split("_")
    p2 = pattern2.split("_")

    for i in range(len(p1)):
        if i < length:
            new_pattern.append(p1[i])
        else:
            s1 = getSet(p1[i])
            s2 = getSet(p2[i])
            new_pattern.append(setSet(s1|s2))
    return "_".join(new_pattern)

# Calculate the similarity matrix
def genMatrix(pattern_list):
    L = len(pattern_list)
    matrix = np.zeros([L, L]) 
    with tqdm(total = L) as pbar:
        for i in range(0,L):
            for j in range(i+1,L):
                score = calSimilarity(pattern_list[i], pattern_list[j])
                matrix[i][j] = score
            pbar.update(1)
    return matrix

# Calculating the similarity function
def calSimilarity(pattern1, pattern2, extra_len=0):
    p1 = pattern1.split("_")[extra_len:]
    p2 = pattern2.split("_")[extra_len:]
    score = 0.0
    s_c = "0123456789abcdef"
    for a,b in zip(p1,p2):
        if ('-' in a or a=='?' or a[0]=='[') and ('-' in b or b=='?' or b[0]=='['):
            c1 = getSet(a)
            c2 = getSet(b)
            score += len(c1&c2)/len(c1|c2) + 1.0
        elif len(a)==1 and len(b)==1 and a!='?' and b!='?': # Only double-single
            score += 1.0 if a==b else 0.0
        else:
            continue
    return score

def shuffle_str(s):
    # Converting strings to lists
    str_list = list(s)
    # Call the shuffle function of the random module to break up the list
    shuffle(str_list)
    # Convert list to string
    return ''.join(str_list)

# Some seed addresses may not be in the generated address range
def genAddrByPattern(pattern, limit=None):
    new_ipv6 = []
    c_set = "0123456789abcdef"
    def dfs(p_list,index,ans):
        if index == len(p_list):
            ip = ""
            for i in range(0,32,4):
                ip += ":" + ans[i:i+4]
            new_ipv6.append(ip[1:])
            return
        if p_list[index] == '?':
            for c in shuffle_str(c_set):
                dfs(p_list,index+1,ans+c)
                if limit is not None and len(new_ipv6) >= limit:return
        elif p_list[index][0] == '[':
            if len(p_list[index]) == 5 and p_list[index][2] == '-':
                t1 = p_list[index][1]
                t2 = p_list[index][3]
                for c in shuffle_str(c_set[int(t1,16):int(t2,16)+1]):
                    dfs(p_list,index+1,ans+c)
                    if limit is not None and len(new_ipv6) >= limit:return
            else:
                for c in shuffle_str(p_list[index][1:-1]):
                    dfs(p_list,index+1,ans+c)
                    if limit is not None and len(new_ipv6) >= limit:return
        else:
            assert len(p_list[index]) == 1
            dfs(p_list, index+1, ans+p_list[index])
    dfs(pattern.split("_"),0,"")
    return new_ipv6

# Analyse pattern full space size
def calSpace(p):
    a = 16**p.count('?')
    b = 1
    for s in p.split("_"):
        if s[0] == '[':
            if len(s) == 5 and s[2] == '-':
                b *= int(s[3],16) - int(s[1],16) + 1
            else:
                b *= (len(s)-2)
    return a*b



