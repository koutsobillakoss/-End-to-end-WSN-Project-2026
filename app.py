from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
#Σύνδεση στην βάση MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["wsn_database"]
collection = db["sensor_data"]

#Κλήση κώδικα html
@app.route("/")
def index():
    return render_template("index.html")

#Fetch τα δεδομένα για την απεικόνηση στο Dashboard
@app.route("/api/latest")
def get_latest():
    docs = list(collection.find().sort("timestamp", -1).limit(20))
    for d in docs:
        d["_id"] = str(d["_id"])
        d["timestamp"] = d["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(docs)

#Fetch τα δεδομένα για την ανασζήτηση ιστορικών δεδομένων
@app.route("/api/history")
def get_history():
    #Δημιουργία Querry για MongoDB, με εισόδους timestamp
    start = request.args.get("start")
    end = request.args.get("end")
    query = {}
    if start and end:
        query["timestamp"] = {
            "$gte": datetime.strptime(start, "%Y-%m-%dT%H:%M"),
            "$lte": datetime.strptime(end, "%Y-%m-%dT%H:%M")
        }
    docs = list(collection.find(query).sort("timestamp", 1).limit(500))
    for d in docs:
        d["_id"] = str(d["_id"])
        d["timestamp"] = d["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(docs)

if __name__ == "__main__":
    app.run(debug=True, port=5000)