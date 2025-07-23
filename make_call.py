import os
from twilio.rest import Client

# Set your Twilio credentials here (or use env vars)
account_sid = "ACa84b12a3d81d88e62b1d06d29cfd4f18"
auth_token = "6c693db27f21ad86c90aa0e77acca6e4"
client = Client(account_sid, auth_token)

call = client.calls.create(
    url="https://30240a1ce4c2.ngrok-free.app/ivr-language",  # Your FastAPI IVR entry point
    to="+918303321573",       # Replace with your verified Indian number
    from_="+14439988287"     # Replace with your Twilio number
)

print(f"Call initiated, SID: {call.sid}")