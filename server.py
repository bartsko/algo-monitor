from fastapi import FastAPI, HTTPException
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

# API Endpoints
INDEXER_URL = "https://mainnet-idx.algonode.cloud/v2"
ALGOD_URL = "https://mainnet-api.algonode.cloud/v2"

REWARDS_SENDER = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"

@app.get("/")
def home():
    return {"message": "Algorand Node Monitor API is running"}

@app.get("/account-info")
def account_info(address: str):
    # 1. Dane z Algod API
    algod_response = requests.get(f"{ALGOD_URL}/accounts/{address}")
    if algod_response.status_code != 200:
        raise HTTPException(status_code=404, detail="Nie znaleziono konta w Algod API")

    algod_data = algod_response.json()["account"]

    balance = algod_data.get("amount", 0) / 1_000_000  # microAlgos -> Algos
    pending_rewards = algod_data.get("pending-rewards", 0) / 1_000_000

    registered_for_rewards = algod_data.get("participation", {}).get("vote-participation-key") is not None

    # 2. Pobranie ostatniego bloku
    status_response = requests.get(f"{ALGOD_URL}/status")
    if status_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Nie można pobrać statusu sieci")

    status_data = status_response.json()
    last_block_time = status_data.get("time-since-last-round", 0)

    return {
        "balance": balance,
        "pending_rewards": pending_rewards,
        "registered_for_rewards": registered_for_rewards,
        "last_block_time": last_block_time
    }

@app.get("/reward-history")
def reward_history(address: str):
    rewards = []

    next_token = ""
    while True:
        params = {
            "asset-id": 0,
            "address": address,
            "tx-type": "pay",
            "limit": 1000,
            "next": next_token
        }
        url = f"{INDEXER_URL}/accounts/{address}/transactions"
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Nie można pobrać historii transakcji")

        data = response.json()
        transactions = data.get("transactions", [])

        for tx in transactions:
            sender = tx.get("sender", "")
            if sender == REWARDS_SENDER:
                timestamp = tx.get("round-time")
                amount = tx.get("payment-transaction", {}).get("amount", 0) / 1_000_000  # ALGO
                date = datetime.utcfromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M:%S")
                rewards.append({"date": date, "amount": amount})

        # Break if no more pages
        if "next-token" not in data:
            break
        next_token = data["next-token"]

    return {"rewards": rewards}
