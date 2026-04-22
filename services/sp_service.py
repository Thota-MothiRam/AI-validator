from sqlalchemy import text
from database import db
from logger_config import setup_logging
import datetime
import decimal
import time


trace = setup_logging("sp_service")


# =========================================================
# Universal Serializer (Safe for JSON + GPT)
# =========================================================
def serialize_value(value):
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()

    if isinstance(value, decimal.Decimal):
        return float(value)

    return value


# =========================================================
# STORED PROCEDURE: AI_GetAllLeadDetails
# =========================================================
def get_full_lead_details(lead_id):
    trace.info(f"[AI_GetAllLeadDetails] Start - Lead ID: {lead_id}")
    start_time = time.time()

    connection = None
    cursor = None

    try:
        connection = db.engine.raw_connection()
        cursor = connection.cursor()

        cursor.execute("EXEC AI_GetAllLeadDetails ?", (lead_id,))
        trace.info("Stored procedure executed successfully.")

        result_sets = []

        while True:
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            trace.info(f"Fetched {len(rows)} rows from current result set.")

            result_sets.append([
                {
                    columns[i]: serialize_value(row[i])
                    for i in range(len(columns))
                }
                for row in rows
            ])

            if not cursor.nextset():
                break

        execution_time = round(time.time() - start_time, 2)
        trace.info(f"[AI_GetAllLeadDetails] Total result sets: {len(result_sets)}")
        trace.info(f"[AI_GetAllLeadDetails] Execution Time: {execution_time}s")

        return {
            "fire_departments": result_sets[0] if len(result_sets) > 0 else [],
            "account_details": result_sets[1] if len(result_sets) > 1 else [],
            "linkedin_companies": result_sets[2] if len(result_sets) > 2 else [],
            "linkedin_details": result_sets[3] if len(result_sets) > 3 else [],
            "linkedin_education": result_sets[4] if len(result_sets) > 4 else [],
            "linkedin_experiences": result_sets[5] if len(result_sets) > 5 else [],
            "linkedin_languages": result_sets[6] if len(result_sets) > 6 else [],
            "llm_company_info": result_sets[7] if len(result_sets) > 7 else [],
            "fire_contracts": result_sets[8] if len(result_sets) > 8 else [],
            "grant_details": result_sets[9] if len(result_sets) > 9 else [],
            "company_safety": result_sets[10] if len(result_sets) > 10 else [],
            "safety_source_ai": result_sets[11] if len(result_sets) > 11 else [],
            "lead_analysis": result_sets[12] if len(result_sets) > 12 else [],
            "usfa_fire_dept": result_sets[13] if len(result_sets) > 13 else [],
            "historical_data": result_sets[14] if len(result_sets) > 14 else [],
            "web_form": result_sets[15] if len(result_sets) > 15 else [],
            "fouts_notes": result_sets[16] if len(result_sets) > 16 else [],
        }

    except Exception as e:
        trace.error(f"[AI_GetAllLeadDetails] ERROR for Lead ID {lead_id}: {str(e)}")
        return {}

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

        trace.info(f"[AI_GetAllLeadDetails] End - Lead ID: {lead_id}")


# =========================================================
# STORED PROCEDURE: AI_GetSalesPivotByState
# =========================================================
def get_state_sales_data(state):
    trace.info(f"[AI_GetSalesPivotByState] Start - State: {state}")
    start_time = time.time()

    if not state:
        trace.warning("State is missing. Returning empty sales data.")
        return []

    try:
        result = db.session.execute(
            text("EXEC AI_GetSalesPivotByState :state"),
            {"state": state}
        )

        rows = result.fetchall()
        columns = list(result.keys())

        trace.info(f"Fetched {len(rows)} sales rows for state: {state}")

        execution_time = round(time.time() - start_time, 2)
        trace.info(f"[AI_GetSalesPivotByState] Execution Time: {execution_time}s")

        return [
            {
                columns[i]: serialize_value(row[i])
                for i in range(len(columns))
            }
            for row in rows
        ]

    except Exception as e:
        trace.error(f"[AI_GetSalesPivotByState] ERROR for State {state}: {str(e)}")
        return []

    finally:
        trace.info(f"[AI_GetSalesPivotByState] End - State: {state}")
