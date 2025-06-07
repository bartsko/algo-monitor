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

# API Endpoints
ALGOD_NODE = "https://mainnet-api.algonode.cloud"
INDEXER_NODE = "https://mainnet-idx.algonode.cloud"
REWARDS_ADDRESS = "Y76M3MSY6DKBRHBL7C3NNDXGS5IIMQVQVUAB6MP4XEMMGVF2QWNPL226CA"

@app.get("/")
async def root():
    return {"message": "Algorand Node Monitor API is running"}

@app.get("/account/{address}")
async def get_account(address: str):
    url = f"{ALGOD_NODE}/v2/accounts/{address}"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Account not found")
    data = response.json()

    balance = data["amount"] / 1e6
    pending_rewards = data.get("pending-rewards", 0) / 1e6
    status = "Online" if data.get("status") == "Online" else "Offline"

    # Last block + timestamp
    block_url = f"{ALGOD_NODE}/v2/status"
    block_resp = requests.get(block_url)
    block_data = block_resp.json()

    last_round = block_data.get("last-round")
    block_detail_url = f"{ALGOD_NODE}/v2/blocks/{last_round}"
    block_detail_resp = requests.get(block_detail_url)
    block_detail = block_detail_resp.json()

    last_block_time_unix = block_detail.get("timestamp", 0)

    current_time_unix = int(datetime.utcnow().timestamp())
    time_since_last_block = current_time_unix - last_block_time_unix

    return {
        "balance": balance,
        "pending_rewards": pending_rewards,
        "status": status,
        "last_block_time": time_since_last_block
    }

@app.get("/rewards/{address}")
async def get_rewards(address: str):
    url = f"{INDEXER_NODE}/v2/accounts/{address}/transactions?tx-type=pay&asset-id=0&limit=1000"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Transaction history not found")

    txns = response.json().get('transactions', [])
    rewards = []

    for tx in txns:
        sender = tx.get("sender")
        receiver = tx.get("payment-transaction", {}).get("receiver")
        amount = tx.get("payment-transaction", {}).get("amount", 0)

        if sender == REWARDS_ADDRESS and receiver == address:
            timestamp = tx.get("round-time", 0)
            date = datetime.utcfromtimestamp(timestamp).strftime("%d.%m.%Y, %H:%M:%S")
            rewards.append({
                "date": date,
                "amount": amount / 1e6
            })

    rewards = sorted(rewards, key=lambda x: x["date"], reverse=True)
    return rewards
