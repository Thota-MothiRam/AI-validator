

import os
import urllib
from dotenv import load_dotenv

load_dotenv()

class Config:
    # # Use your specific MSSQL details
    DRIVER = "{ODBC Driver 17 for SQL Server}"
    SERVER = "BNGEMPL170\\SQLEXPRESS"
    DATABASE = "db_AileadDemo"
    
    # Building the connection string for Windows Authentication
    params = urllib.parse.quote_plus(
        f"DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes;"
    )
    
    SQLALCHEMY_DATABASE_URI = f"mssql+pyodbc:///?odbc_connect={params}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
   


    GET_ALL_LEADS_URL = os.getenv("GET_ALL_LEADS_URL")
    GET_SINGLE_LEAD_URL = os.getenv("GET_SINGLE_LEAD_URL")

    # Use os.getenv to keep these secret
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Microsoft Graph Config
    TENANT_ID = os.getenv("TENANT_ID")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")

    # SMTP_USER = "Hemanth.AN@empulseit.com"
    SMTP_USER = os.getenv("SMTP_USER")
    SALES_TEAM_EMAIL = os.getenv("SALES_TEAM_EMAIL")
    DEALER_EMAIL = os.getenv("DEALER_EMAIL")



