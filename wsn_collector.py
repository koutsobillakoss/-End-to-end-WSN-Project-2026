import socket
import datetime
import re
from pymongo import MongoClient

# Σύνδεση στη MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["wsn_database"]
collection = db["sensor_data"]

# Σύνδεση στο SerialForwarder του VirtualBox-Ubuntu
HOST = "127.0.0.1" #Localhost
PORT = 9002

def connect_to_sf():
    #Σύνδεση με SerialForwarder
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(b"U ")
    s.recv(2)
    print(f"Συνδέθηκε στο SerialForwarder {HOST}:{PORT}")
    return s

def parse_line(line):
    #Απο pattern παίρνουμε τα δεδομένα σε μορφή Parse: ID:1 SampleNum:0 Temp:6969 Hum:866
    pattern = r"ID:(\d+)\s+SampleNum:(\d+)\s+Temp:(\d+).*?Hum:(\d+)"
    match = re.search(pattern, line)
    if match:
        raw_temp = int(match.group(3))
        raw_hum  = int(match.group(4))
        temp_c   = round(-39.6 + 0.01 * raw_temp, 2)
        hum_pct  = round(-2.0468 + 0.0367 * raw_hum - 1.5955e-6 * raw_hum**2, 2)
        return {
            "timestamp": datetime.datetime.now(),
            "node_id":   int(match.group(1)),
            "sample_num": int(match.group(2)),
            "temp_raw":  raw_temp,
            "hum_raw":   raw_hum,
            "temperature_c": temp_c,
            "humidity_pct":  hum_pct
        }
    return None

def main():
    s = connect_to_sf()
    buffer = ""
    print("Αναμονή δεδομένων...")
    while True:
        data = s.recv(1024).decode("utf-8", errors="ignore")
        buffer += data
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            print(f"Ελήφθη: {line}")
            doc = parse_line(line)
            if doc:
                #Αποθήκευση δεδομένων στην βάση MongoDB
                collection.insert_one(doc)
                print(f"Αποθηκεύτηκε: ID:{doc['node_id']} Temp:{doc['temperature_c']}°C Hum:{doc['humidity_pct']}%")

if __name__ == "__main__":
    main()