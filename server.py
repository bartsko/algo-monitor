from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests

app = FastAPI()

# Dodajemy CORS, aby frontend mógł łączyć się z backendem
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NODE_API_URL = "https://mainnet-api.algonode.cloud/v2/accounts"
STATUS_API_URL = "https://mainnet-api.algonode.cloud/v2/status"

# Trasa główna dla testów (zapobiegnie 404 Not Found)
@app.get("/")
def home():
    return {"message": "Algorand Node Monitor API is running"}

# Pobieranie danych o koncie
@app.get("/node-account")
def get_node_account(account: str):
    response = requests.get(f"{NODE_API_URL}/{account}")

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Nie znaleziono konta lub błędna odpowiedź API")

    data = response.json()

    account_info = {
        "address": data["address"],
        "amount": data["amount"],
        "status": data.get("status", "Offline"),
        "vote-participation": "Tak" if "vote-participation-key" in data.get("participation", {}) else "Nie"
    }

    return {"account": account_info}

# Pobieranie ostatniego bloku
@app.get("/last-round")
def get_last_round():
    response = requests.get(STATUS_API_URL)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Nie można pobrać danych o bloku")

    data = response.json()
    return {"last_round": data["last-round"]}

# Uruchamianie serwera na Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
