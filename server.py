from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime

app = FastAPI()

# CORS — pozwalamy na dostęp z frontendu
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALGOD_API_URL = "https://mainnet-api.algonode.cloud/v2"
INDEXER_API_URL = "https://mainnet-idx.algonode.cloud/v2"
REWARDS_SENDER = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"  # Stały adres nagród

@app.get("/")
def root():
    return {"message": "Algorand Node Monitor API is running"}

@app.get("/node-info")
def get_node_info(account: str):
    response = requests.get(f"{ALGOD_API_URL}/accounts/{account}")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Nie znaleziono konta lub błędna odpowiedź API")

    data = response.json()

    account_info = {
        "status": "Online" if data.get("account", {}).get("status") == "Online" else "Offline",
        "amount": data.get("account", {}).get("amount", 0) / 1_000_000,
        "pending_rewards": data.get("account", {}).get("pending-rewards", 0) / 1_000_000
    }

    return account_info

@app.get("/rewards-calendar")
def get_rewards_calendar(account: str):
    url = (
        f"{INDEXER_API_URL}/accounts/{account}/transactions"
        f"?tx-type=pay"
        f"&sender={REWARDS_SENDER}"
        f"&limit=50"
    )
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Nie można pobrać danych nagród")

    data = response.json()
    transactions = data.get("transactions", [])

    rewards = []
    for tx in transactions:
        amount = tx.get("payment-transaction", {}).get("amount", 0) / 1_000_000
        timestamp = tx.get("round-time", 0)
        if timestamp:
            dt = datetime.utcfromtimestamp(timestamp).strftime('%d.%m.%Y, %H:%M:%S')
            rewards.append({"date": dt, "amount": amount})

    # Sortuj malejąco po dacie
    rewards.sort(key=lambda x: x["date"], reverse=True)

    return {"rewards": rewards}
