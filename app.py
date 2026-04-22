import os
import json
from flask import Flask, jsonify, render_template_string
from flask_apscheduler import APScheduler
from sqlalchemy import or_, and_

from database import db, Lead, LeadFraudAnalysis
from services.validator_svc import analyze_lead
# from services.outlook_svc import send_summary_email
from services.sp_service import get_full_lead_details
from config import Config
from logger_config import setup_logging
from datetime import datetime

trace = setup_logging("lead_system")

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

scheduler = APScheduler()


@app.route('/')
def home():
    return "<h1>Lead System Active</h1><p>Processing leads every 1 minute.</p>"


# =========================================================
# MAIN FRAUD PROCESS
# =========================================================
def execute_main_task():
    trace.info("------ STARTING DB LEAD SCAN ------")

    # unprocessed_leads = Lead.query.filter(
    #     or_(Lead.ai_status == None, Lead.ai_status == 'Pending')
    # ).all()

    unprocessed_leads = Lead.query.filter(
        and_(
            or_(
                Lead.ai_status.is_(None),   # ✅ correct NULL check
                Lead.ai_status == 'Pending'
            ),
            Lead.Status == 'Not Started'
        )
    ).all()

    if not unprocessed_leads:
        trace.info("No new leads to process.")
        return 0

    legit_batch = []
    fraud_batch = []

    for lead in unprocessed_leads:
        try:
            trace.info(f"[SP CALL] Fetching full details for Lead ID: {lead.id}")
            full_context = get_full_lead_details(lead.id)

            if not full_context:
                raise Exception("Stored procedure returned empty data.")

            analysis = analyze_lead(full_context)

        except Exception as e:
            trace.error(f"Fraud analysis failed for Lead {lead.id}: {str(e)}")
            analysis = {
                "overall_decision": "Deny",
                "AISummary": "System processing error",
                "confidence_score": 0,
                "field_analysis": {}
            }

        # ========================
        # Extract AI Analysis
        # ========================
        overall_decision = analysis.get("overall_decision", "Deny")
        confidence = analysis.get("confidence_score", 0)
        AISummary = analysis.get("AISummary", "")
        field_analysis = analysis.get("field_analysis", {})

        # ========================
        # UPSERT Fraud Record
        # ========================
        fraud_record = LeadFraudAnalysis.query.filter_by(
            LeadAnalysis_id=lead.id
        ).first()

        if not fraud_record:
            fraud_record = LeadFraudAnalysis(
                LeadAnalysis_id=lead.id
            )
            db.session.add(fraud_record)

        # Core Fields
        fraud_record.Overall_Decision = overall_decision
        fraud_record.Confidence_Score = confidence
        fraud_record.Risk_Description = analysis.get("Readable_Report")
        fraud_record.AISummary = AISummary
        fraud_record.CreatedByAI = "Mary Agent"

        fraud_record.Risk_Level = analysis.get("Risk_Level")      

        # ========================
        # Field-Level Direct Mapping
        # ========================
        fraud_record.Field_FirstName_Status = field_analysis.get("first_name", {}).get("status")
        fraud_record.Field_FirstName_Reason = field_analysis.get("first_name", {}).get("reason")

        fraud_record.Field_LastName_Status = field_analysis.get("last_name", {}).get("status")
        fraud_record.Field_LastName_Reason = field_analysis.get("last_name", {}).get("reason")

        fraud_record.Field_JobTitle_Status = field_analysis.get("job_title", {}).get("status")
        fraud_record.Field_JobTitle_Reason = field_analysis.get("job_title", {}).get("reason")

        fraud_record.Field_CompanyName_Status = field_analysis.get("company_name", {}).get("status")
        fraud_record.Field_CompanyName_Reason = field_analysis.get("company_name", {}).get("reason")

        fraud_record.Field_LLMCompanyName_Status = field_analysis.get("llm_company_name", {}).get("status")
        fraud_record.Field_LLMCompanyName_Reason = field_analysis.get("llm_company_name", {}).get("reason")

        fraud_record.Field_Email_Status = field_analysis.get("email", {}).get("status")
        fraud_record.Field_Email_Reason = field_analysis.get("email", {}).get("reason")

        fraud_record.Field_Phone_Status = field_analysis.get("phone", {}).get("status")
        fraud_record.Field_Phone_Reason = field_analysis.get("phone", {}).get("reason")

        fraud_record.Field_ZIP_Status = field_analysis.get("zip", {}).get("status")
        fraud_record.Field_ZIP_Reason = field_analysis.get("zip", {}).get("reason")

        fraud_record.Field_State_Status = field_analysis.get("state", {}).get("status")
        fraud_record.Field_State_Reason = field_analysis.get("state", {}).get("reason")

        fraud_record.Field_Address_Status = field_analysis.get("address", {}).get("status")
        fraud_record.Field_Address_Reason = field_analysis.get("address", {}).get("reason")

        fraud_record.Field_HistoricalData_Status = field_analysis.get("historical_data", {}).get("status")
        fraud_record.Field_HistoricalData_Reason = field_analysis.get("historical_data", {}).get("reason")

        fraud_record.Field_AccountDetails_Status = field_analysis.get("account_details", {}).get("status")
        fraud_record.Field_AccountDetails_Reason = field_analysis.get("account_details", {}).get("reason")

        # ========================
        # Update Lead Table
        # ========================
        if overall_decision.lower() == "approve":
            lead.ai_status = "Legit"
            lead.Status = "Approved"
            # lead.approved_by = "Mary Agent"
            lead.approved_by = 11
            # lead.ai_reason = None
            lead.ai_reason = AISummary or json.dumps(field_analysis)
            lead.StatusUpdatedOn = datetime.now()
            legit_batch.append({
                "name": f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "N/A",
                "company": lead.company or "N/A",
                "email": lead.email or "N/A",
                "phone": lead.phone or "N/A"
            })

            trace.info(f"Lead {lead.id} marked as LEGIT")
        else:
            lead.ai_status = "Fraud"
            lead.ai_reason = AISummary or json.dumps(field_analysis)
            lead.StatusUpdatedOn = datetime.now()

            fraud_batch.append({
                "name": f"{lead.first_name or ''} {lead.last_name or ''}".strip() or "N/A",
                "company": lead.company or "N/A",
                "email": lead.email or "N/A",
                "phone": lead.phone or "N/A"
            })

            trace.warning(f"Lead {lead.id} marked as FRAUD")

    # ========================
    # Commit DB
    # ========================
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        trace.error(f"DB commit failed: {str(e)}")
    finally:
        db.session.remove()

    # ========================
    # Send Emails
    # ========================
    # if legit_batch:
    #     send_summary_email(Config.SALES_TEAM_EMAIL, legit_batch, "Legit")
    #     send_summary_email(Config.DEALER_EMAIL, legit_batch, "Legit")

    # if fraud_batch:
    #     send_summary_email(Config.SALES_TEAM_EMAIL, fraud_batch, "Fraud")

    trace.info(f"Processed {len(unprocessed_leads)} leads successfully.")
    return len(unprocessed_leads)


