from dotenv import load_dotenv
import os

load_dotenv()

print("Testing environment variables:")
print(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
print(f"TWILIO_ACCOUNT_SID: {'SET' if os.getenv('TWILIO_ACCOUNT_SID') else 'NOT SET'}")
print(f"TWILIO_AUTH_TOKEN: {'SET' if os.getenv('TWILIO_AUTH_TOKEN') else 'NOT SET'}")
print(f"TWILIO_PHONE_NUMBER: {'SET' if os.getenv('TWILIO_PHONE_NUMBER') else 'NOT SET'}")