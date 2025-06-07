from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALGONODE_API = "https://mainnet-api.algonode.cloud/v2"
MONITORED_ADDRESS = "TWÓJ_ADRES"  # <<< Twój adres Algorand!
REWARD_SENDER = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"

@app.get("/node-status")
def node_status():
    response = requests.get(f"{ALGONODE_API}/accounts/{MONITORED_ADDRESS}")
    data = response.json()
    status = data.get("status", "Offline")
    return {"status": status}

@app.get("/average-transactions")
def average_transactions():
    latest = requests.get(f"{ALGONODE_API}/status").json()["last-round"]
    rounds = list(range(latest - 9, latest + 1))
    transactions = []
    for rnd in rounds:
        blk = requests.get(f"{ALGONODE_API}/blocks/{rnd}").json()
        transactions.append(len(blk.get("txns", [])))
    return {"rounds": rounds, "transactions": transactions}

@app.get("/recent-transactions")
def recent_transactions():
    response = requests.get(f"{ALGONODE_API}/accounts/{MONITORED_ADDRESS}/transactions?limit=10")
    txns = response.json().get("transactions", [])
    formatted = [{"hash": txn["id"], "timestamp": txn["round-time"]} for txn in txns]
    return {"transactions": formatted}

@app.get("/block-timer")
def block_timer():
    status = requests.get(f"{ALGONODE_API}/status").json()
    return {"seconds": status["time-since-last-round"]}

@app.get("/reward-calendar")
def reward_calendar():
    response = requests.get(f"{ALGONODE_API}/accounts/{MONITORED_ADDRESS}/transactions?limit=1000")
    txns = response.json().get("transactions", [])
    reward_days = set()

    for txn in txns:
        if txn.get("sender") == REWARD_SENDER:
            timestamp = txn.get("round-time")
            if timestamp:
                day = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
                reward_days.add(day)

    return {"days": sorted(reward_days)}
