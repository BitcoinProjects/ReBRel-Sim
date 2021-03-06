#################################################
#                                               #
# btcnetsim: main                               #
#                                               #
#################################################

import sys
from subprocess import Popen
import os
import json
import time
import random

import btcnet
import txgen

#Globals


def main():
    # Create the network
    if (sys.argv[1] == "create"):
        nettype = sys.argv[2]
        numReach = sys.argv[3]
        numUnreach = sys.argv[4]

        #cleanup logs
        os.system("rm log/*")
        os.system("rm db/*.db")

        if nettype == "std":
            btcnet.createStandardNetwork(int(numReach), int(numUnreach))
        if nettype == "clover":
            probDiffuse = sys.argv[5]

            btcnet.createCloverNetwork(int(numReach), int(numUnreach), probDiffuse)
        if nettype == "dandelion":
            btcnet.createDandelionNetwork(int(numReach), int(numUnreach))

        print("DONE\n")
        return

    # Delete the network
    if (sys.argv[1] == "delete"):
        btcnet.deleteNetwork()
        print("DONE\n")
        return

    # Generate transactions
    if (sys.argv[1] == 'txinit'):
        txgen.initTxSim()
        return

    if (sys.argv[1] == 'runsim'):
        duration = int(sys.argv[2])
        threads = int(sys.argv[3])
        txgen.runTxSim(duration,threads)

        return

    # Generate transactions
    if (sys.argv[1] == 'txrun'):
        duration = int(sys.argv[2])
        threads = int(sys.argv[3])
        txgen.runTxSim(duration,threads)
        return

    # Generate changes in the network
    if (sys.argv[1] == 'netrun'):
        return

    # Run external test script
    if (sys.argv[1] == 'testrun'):
        return

    else:
        print "\nUSAGE:\n"
        print "sudo python btcnetsim.py CMD [args]\n"
        print "CMDs:"
        print "create BINDIR REACH UNREACH : Create REACH reachable nodes and UNREACH unreachable nodes, using binaries in BINDIR."
        print "delete : Delete bitcoin blockchain."
        print "txrun: Make nodes generate random transactions."
        print "netrun: Generate random changes in the network."
        print "add BINDIR NUM: add NUM nodes using binaries in BINDIR."


main()
