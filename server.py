from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoints
ALGOD_API_URL = "https://mainnet-api.algonode.cloud/v2/accounts"
INDEXER_API_URL = "https://mainnet-idx.algonode.cloud/v2/transactions"

@app.get("/")
def home():
    return {"message": "Algorand Node Monitor API is running"}

@app.get("/account-info")
def get_account_info(address: str):
    response = requests.get(f"{ALGOD_API_URL}/{address}")
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Błąd pobierania danych konta")

    data = response.json()
    
    # BEZPIECZNE ODCZYTANIE DANYCH
    account_data = data.get("account", data)

    balance = account_data.get("amount", 0) / 1_000_000
    pending_rewards = account_data.get("pending-rewards", 0) / 1_000_000
    participation = account_data.get("participation", {})
    
    is_participating = "Tak" if participation else "Nie"

    return {
        "balance": balance,
        "pending_rewards": pending_rewards,
        "participating": is_participating
    }

@app.get("/reward-history")
def get_rewards_history(address: str):
    params = {
        "tx-type": "pay",
        "receiver": address,
        "sender": "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA",  # nagrody
        "limit": 30
    }
    response = requests.get(INDEXER_API_URL, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Błąd pobierania historii nagród")

    txns = response.json().get("transactions", [])
    rewards = []
    for txn in txns:
        timestamp = txn.get("round-time")
        amount = txn.get("payment-transaction", {}).get("amount", 0) / 1_000_000
        rewards.append({"timestamp": timestamp, "amount": amount})

    return {"rewards": rewards}
