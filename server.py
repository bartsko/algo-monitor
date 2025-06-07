from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

app = FastAPI()

# Dodanie CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API do Algorand Node
NODE_API_URL = "https://mainnet-api.algonode.cloud/v2/accounts"
STATUS_API_URL = "https://mainnet-api.algonode.cloud/v2/status"

# Algorand Indexer API (do transakcji)
INDEXER_API_URL = "https://mainnet-idx.algonode.cloud/v2"
REWARD_SENDER = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"

@app.get("/")
def home():
    return {"message": "Algorand Node Monitor API is running"}

@app.get("/node-account")
def get_node_account(account: str):
    response = requests.get(f"{NODE_API_URL}/{account}")
    if response.status_code != 200:
        return {"error": "Nie znaleziono konta lub błędna odpowiedź API"}

    data = response.json()

    account_info = {
        "address": data["address"],
        "amount": data["amount"] / 1_000_000,  # Zmienione z microAlgo na Algo
        "pending-rewards": data.get("pending-rewards", 0) / 1_000_000,
        "registered-for-rewards": data.get("registered-for-rewards", False)
    }
    return {"account": account_info}

@app.get("/last-round")
def get_last_round():
    response = requests.get(STATUS_API_URL)
    if response.status_code != 200:
        return {"error": "Nie można pobrać danych o bloku"}

    data = response.json()
    return {"last_round": data["last-round"], "time": int(time.time())}

@app.get("/rewards/{address}")
def get_rewards(address: str):
    response = requests.get(f"{INDEXER_API_URL}/accounts/{address}/transactions?limit=1000")
    if response.status_code != 200:
        return {"error": "Nie można pobrać danych o transakcjach"}

    transactions = response.json().get("transactions", [])
    rewards = []
    for txn in transactions:
        if txn.get("sender") == REWARD_SENDER and txn.get("payment-transaction", {}).get("receiver") == address:
            rewards.append({
                "timestamp": txn.get("round-time"),
                "amount": txn.get("payment-transaction", {}).get("amount", 0) / 1_000_000  # MicroAlgo -> Algo
            })

    return {"rewards": rewards}
