import requests
import json
import os
from dotenv import load_dotenv

# -------------------
# 1. CHARGER .env
# -------------------
load_dotenv()

USERNAME = os.getenv("ADMIN_USERNAME")
PASSWORD = os.getenv("ADMIN_PASSWORD")

if not USERNAME or not PASSWORD:
    print("❌ ADMIN_USERNAME ou ADMIN_PASSWORD manquant dans .env")
    exit()

# -------------------
# 2. CONFIG
# -------------------

BASE_URL = "https://darija-trad.onrender.com"
LOGIN_URL = f"{BASE_URL}/login"
TRANSLATIONS_URL = f"{BASE_URL}/translations"

LANG_CODE_MAP = {
    "dr": "ary_Arab",
    "fr": "fra_Latn",
    "en": "eng_Latn",
}

# -------------------
# 3. LOGIN
# -------------------

login_data = {
    "username": USERNAME,
    "password": PASSWORD
}

response = requests.post(LOGIN_URL, data=login_data)

if response.status_code != 200:
    print(f"❌ Échec de la connexion : {response.status_code} - {response.text}")
    exit()

access_token = response.json().get("access_token")
if not access_token:
    print("❌ Token JWT manquant.")
    exit()

headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "Mozilla/5.0"
}

# -------------------
# 4. EXPORT DES TRADUCTIONS
# -------------------

response = requests.get(TRANSLATIONS_URL, headers=headers)

if response.status_code == 200:
    data = response.json()
    with open("all_translations_dataset.json", "w", encoding="utf-8") as f:
        for item in data:
            src_lang = item.get("source_lang")
            tgt_lang = item.get("target_lang")
            src_text = item.get("source_text")
            tgt_text = item.get("target_text")

            if src_lang in LANG_CODE_MAP and tgt_lang in LANG_CODE_MAP and src_text and tgt_text:
                record = {
                    "translation": {
                        LANG_CODE_MAP[src_lang]: src_text,
                        LANG_CODE_MAP[tgt_lang]: tgt_text
                    }
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print("✅ Export terminé : all_translations_dataset.json")

else:
    print(f"❌ Erreur API : {response.status_code} - {response.text}")
