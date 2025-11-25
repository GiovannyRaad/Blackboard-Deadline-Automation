from pywa import WhatsApp, types
from pywa.types.templates import *
from dotenv import load_dotenv
import os

def send_reminder(course, task, due_date):
    load_dotenv()
    Wtoken = os.environ.get("TOKEN") #Meta cloudApi token
    pID = os.environ.get("PHONEID") #Meta test number ID
    myPhone = os.environ.get("PHONE")

    #Create whatsApp client
    wa = WhatsApp(
        phone_id=pID,
        token=Wtoken

    )

    wa.send_template(
        to=myPhone,  # recipient number
        name="deadline_reminder",  # template name
        language=TemplateLanguage.ENGLISH_US,
        params=[
            BodyText.params(course, task, due_date)
        ]
    )

