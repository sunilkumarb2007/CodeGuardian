import os
import resend
from dotenv import load_dotenv

load_dotenv(r'd:\CodeGuardian\backend\.env', override=True)
resend.api_key = os.environ.get('RESEND_API_KEY')
alert_email = os.environ.get('ALERT_EMAIL', 'sunilkumarb200703@gmail.com')
sender = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

print(f"Testing Resend API with sender={sender} to={alert_email}...")
try:
    response = resend.Emails.send({
        "from": sender,
        "to": alert_email,
        "subject": "CodeGuardian Email Delivery Verification",
        "html": """
            <div style="font-family: monospace; background: #0b0f11; color: #ffffff; padding: 24px; border-radius: 12px; border: 1px solid #1f2937;">
                <h2 style="color: #c6ff3d; margin-top: 0;">CodeGuardian Production Assurance</h2>
                <p>Resend email delivery is active and verified for CodeGuardian alerts.</p>
                <p style="color: #9ca3af; font-size: 12px;">Recipient: """ + alert_email + """</p>
            </div>
        """
    })
    msg_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", str(response))
    print("SUCCESS: Resend Email Dispatched!")
    print(f"Provider Message ID: {msg_id}")
except Exception as e:
    print(f"Resend Email Error: {e}")
