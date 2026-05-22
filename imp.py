import pandas as pd
from pymongo import MongoClient
from datetime import datetime

#Σύνδεση με βάση
client = MongoClient("mongodb://localhost:27017/")
db = client["wsn_database"]
collection = db["sensor_data"]

csv_filename = "wsn_database.sensor_data.csv" 

def bulk_import():
    try:
        print(f"Ανάγνωση του αρχείου {csv_filename}...")
        
        df = pd.read_csv(csv_filename)
        #Μεταφορά όλων των πεδίων
        df.columns = ['_id', 'timestamp', 'node_id', 'sample_num', 'temp_raw', 'hum_raw', 'temperature_c', 'humidity_pct']
        
        documents = []
        for index, row in df.iterrows():
            ts_string = str(row['timestamp']).strip()
            try:
                ts_string = ts_string.replace('Z', '')
                timestamp_obj = datetime.strptime(ts_string, "%Y-%m-%dT%H:%M:%S.%f")
            except ValueError:
                try:
                    timestamp_obj = datetime.strptime(ts_string, "%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    timestamp_obj = datetime.now()

            doc = {
                
                "original_id": str(row['_id']).strip(),
                "timestamp": timestamp_obj,
                "mote_id": int(row['node_id']), 
                "sample_num": int(row['sample_num']),
                "temp_raw": int(row['temp_raw']),
                "hum_raw": int(row['hum_raw']),
                "temperature_c": float(row['temperature_c']),
                "humidity_pct": float(row['humidity_pct'])
            }
            documents.append(doc)
        
        if documents:
            collection.delete_many({}) 
            
            result = collection.insert_many(documents)
            print(f"Επιτυχής εισαγωγή! Αποθηκεύτηκαν {len(result.inserted_ids)} εγγραφές στη MongoDB.")
        else:
            print("Δεν βρέθηκαν δεδομένα για εισαγωγή.")

    except Exception as e:
        print(f"Προέκυψε σφάλμα κατά την εισαγωγή: {e}")

if __name__ == "__main__":
    bulk_import()