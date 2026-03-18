import socket 
import time

esp32C3 = "172.20.10.7"
END_Port = 5005
RECEIVE_PORT = 5006
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.bind(("", RECEIVE_PORT))
sock.settimeout(1.0)

print("PI IS READY - Sending message AND RECEIVING")

while True:
    message = "HELLO BEEES"
    sock.sendto(message.encode(), (esp32C3, END_Port))
  
    print("Sent", message)
    
    # RECEIVE - now properly indented inside the loop
    try:    
        data, addr = sock.recvfrom(1024)
        print("Receive from esp32C3")
        print(data.decode())
    except socket.timeout:
        print("no reply")
        print("")
    
    time.sleep(5)