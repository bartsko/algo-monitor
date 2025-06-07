from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Pozwalamy na połączenia z dowolnej domeny (ważne dla frontendów na Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Algorand - Algonode
ALGOD_API = "https://mainnet-api.algonode.cloud/v2"
INDEXER_API = "https://mainnet-idx.algonode.cloud/v2"
REWARD_SENDER = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"

@app.get("/")
def root():
    return {"message": "Algorand Node Monitor API is running"}

@app.get("/node-status/{address}")
def get_node_status(address: str):
    response = requests.get(f"{ALGOD_API}/accounts/{address}")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Nie znaleziono konta")
    
    data = response.json()
    return {
        "address": data["address"],
        "amount": data["amount"],
        "status": data.get("status", "Offline"),
        "pending-rewards": data.get("pending-rewards", 0)
    }

@app.get("/last-round")
def get_last_round_time():
    response = requests.get(f"{ALGOD_API}/status")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Nie można pobrać danych o ostatnim bloku")
    
    data = response.json()
    return {
        "time-since-last-round": data.get("time-since-last-round")
    }

@app.get("/rewards/{address}")
def get_rewards(address: str):
    params = {
        "tx-type": "pay",
        "address-role": "receiver",
        "limit": 1000
    }
    response = requests.get(f"{INDEXER_API}/accounts/{address}/transactions", params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Nie można pobrać historii transakcji")
    
    data = response.json()
    rewards = []
    for tx in data.get("transactions", []):
        if tx.get("sender") == REWARD_SENDER:
            rewards.append({
                "date": tx["round-time"],
                "amount": tx["amount"]
            })
    return rewards
