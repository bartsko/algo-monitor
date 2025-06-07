from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stałe
ALGONODE_API = "https://mainnet-api.algonode.cloud/v2"
REWARD_SENDER = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"

@app.get("/")
def home():
    return {"message": "Algorand Node Monitor API is running"}

# Sprawdzenie udziału w konsensusie
@app.get("/node-status")
def node_status(address: str = Query(...)):
    response = requests.get(f"{ALGONODE_API}/accounts/{address}")
    data = response.json()
    participation = data.get("account", {}).get("participation", {})
    status = "Online" if "selection-participation-key" in participation else "Offline"
    return {"status": status}

# Średnia liczba transakcji na blok
@app.get("/average-tx")
def average_tx():
    response = requests.get(f"{ALGONODE_API}/blocks?limit=10")
    data = response.json()

    blocks = data.get("blocks", [])
    if not blocks:
        return {"average_tx": 0}

    total_tx = sum(block.get("txns", 0) for block in blocks)
    avg_tx = total_tx / len(blocks)
    return {"average_tx": avg_tx}

# Czas od ostatniego bloku
@app.get("/block-timer")
def block_timer():
    response = requests.get(f"{ALGONODE_API}/status")
    data = response.json()

    time_micro = data.get("time-since-last-round", 0)  # Mikrosekundy
    return {"seconds": time_micro}

# Kalendarz nagród
@app.get("/reward-calendar")
def reward_calendar(address: str = Query(...)):
    response = requests.get(f"{ALGONODE_API}/accounts/{address}/transactions?limit=10000")
    data = response.json()

    transactions = data.get("transactions", [])
    reward_dates = []
    for tx in transactions:
        if tx.get("sender") == REWARD_SENDER:
            timestamp = tx.get("round-time", 0)
            date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
            reward_dates.append(date)
    return {"reward_dates": reward_dates}
