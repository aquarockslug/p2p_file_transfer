import sys, threading, json
from os import listdir, getcwd
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
files = listdir(getcwd() + args[3])

peer = {
    'name': args[0],
    'ip': args[1],
    'port': int(args[2]),
    'path': args[3]
}  
if (len(args) == 6): # join network
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    firstNeighbor = {
        'ip': args[4],
        'port': int(args[5])
    }
    # send join request to firstNeighbor
    joinRequest = {'type': 'join', 'peer': peer}
    clientSocket.sendto(str.encode(json.dumps(joinRequest)), 
                        (firstNeighbor['ip'], firstNeighbor['port']))
    # wait for name as acknowledgment
    firstNeighbor['name'] = clientSocket.recvfrom(1024)[0].decode('UTF-8')
    print("%s: Connected to %s %s:%s" % 
        (peer['name'], firstNeighbor['name'], firstNeighbor['ip'], firstNeighbor['port']))
    neighbors.append(firstNeighbor)

##########################################################################
# wait for connections
def lookup():
    lookupSocket = socket(AF_INET, SOCK_DGRAM)# UDP datagram
    lookupSocket.bind((peer['ip'], peer['port']))
    print("running lookup on %s:%s" % (peer['ip'], peer['port']))
    while True:
        request = lookupSocket.recvfrom(1024) # wait for request
        message = json.loads(request[0])
        returnAddress = request[1]

        if (message['type'] == 'join'):
            newNeighbor = message['peer']
            neighbors.append(newNeighbor)
            lookupSocket.sendto(str.encode(peer['name']), returnAddress)
            print("%s: Accepting %s %s:%s" % 
                (peer['name'], newNeighbor['name'], newNeighbor['ip'], newNeighbor['port']))

        #if (message['type'] == 'disconnection'):


##########################################################################
def transfer():
    print("")

##########################################################################
def ui():
    options = {'s': status, 'f': find, 'g': get}
    choice = '' 
    while (choice != 'q'):
        choice = input(prompt)
        if (list(options.keys()).count(choice) == 1):# if valid choice
            options[choice]()
    quit()

def status():
    print("Peers:")
    for neighbor in neighbors:
        print("\t%s %s:%s" % (neighbor['name'], neighbor['ip'], neighbor['port']))
    files = listdir(getcwd() + peer['path'])# update files
    print("Files: %s" % peer['path'])
    for file in files:
        print("\t%s" % file)
    #for file in files:
    #print("\t%s" % "filename")

def find():
    print("find")

def get():
    print("get")

def quit():
    print("Notifying %s of departure" % peer['name'])
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