@app.route('/run')
def run_process():
    with app.app_context():
        count = execute_main_task()
    return jsonify({"status": "Success", "leads_processed": count})


@app.route('/dashboard')
def dashboard():
    # recent_leads = Lead.query.order_by(Lead.id.desc()).limit(20).all()
    recent_leads = Lead.query.order_by(Lead.id.desc()).all()

    template = """
    <html>
    <head>
        <title>AI Lead Fraud Dashboard</title>
        <style>
            body { font-family: sans-serif; margin: 40px; background: #f4f7f6; }
            table { width: 100%; border-collapse: collapse; background: white; }
            th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
            th { background-color: #eee; }
            .status-pending { color: #666; font-style: italic; }
            .status-legit, .status-approved { color: green; font-weight: bold; }
            .status-fraud, .status-denied { color: red; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>AI Lead Fraud Dashboard</h2>
        <a href="/run">Force Manual Run</a>
        <br><br>
        <table>
            <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Status</th>
                <th>AI Fraud Status</th>
                <th>Approved_Denied_by</th>
                <th>Reason</th>
            </tr>
            {% for lead in leads %}
            <tr>
                <td>{{ lead.id }}</td>
                <td>{{ lead.email }}</td>
                <td class="status-{{ lead.Status.lower() if lead.Status else 'pending' }}">
                    {{ lead.Status or 'Pending' }}
                </td>
                <td class="status-{{ lead.ai_status.lower() if lead.ai_status else 'pending' }}">
                    {{ lead.ai_status or 'Pending' }}
                </td>
                <td>{{ lead.approved_by or '-' }}</td>
                <td>{{ lead.ai_reason or '-' }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(template, leads=recent_leads)


@scheduler.task('interval', id='process_leads_job', minutes=5)
def scheduled_lead_job():
    with app.app_context():
        execute_main_task()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    scheduler.init_app(app)
    scheduler.start()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
    