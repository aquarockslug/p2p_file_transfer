import sys
import threading
from socket import *

prompt = """Your options:\n1. [s]tatus\n2. [f]ind <filename>
3. [g]et <filename> <peer IP> <peer port>\n4. [q]uit\nYour choice: """

args = sys.argv[1:]
if (len(args) != 4 and len(args) != 6): 
    print("incorrect number of arguments, must be 4 or 6")
    sys.exit(0)

neighbors = []

peer = {
    'name': args[0],
    'ip': args[1],
    'port': int(args[2]),
    'path': args[3]
}  
if (len(args) == 6): # join network
    firstNeighbor = {
        'ip': args[4],
        'port': int(args[5])
    }
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.sendto(str.encode("join request"), (firstNeighbor['ip'], firstNeighbor['port']))
    neighbors.append(firstNeighbor)

##########################################################################
# wait for connections
def lookup():
    lookupSocket = socket(AF_INET, SOCK_DGRAM)
    lookupSocket.bind((peer['ip'], peer['port']))
    print("running lookup on %s:%s" % (peer['ip'], peer['port']))
    while True:
        request = lookupSocket.recvfrom(1024) # wait for request
        message = request[0]
        address = request[1]
        # newNeighbor = {
        #     'ip': args[4],
        #     'port': int(args[5])
        # }
        #neighbors.append(newNeighbor)
        print(address)
        print(message)
        # add neighbor

        # sends an acknowledgment on the ephemeral port that request was sent from
        #lookupSocket.sendto("ack", address)

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
        print("\t%s %s:%s", (neighbor['name'], neighbor['ip'], neighbor['port']))
    print("Files: %s", peer['path'])
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