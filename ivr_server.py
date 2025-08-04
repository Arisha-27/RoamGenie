import streamlit as st
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from twilio.rest import Client
import uvicorn
import logging


ivr_app = FastAPI()

BASE_URL = "https://1fd0a36a56f7.ngrok-free.app"  # Replace with your current ngrok URL

# Twilio setup
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_NUMBER = "+14439988287"
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


class CallRequest(BaseModel):
    to_number: str

@ivr_app.post("/start-call")
def start_call(req: CallRequest):
    try:
        call = client.calls.create(
            url=f"{BASE_URL}/ivr-language",
            to=req.to_number,
            from_=TWILIO_NUMBER
        )
        return {"success": True, "sid": call.sid}
    except Exception as e:
        logging.exception("Twilio call initiation failed")
        raise HTTPException(status_code=500, detail=f"Call error: {str(e)}")


# STEP 1: Language selection
@ivr_app.post("/ivr-language")
async def language_select(request: Request):
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather action="{BASE_URL}/ivr-menu" method="POST" timeout="5" numDigits="1">
        <Say language="en-IN">Press 1 for English. Press 2 for Hindi.</Say>
    </Gather>
    <Redirect>{BASE_URL}/ivr-language</Redirect>
</Response>"""
    return Response(content=xml, media_type="application/xml")

# STEP 2: Language-based menu
@ivr_app.post("/ivr-menu")
async def ivr_menu(request: Request):
    form = await request.form()
    lang_digit = form.get("Digits", "")

    if lang_digit == "1":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather action="{BASE_URL}/ivr-english-options" method="POST" timeout="5" numDigits="1">
        <Say language="en-IN">Press 1 for booking. Press 2 for refund. Press 3 to escalate.</Say>
    </Gather>
    <Redirect>{BASE_URL}/ivr-menu</Redirect>
</Response>"""

    elif lang_digit == "2":
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather action="{BASE_URL}/ivr-hindi-options" method="POST" timeout="5" numDigits="1">
        <Say language="hi-IN">बुकिंग के लिए 1 दबाएं। रिफंड के लिए 2 दबाएं। शिकायत के लिए 3 दबाएं।</Say>
    </Gather>
    <Redirect>{BASE_URL}/ivr-menu</Redirect>
</Response>"""

    else:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="en-IN">Invalid input. Please try again.</Say>
    <Redirect>{BASE_URL}/ivr-language</Redirect>
</Response>"""

    return Response(content=xml, media_type="application/xml")

# STEP 3: English options
@ivr_app.post("/ivr-english-options")
async def english_menu(request: Request):
    form = await request.form()
    digit = form.get("Digits", "")
    
    messages = {
        "1": "Your booking is confirmed. Thank you for choosing our travel agency.",
        "2": "Your refund request is being processed. You will receive an email confirmation shortly.",
        "3": "Please hold while we connect you to our escalation team."
    }
    
    msg = messages.get(digit, "Invalid input. Please try again.")
    
    if digit in messages:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="en-IN">{msg}</Say>
    <Pause length="1"/>
    <Say language="en-IN">Thank you for calling. Goodbye.</Say>
    <Hangup/>
</Response>"""
    else:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="en-IN">{msg}</Say>
    <Redirect>{BASE_URL}/ivr-menu</Redirect>
</Response>"""
    
    return Response(content=xml, media_type="application/xml")

# STEP 4: Hindi options
@ivr_app.post("/ivr-hindi-options")
async def hindi_menu(request: Request):
    form = await request.form()
    digit = form.get("Digits", "")
    
    messages = {
        "1": "आपकी बुकिंग पुष्टि हो गई है। हमारी ट्रैवल एजेंसी चुनने के लिए धन्यवाद।",
        "2": "आपका रिफंड अनुरोध प्रक्रिया में है। आपको जल्द ही ईमेल कन्फर्मेशन मिलेगा।",
        "3": "कृपया प्रतीक्षा करें जब तक हम आपको हमारी शिकायत टीम से जोड़ते हैं।"
    }
    
    msg = messages.get(digit, "अमान्य विकल्प। कृपया फिर से कोशिश करें।")
    
    if digit in messages:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">{msg}</Say>
    <Pause length="1"/>
    <Say language="hi-IN">कॉल करने के लिए धन्यवाद। अलविदा।</Say>
    <Hangup/>
</Response>"""
    else:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">{msg}</Say>
    <Redirect>{BASE_URL}/ivr-menu</Redirect>
</Response>"""
    
    return Response(content=xml, media_type="application/xml")

# Health check endpoint
@ivr_app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Travel Agent IVR"}

# Root endpoint for testing
@ivr_app.get("/")
async def root():
    return {"message": "Travel Agent IVR Service is running"}

# Server runner
if __name__ == "__main__":
    uvicorn.run("ivr_server:ivr_app", host="0.0.0.0", port=8010, reload=True)
