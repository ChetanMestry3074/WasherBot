from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
import requests
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Slack credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Zoho OAuth credentials
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI")
ZOHO_AUTH_CODE = os.getenv("ZOHO_AUTH_CODE")  # One-time code from Zoho

# Print loaded credentials (debug)
print("Slack Bot Token Loaded:", bool(SLACK_BOT_TOKEN))
print("Slack App Token Loaded:", bool(SLACK_APP_TOKEN))
print("Gemini API Key Loaded:", bool(GEMINI_API_KEY))
print("Zoho Client ID Loaded:", bool(ZOHO_CLIENT_ID))

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Slack bot
app = App(token=SLACK_BOT_TOKEN)

# === Function to get Zoho tokens using the auth code ===
def get_zoho_tokens():
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "redirect_uri": ZOHO_REDIRECT_URI,
        "code": ZOHO_AUTH_CODE
    }

    try:
        response = requests.post(url, data=data)
        result = response.json()
        print("Zoho token response:", result)
        return result
    except Exception as e:
        print("Error fetching Zoho tokens:", e)
        return None

# === Slack message event handler ===
@app.event("message")
def handle_message_events(event, say):
    text = event.get("text")
    user = event.get("user")
    bot_id = event.get("bot_id")

    if bot_id is not None:
        return  # Ignore messages from bots

    print(f"Received message from user {user}: {text}")

    prompt = f"""
    You are a support assistant for washing machine issues.

    User said: "{text}"

    Give a helpful, clear response. Do NOT use any markdown like **bold**, *italic*, or bullet points. Just plain, readable text.

    If the issue can’t be resolved easily, ask the user if they’d like to create a support ticket.
    """

    try:
        response = model.generate_content([prompt])
        bot_reply = response.text
    except Exception as e:
        bot_reply = "Sorry, there was an issue generating a response. Please try again later."
        print(f"Error from Gemini: {e}")

    say(bot_reply)

# === Main entry point ===
if __name__ == "__main__":
    print("Starting Slack bot...")

    # Get Zoho tokens once
    zoho_tokens = get_zoho_tokens()
    if zoho_tokens:
        access_token = zoho_tokens.get("access_token")
        refresh_token = zoho_tokens.get("refresh_token")
        print("Access Token:", access_token)
        print("Refresh Token:", refresh_token)

        # Optional: Save these securely to use for ticket creation later

    # Start Slack bot
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
