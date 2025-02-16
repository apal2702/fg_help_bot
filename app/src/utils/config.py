import os
import toml
import json

PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)


def load_config(role):
    """

    @return:  toml file configurations
    @rtype: object
    """
    env = os.getenv("TWILIO_ENVIRONMENT") or ""

    if role == "toll_fraud_detector":
        config_filepath = env + "_" + "config.toml"
    elif role == "accsec-ai-playground":
        config_filepath = env + "_test_" + "config.toml"
    elif role == 'test':
        config_filepath = "test_" + "config.toml"
    else:
        config_filepath = "_" + "config.toml"

    filepath = os.path.join(PROJECT_DIR, "config", config_filepath)
    with open(filepath, "r") as f:
        return toml.load(f)


def load_credentials(secret):
    creds = read_secrets(secret)
    username = creds["username"]
    password = creds["password"]
    return username, password

def load_rollbar_token(secret):
    token = read_secrets(secret)
    rollbar_token = token['access_token']
    return rollbar_token

def read_secrets(secret):
    """
    Function to get value of secrets
    Args:
        secret: secret name saved on the admiral role
    Returns: secret dictionary
    """
    try:
        secret_val = json.load(open(os.path.join("/secrets", secret), "r"))
        return secret_val
    except FileNotFoundError:
        print("error")
        # raise_exception("Secret Does Not Exist")
        # return {
        #     "username": os.environ.get("USERNAME"),
        #     "password": os.environ.get("PASSWORD")
        # }
