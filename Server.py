import argparse
from sys import argv
import binascii
import socket
import struct

#SIMILAR TO PROJ 0 WE WILL TAKE IN PORT INFO FROM ARGS
parser = argparse.ArgumentParser(description = """This is a very basic server program""")
parser.add_argument('port', type = int, help = 'This is the port to connect to the server on', action = 'store')
args = parser.parse_args(argv[1:])

#1. WE CONNECT TO OUR CLIENT SOCKET
host = ''
port = args.port
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM ) #NOT UDP HERE
clientSocket.bind((host, port))
clientSocket.listen(1) #WE ARE RUNNING ONLY ONE PROCESS
conn, address = clientSocket.accept()

#2. THIS LOOP SHOULD TAKE IN THE WEBSITE RECEIVED, CONVERT IT TO HEXADECIMAL, REMOVE ANYTHING UNECESSARY, SEND QUERY
#TO GOOGLE AND SEND RESPONSE TO CLIENT
while True:
    #WE CHECK TO MAKE SURE THAT THE INFORMATION WE ARE RECEIVING IS ACTUALLY A
    # STRING AND WHAT WE WANT
    websiteRcvd = conn.recv(512).decode('utf-8')
    if not websiteRcvd:
        break
    #AFTER WE GET THE WEBSITE NAME WE WILL PUT IT IN A LIST PROPERLY TO BE USED IN THE NEXT LOOP
    charList = []
    for l in websiteRcvd:
        charList.append(l)

    queryCompileList = []
    dotPlaceCounter = 0
    ph = 0

    #THIS FUNCTION WILL BE USED TO FORMAT THE COUNT OF QUERY WE WILL BE SENDING TO GOOGLE
    #IT WILL ADD A 0 IF THE NUMBER IS <10
    def countFormatter(dotPlaceCounter, queryCompileList, ph):
        if dotPlaceCounter >= 10:
            return queryCompileList.insert(ph, (str(dotPlaceCounter)))
        else:
            return queryCompileList.insert(ph, ("0" + str(dotPlaceCounter)))

    #THIS LOOP WILL LOOK FOR ANY DOTS THAT WERE SENT IN THE MESSAGE,
    #AND REMOVE THEM FROM THE QUERY TO BE SENT TO GOOGLE
    for char in charList:
                #converting every character to ascii then to hex, then removing the 0x
                hexTranslation = hex(ord(char))[2:]
                queryCompileList.append(hexTranslation)
                temp = (ph+2)
                #IF/ELSE STATEMENT TO SEPERATE THE '.' FROM THE REST OF THE LETTERS
                #SHOULD UTILIZE THE COUNTFORMATTER FUNCITON
                if hexTranslation != "2e": #hex value of the dot is 2e
                    dotPlaceCounter = dotPlaceCounter + 1
                elif hexTranslation == "2e":
                    countFormatter(dotPlaceCounter, queryCompileList, ph)
                    dotPlaceCounter = 0
                    ph = queryCompileList.index("2e", (temp))
    if dotPlaceCounter > 0:
            countFormatter(dotPlaceCounter, queryCompileList, ph)
            dotPlaceCounter = 0
    while "2e" in queryCompileList: #remove the 2e and insert the count
        queryCompileList.remove("2e")


    queryBody = ' '.join(queryCompileList) # making the string list into a string

 #SEND THE HEXADECIMAL BODY STRING CREATED TO GOOGLE USING CODE FROM BLOG
 #WE KEEP THE HEADER AND FOOTER FROM THE BLOG AND INSERT THE BODY WE CREATED FROM
 #INFO RECEIVED FROM CLIENT
    def send_udp_message(message, address, port):
        message = message.replace(" ", "").replace("\n", "")
        server_address = (address, port)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(binascii.unhexlify(message), server_address)
            websiteRcvd, _ = sock.recvfrom(4096)
        finally:
            sock.close()
        return binascii.hexlify(websiteRcvd).decode("utf-8")

    header = "AA AA 01 00 00 01 00 00 00 00 00 00 " #same for every domain
    tail = "00 00 01 00 01" #same for every domain
    message = header + queryBody +  tail

    response = send_udp_message(message, "8.8.8.8", 53) #sending request to dNS server using port 53

    s = response[-8:] #the last eight characters holds the ip address
    addr_long = int(s, 16)
    struct.pack(">L", addr_long)
    ipAddressToSend = socket.inet_ntoa(struct.pack(">L", addr_long))

    print(ipAddressToSend)
    #check statement to make sure we are sending and actual address^

    conn.send(ipAddressToSend.encode('utf-8')) #sending the ip adresses back

conn.close()
clientSocket.close()
