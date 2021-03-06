
#################################################
#                                               #
# BTCNET: create and destroy network            #
#                                               #
#################################################

import os
import time
import math
import random
import json
import fileinput

import txgen

#Global
IMG = "netsim"
miner="nodeMiner"
minerBin="bin/miner"
btcdir = "/btc/"
bindir = "bin/clover/"
btcd = "bitcoind"
btcli = "bitcoin-cli"
btcdx = btcdir+btcd
btclix = btcdir+btcli
btcopt = "-regtest -fallbackfee=0.00000001 -dustrelayfee=0.0 -mintxfee=0.00000001" #-nodebuglogfile
OUTPEERS = 4

def execBTC(node, opts=""):
    os.system("docker exec -t "+node+" "+btcdx+" "+btcopt+" "+opts+" -daemon > /dev/null")

def execN(node, cmd, opts=""):
    os.system("docker exec -t "+node+" "+btclix+" -regtest "+opts+" "+cmd)

def execS(node, cmd, opts=""):
    execN(node, cmd+">/dev/null", opts)

def execNR(node, cmd, opts=""):
    assert(node != None)
    assert(cmd != None)
    return os.popen("docker exec -t "+node+" "+btclix+" -regtest "+opts+" "+cmd).read().strip()

def getNodeIP(node):
    ip = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "+node).read().rstrip()

    return ip

def getNodeList(name="node", exclude=" "):
    nodes = os.popen("docker ps --filter=\"name="+name+"\" --format '{{.Names}}'").readlines()
    nodeList = []
    for i in range(len(nodes)):
        n = nodes[i].rstrip()
        if exclude not in n:
            nodeList.append(n)

    return nodeList

def getRandList(name, num, exclude=" "):
    randList = getNodeList(name, exclude)
    
    #shuffle
    random.shuffle(randList)
    #get first num elements
    del randList[num:]

    return randList

def getRandNode(name, exclude=" "):
    rList = getRandList(name,1,exclude)
    if(len(rList)>0):
        return rList[0]


#Create a docker image with the binaries contained in 'bin/' and save it as 'netsim'
def createNodeDock(bdir=bindir):
    print "Creating node container"
    os.system("docker run -it -d --name "+IMG+" ubuntu:latest /bin/bash")
    os.system("docker cp "+bdir+" "+IMG+":/btc")
    os.system("docker commit "+IMG+" "+IMG+":node")
    os.system("docker stop "+IMG+" && docker rm "+IMG)
    print "DONE\n"

#Start a new node container
def runNode(name, options):
    os.system("docker run -it -d --rm --network=btcnet --name "+name+" "+IMG+":node /bin/bash > /dev/null")
    execBTC(name, options)
    # print "Running "+name+"("+getNodeIP(name)+")"

def renameNode(name, newName):
    os.system("docker rename "+name+" "+newName)

    #Update node DB file
    for line in fileinput.input("db/nodes.db", inplace = 1): 
      print line.replace(name+"=", newName+"="), # +"=" avoids ambiguity between R1 and R10


def connectNode(nFrom,nTo):
    toAddr = getNodeIP(nTo)
    # print "connecting "+nFrom+" to "+nTo
    execN(nFrom,"addnode "+toAddr+":18444 onetry")

#Connect a node to 3 R nodes
def connectNodes(node):
    #get random R nodes
    randList = getRandList("nodeR",OUTPEERS,node)

    # print node+":"
    for rNode in randList:
        connectNode(node,rNode)

#Run a new node and connect it
# def addNode(name, options):
#     runNode(name, options)
#     time.sleep(2)
#     connectNodes(name)

#     nodeDb = open("db/nodes.db","a")
#     nodeDb.write(name+"="+getNodeIP(name)+"\n")
#     nodeDb.close()


#Create 'numReach'+'numUnreach' containers and create random connections
def createNetwork(bdir,numReach, numUnreach, opts):
    createNodeDock(bdir)
    print "Creating network..."
    os.system("docker network create --internal --subnet 10.1.0.0/16 btcnet > /dev/null")

    print "num nodes="+str(numReach+numUnreach)

    #create nodedb
    if not os.path.exists('db'):
        os.makedirs('db')
    nodeDb = open("db/nodes.db","w")
    #creat log dir
    if not os.path.exists('log'):
        os.makedirs('log')

    print "Creating nodes..."
    #create reachable nodes
    logs=" -logips -debug=net -logtimemicros"
    btcopts = opts+logs
    for i in range(1, numReach+1):
        name="nodeR"+str(i)
        runNode(name, btcopts)
        nodeDb.write(name+"="+getNodeIP(name)+"\n")

    #create unreachable nodes
    for i in range(1, numUnreach+1):
        name="nodeU"+str(i)
        runNode(name, "-listen=0 "+btcopts)
        nodeDb.write(name+"="+getNodeIP(name)+"\n")

    nodeDb.close()
    print "DONE"
    time.sleep(5)

    #create connections
    print "Connecting nodes..."
    nodeList = getNodeList()
    for node in nodeList:
        connectNodes(node)
    print "DONE"

    return    

def createCloverNetwork(numReach=20, numUnreach=0, probDiffuse=30):
    outconns=" -outbound="+str(OUTPEERS)
    diffuse=" -probdiffuse="+probDiffuse
    opts=outconns+diffuse

    bdir = "bin/clover/"
    createNetwork(bdir, numReach, numUnreach, opts)

def createStandardNetwork(numReach=20, numUnreach=0):
    bdir = "bin/std/"
    createNetwork(bdir, numReach, numUnreach, "-outbound="+str(OUTPEERS))

def createDandelionNetwork(numReach=20, numUnreach=0):
    bdir = "bin/dandelion/"
    createNetwork(bdir, numReach, numUnreach, "")

    

# Dump logs
def dumpLogs():
    print "Dumping logs"

    nodeList = getNodeList()
    for node in nodeList:
        nLog = os.popen('docker exec -t '+node+' cat /root/.bitcoin/regtest/debug.log').read()

        f = open("log/"+node+".log", "w")
        f.write(nLog)
        f.close()

def stopContainers(name):
    print "Removing "+name+" containers"
    os.system("docker stop $(docker ps -a --filter=\"name="+name+"\" -q) > /dev/null")
    # os.system("docker rm $(docker ps -a --filter=\"name="+name+"\" -q) > /dev/null")

def stopNodes():
    print "Stopping nodes"
    nodeList = getNodeList()

    for node in nodeList:
        execS(node,"stop")

    time.sleep(5)
    dumpLogs()

# Stop and delete all 'node' containers
def deleteNetwork():
    print "Stopping network"
    stopNodes()
    stopContainers("node")