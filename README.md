
On this website we present additional information about our ATC paper Clusters in the Expanse:  AddrMiner: A Comprehensive Global Active IPv6 Address Discovery System


## Paper
### Abstract

  Fast Internet-wide scanning is essential for network situational awareness and asset evaluation. However, the vast IPv6 address space makes brute-force scanning infeasible. Although state-of-the-art techniques have made effective attempts, these methods do not work in seedless regions, while the detection efficiency is low in regions with seeds. Moreover, the constructed hitlists with low coverage cannot truly represent the active IPv6 address landscape of the Internet.

  This paper introduces AddrMiner, a systematic and comprehensive global active IPv6 address probing system. We divide the IPv6 address space regions into three kinds according to the number of seed addresses to discover active IPv6 addresses from scratch, from few to many. For the regions  with no seeds, we present AddrMiner-N, leveraging an organization association strategy to mine active addresses. It fills the gap of address probing in seedless regions and finds active addresses covering 86.4K BGP prefixes, accounting for 81.6% of the probed BGP prefixes. For the regions with few seeds, we propose AddrMiner-F, utilizing  a similarity matching strategy to probe active addresses further. The hit rate of active address probing is improved by 70\%-150\% compared to existing algorithms. Moreover, for the regions with sufficient seeds, we present AddrMiner-S  to generate target addresses based on reinforcement learning dynamically. It nearly doubles the hit rate compared to the state-of-the-art algorithms.

  Finally, we deploy AddrMiner and discover 2.1 billion active IPv6 addresses, including 1.7 billion de-aliased active addresses and 0.4 billion aliased addresses, through continuous probing for 13 months. We would like to further open the door of IPv6 measurement studies by publicly releasing AddrMiner and sharing our data.

## Artifact Environment

  Our artifact AddrMiner runs on nodes with the identical hardware configuration of Intel Core Processor (Broadwell) 32-core CPU, 64GiB RAM, and 1TB HDD. The software configuration is also the same for each node. The operating system runs on Ubuntu/Linux 18.04.5 LTS with kernel 4.15.0-162-generic x86_64. The four nodes are deployed in a 10 Gigabit bandwidth IPv6 network. （Smaller tests can lower the configuration）

  AddrMiner is compateible with Python3.6.9 You can install the requirements for your version. 

## Dependencies and installation
  AddrMiner uses the following packages:
 
* argparse
  ```
  pip3 install argparse
  ```

* Pyasn 1.6.1
  ```
  pip3 install pyasn
  ```
  
* Community 1.0.0b
  ```
  pip3 install community
  ```
  
* Cython 0.29.28
  ```
  pip3 install Cython
  ```
  
* Infomap 2.3.0
  ```
  pip3 install infomap
  ```

* zmapv6 (ask in IPv4 network)

  Building from Source

  ```
  git clone https://github.com/tumi8/zmap.git
  cd zmap
  ```
  Installing ZMap Dependencies

  On Ubuntu-based systems
  ```
  sudo apt-get install build-essential cmake libgmp3-dev gengetopt libpcap-dev flex byacc libjson-c-dev pkg-config libunistring-dev
  ```
  Building and Installing ZMap

  ```
  cmake .
  make -j4
  sudo make install
  ```

## File Description
  - Data: seed address and bgp prefix file, where the seed address format is csv, there are four columns, respectively, ipv6,std_ipv6,asn,bgp_prefix, put the seed address in the ipv6 column
  - pk_data: store the pattern library
  - BGP: store three scenarios of BGP prefix information
  - result: store probe results


## Usage
Parameter meaning introduction:
  - output: type=str, output directory name
  - prefix:type=str,BGP prefix
  - budget: type=int, the upperbound of scan times
  - IPv6:type=str, local IPv6 address
  - hmin:type=float,default=14.0,similarity threshold
  - hmax:type=float,default=16.0,similarity threshold
  - algorithm:type=str,default='louvain', graph community discovery algorithm
  - sst: type=int, default=1e7, mode space upper limit
  - types:type=int,default=4,nibble value type threshold
  - emin:type=float,default=0.4,Shannon entropy lower bound,(0,1)
  - emax:type=float,default=0.8,Shannon entropy upper bound,(0,1)
  - kheap:type=int,default=10,the number of similar addresses selected by topk strategy


### running example

  Probing for all BGP prefixes
  
  Note: 
  Because the number of BGP prefixes exceeds 150,000, the detection period for all prefixes exceeds 1 month. In order to facilitate the test and ensure the fairness of the test, we randomly select 500 BGP prefixes in each scenarios (sufficient seed scenario, few seed scenario and no seed scenerio) for experimental testing.
  
  ```
  sudo python3 AddrMiner.py --output=outputDir --budget= the upperbound of scan times each bgp prefix --IPv6=IPv6addr
  eg: sudo python3 AddrMimer.py  --output=result --budget=100  --IPv6=XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX:XXXX
  ```


（Of course, our system relies on the IPv6 network, so if you do not have a test environment at the time of testing, we can provide it for you. If you need assistance with the environment, please contact the email address below.）



# Data
In order to support IPv6 network related research, we provide more data about hitlist(active IPv6 addresses) and address fingerprint information.
If you want more data, you can send a request to sgl18@mails.tsinghua.edu.cn. 
The request should include the work department, the purpose of data usage, and the data content obtained.





