from dotenv import load_dotenv
from datetime import datetime
import os
import sys

# The fetching half lives in the skill folder; the WhatsApp half in its own.
ROOT = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.join(ROOT, "skills", "blackboard-deadlines")
WHATSAPP_DIR = os.path.join(ROOT, "whatsapp")
sys.path.insert(0, SKILL_DIR)
sys.path.insert(0, ROOT)

import headlessEventsFetcher
from whatsapp import messageSender

def convert_iso_to_deadline(iso_time):
    # Parse ISO8601 string into datetime object
    dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))

    return dt.strftime("%B %d, %Y at %H:%M")

if __name__ == "__main__":

    # Each half keeps its own .env next to its code.
    load_dotenv(os.path.join(SKILL_DIR, ".env"))
    load_dotenv(os.path.join(WHATSAPP_DIR, ".env"))

    username = os.environ.get("UNI_USER")
    password = os.environ.get("UNI_PASS")
    tmz = os.environ.get("TIMEZONE")  # e.g., "Asia/Beirut"

    Wtoken = os.environ.get("TOKEN") #Meta cloudApi token
    pID = os.environ.get("PHONEID") #Meta test number ID
    myPhone = os.environ.get("PHONE") #Your phone number with country code
    template_name = os.environ.get("TEMPLATE_NAME") #WhatsApp template name

    event_data = headlessEventsFetcher.run(username, password, tmz)

    for event in event_data.values():
        course = "*" + event.get("course", "No Course") + "*"
        task = "*" + event.get("title", "No Title") + "*"
        due_date =  event.get("endDate", "No End Date")
        due_date = "*" + convert_iso_to_deadline(due_date) + "*"

        messageSender.send_reminder(Wtoken, pID, myPhone, template_name, course, task, due_date)
