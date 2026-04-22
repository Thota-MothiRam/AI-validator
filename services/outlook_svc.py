import requests
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import Config
from logger_config import setup_logging

trace = setup_logging("lead_system")


def get_access_token():
    token_url = f"https://login.microsoftonline.com/{Config.TENANT_ID}/oauth2/v2.0/token"

    token_data = {
        "client_id": Config.CLIENT_ID,
        "client_secret": Config.CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials"
    }

    response = requests.post(token_url, data=token_data)
    token_json = response.json()

    return token_json.get("access_token")


def send_summary_email(to_address, leads_list, status):

    msg = MIMEMultipart()
    msg["From"] = Config.SMTP_USER
    msg["To"] = to_address
    msg["Subject"] = f"Automated Lead Summary: {status} Batch ({len(leads_list)})"

    bg_color = "#28a745" if status == "Legit" else "#dc3545"

    rows_html = ""
    for lead in leads_list:
        rows_html += f"""
        <tr>
            <td style="border:1px solid #ddd; padding:8px;">{lead.get('name', 'N/A')}</td>
            <td style="border:1px solid #ddd; padding:8px;">{lead.get('company', 'N/A')}</td>
            <td style="border:1px solid #ddd; padding:8px;">{lead.get('email', 'N/A')}</td>
            <td style="border:1px solid #ddd; padding:8px;">{lead.get('phone', 'N/A')}</td>
            <td style="border:1px solid #ddd; padding:8px; font-weight:bold; color:{bg_color};">{status}</td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color:{bg_color};">{status} Leads Processed</h2>
        <p>The following batch has been analyzed by the AI system:</p>
        <table style="border-collapse:collapse; width:100%; text-align:left;">
            <tr style="background-color:#f2f2f2;">
                <th style="border:1px solid #ddd; padding:8px;">Name</th>
                <th style="border:1px solid #ddd; padding:8px;">Company</th>
                <th style="border:1px solid #ddd; padding:8px;">Email</th>
                <th style="border:1px solid #ddd; padding:8px;">Phone</th>
                <th style="border:1px solid #ddd; padding:8px;">AI Fraud Status</th>
            </tr>
            {rows_html}
        </table>
        <br>
        <p style="color:#666; font-size:12px;">Processed by: Mary (AI Assistant)</p>
    </body>
    </html>
    """

    try:
        trace.info("[TRACE: EMAIL SVC] -> Getting Graph access token...")

        access_token = get_access_token()

        if not access_token:
            trace.error("Failed to get Graph API access token.")
            return False

        send_url = f"https://graph.microsoft.com/v1.0/users/{Config.SMTP_USER}/sendMail"

        email_data = {
            "message": {
                "subject": msg["Subject"],
                "body": {
                    "contentType": "HTML",
                    "content": html_content
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_address
                        }
                    }
                ]
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(send_url, headers=headers, data=json.dumps(email_data))

        if response.status_code == 202:
            trace.info(f"[TRACE: EMAIL SUCCESS] -> Sent to {to_address}")
            return True
        else:
            trace.error(f"[TRACE: EMAIL ERROR] -> {response.text}")
            return False

    except Exception as e:
        trace.error(f"[TRACE: EMAIL ERROR] for {to_address} -> {str(e)}")
        return False
    
    