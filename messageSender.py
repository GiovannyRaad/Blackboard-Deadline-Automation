from pywa import WhatsApp, types
from pywa.types.templates import *

def send_reminder(Wtoken, pID, myPhone, course, task, due_date):

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

