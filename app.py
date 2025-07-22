from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
import requests
import logging
import google.generativeai as genai

# === Load environment variables ===
load_dotenv()

# Slack credentials
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Mantis credentials
MANTIS_URL = os.getenv("MANTIS_URL")  # e.g., http://localhost/mantis/api/rest/
MANTIS_API_TOKEN = os.getenv("MANTIS_API_TOKEN")
MANTIS_PROJECT_ID = os.getenv("MANTIS_PROJECT_ID")

# === Logging Configuration ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === Validate environment variables ===
required_envs = [
    ("SLACK_BOT_TOKEN", SLACK_BOT_TOKEN),
    ("SLACK_APP_TOKEN", SLACK_APP_TOKEN),
    ("GEMINI_API_KEY", GEMINI_API_KEY),
    ("MANTIS_URL", MANTIS_URL),
    ("MANTIS_API_TOKEN", MANTIS_API_TOKEN),
    ("MANTIS_PROJECT_ID", MANTIS_PROJECT_ID),
]

for name, val in required_envs:
    if not val:
        logging.error(f"Missing environment variable: {name}")
        raise Exception(f"Missing environment variable: {name}")

# === Configure Gemini ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# === Initialize Slack bot ===
app = App(token=SLACK_BOT_TOKEN)


# === MantisBT ticket creation function ===
def create_mantis_ticket(summary, description):
    url = f"{MANTIS_URL.rstrip('/')}/issues/"
    headers = {
        "Authorization": MANTIS_API_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
    "summary": summary,
    "description": description,
    "project": {"id": int(MANTIS_PROJECT_ID)},
    "category": "General"  # Make sure this matches an existing category in your Mantis project
    }


    try:
        logging.info(f"Creating Mantis ticket with summary: {summary}")
        response = requests.post(url, headers=headers, json=data)

        # Check for HTTP errors
        if response.status_code != 201:
            logging.error(f"Failed to create ticket. Status: {response.status_code}, Response: {response.text}")
            return None

        result = response.json()
        logging.info(f"Ticket successfully created: {result}")
        return result
    except Exception as e:
        logging.exception("Exception while creating Mantis ticket")
        return None


# === Slack message event handler ===
@app.event("message")
def handle_message_events(event, say):
    text = event.get("text", "")
    user = event.get("user")
    bot_id = event.get("bot_id")

    if bot_id is not None:
        return  # Ignore messages from other bots

    logging.info(f"Received message from user {user}: {text}")

    if "create ticket" in text.lower():
        summary = "Support Request from Slack"
        description = f"User ID: {user}\n\nIssue: {text}"
        ticket = create_mantis_ticket(summary, description)

        if ticket and "issue" in ticket:
            ticket_id = ticket["issue"]["id"]
            say(f"✅ A support ticket has been created in MantisBT! Ticket ID: {ticket_id}")
        else:
            say("⚠️ Sorry, something went wrong while creating the ticket. Please try again later.")
    else:
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
            logging.exception("Gemini API error")

        say(bot_reply)


# === Main entry point ===
if __name__ == "__main__":
    logging.info("Starting Slack bot...")
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
