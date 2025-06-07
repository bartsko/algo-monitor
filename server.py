from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALGOD_API_URL = "https://mainnet-api.algonode.cloud/v2"
INDEXER_API_URL = "https://mainnet-idx.algonode.cloud/v2"
REWARDS_SENDER = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"

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
        f"&limit=1000"   # Pobieramy więcej transakcji, nie tylko ostatnie 50
    )
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Nie można pobrać danych nagród")

    data = response.json()
    transactions = data.get("transactions", [])

    # Filtrowanie transakcji - nagrody od stałego adresu
    rewards = []
    for tx in transactions:
        payment = tx.get("payment-transaction", {})
        sender = tx.get("sender")
        receiver = payment.get("receiver")
        amount = payment.get("amount", 0)

        if sender == REWARDS_SENDER and receiver == account:
            timestamp = tx.get("round-time", 0)
            if timestamp:
                dt = datetime.utcfromtimestamp(timestamp).strftime('%d.%m.%Y, %H:%M:%S')
                algo_amount = amount / 1_000_000  # Zamiana microAlgo -> ALGO
                rewards.append({"date": dt, "amount": round(algo_amount, 6)})

    # Sortuj malejąco po dacie
    rewards.sort(key=lambda x: x["date"], reverse=True)

    return {"rewards": rewards}
