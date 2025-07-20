from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
import re
import google.generativeai as genai

# Load env variables
load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

print("Bot Token Loaded:", bool(SLACK_BOT_TOKEN))
print("App Token Loaded:", bool(SLACK_APP_TOKEN))
print("Gemini API Key Loaded:", bool(GEMINI_API_KEY))

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Slack bot
app = App(token=SLACK_BOT_TOKEN)

# Respond to ALL messages (excluding bot's own messages)
@app.event("message")
def handle_message_events(event, say):
    text = event.get("text")
    user = event.get("user")
    bot_id = event.get("bot_id")

    if bot_id is not None:
        return  # Skip messages sent by any bot (including this one)

    print(f"Received message from user {user}: {text}")

    prompt = f"""
    You are a support assistant for washing machine issues.

    User said: "{text}"

    Give a helpful, clear response. Do NOT use any markdown like *bold, *italic, or bullet points. Just plain, readable text.

    If the issue can’t be resolved easily, ask the user if they’d like to create a support ticket.
    """


    try:
        response = model.generate_content([prompt])
        bot_reply = response.text
    except Exception as e:
        bot_reply = "Sorry, there was an issue generating a response. Please try again later."
        print(f"Error from Gemini: {e}")

    say(bot_reply)

if _name_ == "_main_":
    print("Starting Slack bot...")
    SocketModeHandler(app, SLACK_APP_TOKEN).start()


for m in genai.list_models():
    print(m.name, m.supported_generation_methods)
