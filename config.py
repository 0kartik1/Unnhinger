import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "people_db")
    FULLCONTACT_API_KEY = os.getenv("FULLCONTACT_API_KEY", "")
    DISCOVERY_STALENESS_DAYS = int(os.getenv("DISCOVERY_STALENESS_DAYS", "7"))
    DEBUG = os.getenv("FLASK_ENV", "production") == "development"
