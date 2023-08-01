import os, boto3
import sqlalchemy
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


load_dotenv()

VERSION = "0.1.1"

stage = os.getenv("STAGE", "dev")
environment = "prod" if stage == "prod" else "dev"

print(f"AWS_PROFILE: {os.getenv('AWS_PROFILE')}, env={environment}")

ssm = boto3.client("ssm")

db_host = os.getenv("DB_HOST", None)
db_name = os.getenv("DB_NAME", stage)
db_user = os.getenv("DB_USER", None)
db_pass = os.getenv("DB_PASSWORD", None)


if db_host is None or db_user is None or db_pass is None:
    param_response = ssm.get_parameters(Names=[
        f"/{environment}/webapp/database/host",
        f"/{environment}/webapp/database/port",
        f"/{environment}/webapp/database/user",
        f"/{environment}/webapp/database/password"
    ], WithDecryption=True)

    db_config = {p["Name"].split("/")[-1]: p["Value"] for p in param_response["Parameters"]}

    if db_host is None:
        db_host = f"{db_config['host']}:{db_config['port']}"

    if db_user is None:
        db_user = db_config["user"]

    if db_pass is None:
        db_pass = db_config["password"]

SITE = os.getenv("SITE")
SITE_TITLE = os.getenv("SITE_TITLE")

if SITE is None or SITE_TITLE is None:
    param_response = ssm.get_parameters(Names=[
        f"/{environment}/webapp/site",
        f"/{environment}/webapp/site_title"
    ], WithDecryption=True)

    site_config = {p["Name"].split("/")[-1]: p["Value"] for p in param_response["Parameters"]}

    if SITE is None:
        SITE = site_config['site']

    if SITE_TITLE is None:
        SITE_TITLE = site_config['site_title']

SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

CALLBACK_URL = os.getenv('CALLBACK_URL')

ENCRYPT_DECRYPT_KEY = os.getenv('ENCRYPT_DECRYPT_KEY', None)

if ENCRYPT_DECRYPT_KEY is None:
    param_response = ssm.get_parameters(Names=[
                f"/{environment}/webapp/encrypt_decrypt_key"
            ], WithDecryption=True)
    app_config = {p["Name"].split("/")[-1]: p["Value"] for p in param_response["Parameters"]}
    if app_config and 'encrypt_decrypt_key' in app_config:
        ENCRYPT_DECRYPT_KEY = app_config["encrypt_decrypt_key"]

if CALLBACK_URL is None:
    param_response = ssm.get_parameters(Names=[
        f"/{environment}/webapp/callback_url"
    ], WithDecryption=True)

    app_config = {p["Name"].split("/")[-1]: p["Value"] for p in param_response["Parameters"]}

    if CALLBACK_URL is None:
        CALLBACK_URL = app_config['callback_url']


