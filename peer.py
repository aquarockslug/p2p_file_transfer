import sys, os, threading, json
#from os import listdir, getcwd
from socket import *

# py peer.py A 127.0.0.1 1111 /files 
# py peer.py B 127.0.0.2 2222 /filesB 127.0.0.1 1111

prompt = """Your options:\n1. [s]tatus\n2. [f]ind <filename>
3. [g]et <filename> <peer IP> <peer port>\n4. [q]uit\nYour choice: """

args = sys.argv[1:]
if (len(args) != 4 and len(args) != 6): 
    print("incorrect number of arguments, must be 4 or 6")
    sys.exit(0)

neighbors = []
files = os.listdir(os.getcwd() + args[3])

# 4 -> 2 sockets?
lookupSocket = socket(AF_INET, SOCK_DGRAM)# UDP datagram
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientTransferSocket = socket(AF_INET, SOCK_STREAM)
transferSocket = socket(AF_INET, SOCK_STREAM)

peer = {
    'name': args[0],
    'ip': args[1],
    'lookupPort': int(args[2]),
    'transferPort' : int(args[2]) + 1,
    'path': args[3]
}  

if (len(args) == 6): # join network
    firstNeighbor = {
        'ip': args[4],
        'lookupPort': int(args[5])
    }
    # send join request to firstNeighbor
    joinRequest = {'type': 'join', 'peer': peer}
    clientSocket.sendto(str.encode(json.dumps(joinRequest)), 
                        (firstNeighbor['ip'], firstNeighbor['lookupPort']))
    # wait for name as acknowledgment
    firstNeighbor['name'] = clientSocket.recvfrom(1024)[0].decode('UTF-8')
    print("%s: Connected to %s %s:%s" %  (peer['name'], firstNeighbor['name'], 
                                   firstNeighbor['ip'], firstNeighbor['lookupPort']))
    neighbors.append(firstNeighbor)

#def joinRequest()

##########################################################################
def lookup():
    lookupSocket.bind((peer['ip'], peer['lookupPort']))
    print("running lookup on %s:%s" % (peer['ip'], peer['lookupPort']))
    while True:
        request = lookupSocket.recvfrom(1024) # wait for request
        message = json.loads(request[0])
        returnAddress = request[1]

        if (message['type'] == 'join'):   
            newNeighbor = message['peer']
            neighbors.append(newNeighbor)
            lookupSocket.sendto(str.encode(peer['name']), returnAddress)
            print("%s: Accepting %s %s:%s" % (peer['name'], newNeighbor['name'], 
                                         newNeighbor['ip'], newNeighbor['lookupPort']))
        #elif (message['type'] == 'lookup'):
        #elif (message['type'] == 'response'):
        elif (message['type'] == 'disconnect'):
            for neighbor in neighbors:
                if (neighbor['name'] == message['name']):
                    neighbors.remove(neighbor)
                    print("%s is offline" % message['name'])

##########################################################################
def transfer():
    #transferSocket.bind((peer['ip'], peer['transferPort']))
    transferSocket.bind(('', peer['transferPort']))
    transferSocket.listen(10)
    while True:
        connectionSocket, addr = transferSocket.accept() # wait for incoming connection
        print("Connection established")
        message = connectionSocket.recvfrom(1024) # wait for message
        requestedFilename = message[0].decode('UTF-8')
        print("Received request for %s from %s" % 
                (requestedFilename, connectionSocket.getpeername()))
        for filename in files:
            if filename == requestedFilename:
                file = open(os.getcwd() + peer['path'] + "/" + filename)
                connectionSocket.send(str(file.read()).encode())
                print("file sent")
                # connectionSocket.send(str("Error: no such file").encode())
                # print("Error: no such file")

##########################################################################
def ui():
    command = ''
    options = {'s': status, 'f': find, 'g': get}
    while (command != 'q'):
        choice = input(prompt).split()
        if (len(choice) == 0):
            continue
        command = choice[0]
        if (list(options.keys()).count(command) == 1):# if valid choice
            options[command](choice[1:])# call corresponding command with arguments
    quit()

def status(args):
    print("Peers:")
    for neighbor in neighbors:
        print("\t%s %s:%s" % (neighbor['name'], neighbor['ip'], neighbor['lookupPort']))
    files = os.listdir(os.getcwd() + peer['path'])# update files
    print("Files: %s" % peer['path'])
    for file in files:
        print("\t%s" % file)

def find(args):
    if (len(args) == 1):
        filename = args[0]  
        print("find %s", filename)
    else: 
        print("incorrect number of arguments, must be 1")
    # call get([filename, peerIp, peerPort])

def get(args):
    if (len(args) == 3):
        filename = args[0]
        targetIp = args[1]
        targetPort = int(args[2])
        clientTransferSocket.connect((targetIp, targetPort))
        print("Requesting %s from %s" % (filename, targetIp))
        clientTransferSocket.send(str.encode(filename))
        file = clientTransferSocket.recv(2048).decode()
        if file == "Error: no such file":
            print(file)
        else:
            print("File received")
            newFile = open(os.getcwd() + peer['path'] + "/" + filename, 'w')
            newFile.write(file)
            newFile.close()
    else: 
        print("incorrect number of arguments, must be 3")

def quit():
    disconnectNotice = {'type': 'disconnect', 'name': peer['name']}
    for neighbor in neighbors:
        print("Notifying %s of departure" % neighbor['name'])
        clientSocket.sendto(str.encode(json.dumps(disconnectNotice)), 
                            (firstNeighbor['ip'], firstNeighbor['lookupPort']))
    print("Quitting")
    sys.exit(0)

##########################################################################

def main():
    uiThread = threading.Thread(target=ui, args=())
    lookupThread = threading.Thread(target=lookup, args=())
    transferThread = threading.Thread(target=transfer, args=())
    
    uiThread.start()
    lookupThread.start()
    transferThread.start()
    
main()