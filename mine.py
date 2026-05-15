import requests
import time
import re
import os
import google.generativeai as genai

# ================== CONFIGURATION ==================
WALLET = os.getenv("WALLET")
AGENT = "<0309L>"
API_KEY = os.getenv("API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_URL = "https://bqrapnlqqtjedjyhlfci.supabase.co/functions/v1/submit-solution"

HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Setup Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

def canonicalize_answer(raw_answer):
    return re.sub(r'\s+', ' ', str(raw_answer).strip().lower())

def solve_puzzle(prompt):
    print(f"\n[INCOMING PUZZLE]")
    print(f"Prompt: {prompt[:400]}..." if len(prompt) > 400 else prompt)
    
    try:
        response = model.generate_content(
            f"{prompt}\n\nJawab hanya dengan jawaban yang paling tepat, singkat, dan langsung. Jangan tambah penjelasan apapun."
        )
        raw_answer = response.text.strip()
        answer = canonicalize_answer(raw_answer)
        print(f"[→] Jawaban Gemini: {answer}")
        return answer
    except Exception as e:
        print(f"[!] Gemini Error: {e}")
        return canonicalize_answer(input("\nManual fallback > "))

def mine():
    print(f"Booting agent {AGENT}...")
    print(f"Target Wallet: {WALLET}")
    print("Initiating $NOCOIN mining loop with Gemini...")
    print("-" * 60)

    while True:
        try:
            res = requests.get(f"{BASE_URL}?eth={WALLET}", headers=HEADERS, timeout=30)

            if res.status_code == 429:
                print("[!] Rate limit (Pull). Sleeping 8s...")
                time.sleep(8)
                continue

            res.raise_for_status()
            data = res.json()
            puzzle = data.get("puzzle")

            if not puzzle:
                print("[*] Puzzle pool habis. Idling 30 detik...")
                time.sleep(30)
                continue

            puzzle_id = puzzle["id"]
            prompt = puzzle["prompt"]

            answer = solve_puzzle(prompt)

            payload = {
                "eth_address": WALLET,
                "agent_name": AGENT,
                "puzzle_id": puzzle_id,
                "answer": answer
            }

            print(f"[*] Submitting puzzle {puzzle_id}...")
            post_res = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=30)

            if post_res.status_code == 429:
                print("[!] Rate limit (Submit). Sleeping 8s...")
                time.sleep(8)
                continue

            post_res.raise_for_status()
            result = post_res.json()

            if result.get("correct"):
                print(f"[+] BERHASIL! +{result.get('reward', 500)} $NTC")
                print(f"[+] Balance: {result.get('balance')}")
            else:
                print(f"[-] Salah.")

            time.sleep(1.8)

        except Exception as e:
            print(f"[!] Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    if not all([WALLET, API_KEY, GEMINI_API_KEY]):
        print("❌ Environment variables belum diisi!")
    else:
        mine()