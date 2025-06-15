import requests
import json
import os
from datetime import datetime, timedelta
from urllib.parse import quote_plus

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL") or "your_discord_webhook_here"
CHARACTERS = [
    "illumine",
    "Kamakadzei",
    "hex good",
    "Jay the pally",
    "zaneon the monk"
]
XP_STORAGE_FILE = "xp_storage.json"
API_URL_TEMPLATE = "https://api.guildstats.eu/v3/characters/{}"

def get_character_xp(character_name):
    try:
        encoded_name = quote_plus(character_name)
        url = API_URL_TEMPLATE.format(encoded_name)
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("experience", 0)
    except Exception as e:
        print(f"Error fetching XP for {character_name}: {e}")
        return None

def load_xp_storage():
    if not os.path.exists(XP_STORAGE_FILE):
        return {}
    with open(XP_STORAGE_FILE, "r") as f:
        return json.load(f)

def save_xp_storage(storage):
    with open(XP_STORAGE_FILE, "w") as f:
        json.dump(storage, f, indent=2)

def send_discord_message(message):
    data = {"content": message}
    response = requests.post(DISCORD_WEBHOOK_URL, json=data)
    if response.status_code == 204:
        print("Discord message sent successfully!")
    else:
        print(f"Failed to send Discord message: {response.status_code} - {response.text}")

def main():
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    storage = load_xp_storage()

    # Fetch current XP for all characters
    today_data = {}
    for char in CHARACTERS:
        xp = get_character_xp(char)
        if xp is not None:
            today_data[char] = xp

    # Save today's XP snapshot
    storage[str(today)] = today_data
    save_xp_storage(storage)

    # Check if we have enough data to calculate yesterday's gain
    if str(yesterday) not in storage or str(day_before_yesterday) not in storage:
        print("Not enough data to calculate yesterday's XP gain.")
        return

    message_lines = [f"**XP gains for {yesterday}:**"]
    yesterday_data = storage[str(yesterday)]
    day_before_data = storage[str(day_before_yesterday)]

    for char in CHARACTERS:
        if char in yesterday_data and char in day_before_data:
            xp_gain = yesterday_data[char] - day_before_data[char]
            if xp_gain < 0:
                xp_gain = 0  # Handle possible resets
            message_lines.append(f"- **{char}** gained **{xp_gain:,} XP**")
        else:
            message_lines.append(f"- No data for {char} on required days.")

    send_discord_message("\n".join(message_lines))

if __name__ == "__main__":
    main()
