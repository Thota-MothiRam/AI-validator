

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Lead(db.Model):
    __tablename__ = "tbl_LeadAnalysis"
    
    id = db.Column("LeadAnalysis_id", db.Integer, primary_key=True)
    first_name = db.Column("first_name", db.String(100))
    last_name = db.Column("last_name", db.String(100))
    email = db.Column("Email", db.String(400))
    phone = db.Column("Phone", db.String(400))
    company = db.Column("CompanyName", db.String(400))
    truck_interest = db.Column("Truck_of_interest", db.String(400))
    
    # Critical mappings for spaces in SQL column names
    ai_status = db.Column("AI_Fraud_Status", db.String(20))
    ai_reason = db.Column("AI_Reason", db.Text) 
    denial_reason = db.Column("Reason_Lead_is_denied", db.Text)
    # approved_by = db.Column("Approved_Denied_by", db.String(255))
    approved_by = db.Column("StatusDoneBy", db.Integer)
    Status = db.Column("Status", db.String(20))
    StatusUpdatedOn = db.Column("StatusUpdatedOn", db.DateTime)



# ================================
# Full Fraud Analysis Table
# ================================
class LeadFraudAnalysis(db.Model):
    __tablename__ = "tbl_LeadFraudAnalysis"

    FraudAnalysis_id = db.Column(db.Integer, primary_key=True)
    LeadAnalysis_id = db.Column(db.Integer, db.ForeignKey("tbl_LeadAnalysis.LeadAnalysis_id"), nullable=False)

    Overall_Decision = db.Column(db.String(20), nullable=False)
    Confidence_Score = db.Column(db.Integer, nullable=False)
    Risk_Level = db.Column(db.String(50))
    # Risk_Description = db.Column(db.String(1000))
    Risk_Description = db.Column(db.Text)
  

    # All field-level columns from your table
    Field_FirstName_Status = db.Column(db.String(50))
    Field_FirstName_Reason = db.Column(db.String(500))
    Field_LastName_Status = db.Column(db.String(50))
    Field_LastName_Reason = db.Column(db.String(500))
    Field_JobTitle_Status = db.Column(db.String(50))
    Field_JobTitle_Reason = db.Column(db.String(500))
    Field_CompanyName_Status = db.Column(db.String(50))
    Field_CompanyName_Reason = db.Column(db.String(500))
    Field_LLMCompanyName_Status = db.Column(db.String(50))
    Field_LLMCompanyName_Reason = db.Column(db.String(500))
    Field_Email_Status = db.Column(db.String(50))
    Field_Email_Reason = db.Column(db.String(500))
    Field_Phone_Status = db.Column(db.String(50))
    Field_Phone_Reason = db.Column(db.String(500))
    Field_ZIP_Status = db.Column(db.String(50))
    Field_ZIP_Reason = db.Column(db.String(500))
    Field_State_Status = db.Column(db.String(50))
    Field_State_Reason = db.Column(db.String(500))
    Field_Address_Status = db.Column(db.String(50))
    Field_Address_Reason = db.Column(db.String(500))
    Field_HistoricalData_Status = db.Column(db.String(50))
    Field_HistoricalData_Reason = db.Column(db.String(500))
    Field_AccountDetails_Status = db.Column(db.String(50))
    Field_AccountDetails_Reason = db.Column(db.String(500))
    AISummary = db.Column(db.Text)
    CreatedByAI = db.Column(db.String(100))

    # Relationship
    lead = db.relationship("Lead", backref="fraud_analyses")


