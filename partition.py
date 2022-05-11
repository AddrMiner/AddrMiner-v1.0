"""
    Divide BGP prefixes into three scenarios based on seed addresses
    input: seeds
    output: BGP-N, BGP-F, BGP-S
"""
import pandas as pd
import pyasn
from tools import *

def get3bgp(seeds_path):
    bgps = {}
    ansdb = pyasn.pyasn("./data/ipasn.dat")
    seeds = pd.read_csv(seeds_path,encoding= 'utf-8')
    seeds = seeds['ipv6'].tolist()
    for addr in seeds:
        bgp=ansdb.lookup(addr)[1]
        if bgp not in bgps: bgps[bgp] = []
        bgps[bgp].append(standardize(addr))
    
    with open("./data/ipasn.dat") as f:
        lines = f.readlines()
    all_bgp_prefix = set([ i.split("\t")[0] for i in lines[6:]])
    all_bgp_prefix  = [ i for i in all_bgp_prefix if "::" in i]
    
    for bgp in all_bgp_prefix:
        if bgp not in bgps: bgps[bgp] = []
    
    bgp_n = {}
    bgp_f = {}
    bgp_s = {}
    for bgp in bgps:
        if bgp==None: continue
        if len(bgps[bgp]) < 10 and len(bgps[bgp]) > 0: bgp_f[bgp] = bgps[bgp]
        if len(bgps[bgp]) > 10: bgp_s[bgp] = bgps[bgp]
        if len(bgps[bgp]) == 0: bgp_n[bgp] = bgps[bgp]

    with open("BGP/BGP-N.pk","wb") as f:
        pickle.dump(bgp_n,f)
    
    with open("BGP/BGP-N","w") as f:
        for bgp in bgp_n:
            f.write(bgp+"\n")
     
    with open("BGP/BGP-F.pk","wb") as f:
        pickle.dump(bgp_f,f)
    
    with open("BGP/BGP-F","w") as f:
        for bgp in bgp_f:
            f.write(bgp+" "+str(len(bgp_f[bgp]))+"\n")
        
    with open("BGP/BGP-S.pk","wb") as f:
        pickle.dump(bgp_s,f)
    
    with open("BGP/BGP-S","w") as f:
        for bgp in bgp_s:
            f.write(bgp+" "+str(len(bgp_s[bgp]))+"\n")

if __name__ == "__main__":
    get3bgp("./data/seeds.csv")