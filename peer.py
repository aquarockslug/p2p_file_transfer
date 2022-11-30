import sys
import os
import threading
import json
# from os import listdir, getcwd
from socket import *

# py peer.py A 127.0.0.1 1111 /files
# py peer.py B 127.0.0.2 2222 /filesB 127.0.0.1 1111
# g test.txt 127.0.0.1 1112
# g test.txt 127.0.0.2 2223
# f test.txt

prompt = """Your options:\n1. [s]tatus\n2. [f]ind <filename>
3. [g]et <filename> <peer IP> <peer port>\n4. [q]uit\nYour choice: """

args = sys.argv[1:]
if (len(args) != 4 and len(args) != 6):
    print("incorrect number of arguments, must be 4 or 6")
    sys.exit(0)

neighbors = []
files = os.listdir(os.getcwd() + args[3])

# only 2 sockets required?
lookupSocket = socket(AF_INET, SOCK_DGRAM)  # UDP datagram
clientSocket = socket(AF_INET, SOCK_DGRAM)
responseSocket = socket(AF_INET, SOCK_DGRAM)
clientTransferSocket = socket(AF_INET, SOCK_STREAM)  # TCP
transferSocket = socket(AF_INET, SOCK_STREAM)

peer = {
    'name': args[0],
    'ip': args[1],
    'lookupPort': int(args[2]),
    'transferPort': int(args[2]) + 1,
    'path': args[3]
}

if (len(args) == 6):  # join network
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
    print("%s: Connected to %s %s:%s" % (peer['name'], firstNeighbor['name'],
                                          firstNeighbor['ip'], firstNeighbor['lookupPort']))
    neighbors.append(firstNeighbor)

# def joinRequest()

##########################################################################


def lookup():
    lookupSocket.bind((peer['ip'], peer['lookupPort']))
    print("running lookup on %s:%s" % (peer['ip'], peer['lookupPort']))
    while True:
        request = lookupSocket.recvfrom(1024)  # wait for request
        message = json.loads(request[0])
        returnAddress = request[1]

        if (message['type'] == 'join'):
            newNeighbor = message['peer']
            neighbors.append(newNeighbor)
            lookupSocket.sendto(str.encode(peer['name']), returnAddress)
            print("%s: Accepting %s %s:%s" % (peer['name'], newNeighbor['name'],
                                              newNeighbor['ip'], newNeighbor['lookupPort']))

        elif (message['type'] == 'lookup'):
            target = message['filename']
            print("File request %s received from %s" % (target, message['names'][0]))
            # discard request if I am already in message['peers']
            for visitedPeer in message['names']:
                if (visitedPeer == peer['name']):
                    message = None
                    print("Duplicate; discarding.")
                    break

            #sourcePeer = message['peer']
            if message: # new lookup request
                if haveFile(target):
                    print("File %s available on %s" % (target, peer['path']))
                    response = {'type': 'response', 
                                'ip': peer['ip'], 
                                'port': peer['transferPort'],
                                'filename': target}

                    print("send response: %s" % response)
                    clientSocket.sendto(str.encode(json.dumps(response)), 
                        (message['source']['ip'], message['source']['lookupPort']))
                else:
                    message['names'].append(peer['name'])   
                    print("Flooding to neighbors:")
                    # forward lookup request to neighbors except returnAddress

        elif (message['type'] == 'response'):
            print("Response received")
            get([message['filename'], message['ip'], message['port']]) 

        elif (message['type'] == 'disconnect'):
            for neighbor in neighbors:  
                if (neighbor['name'] == message['name']):
                    neighbors.remove(neighbor)
                    print("%s is offline" % message['name'])
                    break


def haveFile(target):
    files = os.listdir(os.getcwd() + peer['path'])
    for file in files:
        if file == target:
            return True
    else:
        return False

##########################################################################


def transfer():
    transferSocket.bind(('', peer['transferPort']))
    transferSocket.listen(10)
    while True:
        connectionSocket, addr = transferSocket.accept()  # wait for incoming connection
        print("Connection established")
        message = connectionSocket.recvfrom(1024)  # wait for message
        requestedFilename = message[0].decode('UTF-8')
        sendfile(connectionSocket, requestedFilename) # new thread?
        print("Received request for %s from %s" %
              (requestedFilename, connectionSocket.getpeername()))


def sendfile(connectionSocket, filename):
    file = ""
    for currFilename in files:
        if currFilename == filename:
            file = open(os.getcwd() + peer['path'] + "/" + currFilename)
            connectionSocket.send(str(file.read()).encode())
    if file:
        print("file sent")
    else:
        connectionSocket.send(str("Error: no such file").encode())
        print("Error: no such file")

##########################################################################

def ui():
    command = ''
    options = {'s': status, 'f': find, 'g': get}
    while (command != 'q'):
        choice = input(prompt).split()
        if (len(choice) == 0):
            continue
        command = choice[0]
        if (list(options.keys()).count(command) == 1):  # if valid choice
            options[command](choice[1:])  # call command with arguments
    quit()


def status(args):
    print("Peers:")
    for neighbor in neighbors:
        print("\t%s %s:%s" %
              (neighbor['name'], neighbor['ip'], neighbor['lookupPort']))
    files = os.listdir(os.getcwd() + peer['path'])  # update files
    print("Files: %s" % peer['path'])
    for file in files:
        print("\t%s" % file)


def find(args):
    if len(args) != 1:
        print("incorrect number of arguments, must be 1")
        return

    target = args[0]
    print("find %s" % target)
    
    # Check if its saved locally
    if haveFile(target):
        print("File %s available on %s" % (target, peer['path']))

    # send lookup request to all neighbors
    lookupRequest = {'type': 'lookup', 'names': [peer['name']], 
                     'filename': target, 'source': peer}
    print("File discovery in progress: Flooding")
    for neighbor in neighbors:
        print("\tsending to %s" % neighbor['name'])
        clientSocket.sendto(str.encode(json.dumps(lookupRequest)),
                            (neighbor['ip'], neighbor['lookupPort']))

def get(args):
    if (len(args) == 3):
        filename = args[0]
        targetIp = args[1]
        targetPort = int(args[2])
        clientTransferSocket.connect((targetIp, targetPort))
        print("Requesting %s from %s" % (filename, targetIp))
        clientTransferSocket.send(str.encode(filename)) # send filename
        file = clientTransferSocket.recv(2048).decode() # wait for response
        if file != "Error: no such file":
            print("File received")
            newFile = open(os.getcwd() + peer['path'] + "/" + filename, 'w')
            newFile.write(file)
            newFile.close()
        else:
            print(file)
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
