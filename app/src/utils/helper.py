import os
import logging
import pandas as pd
import time
import datetime
from functools import wraps
import hashlib

# from csv_logger import CsvLogger
from time import sleep
import requests
import subprocess
import json

PROJECT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)


def update_quantico_log(event, status, response, request, timestamp):
    log = {
        "event": event,
        "level": status,
        "objects": response,
        "product": "Toll Fraud",
        "public": False,
        "request": request,
        "timestamp": timestamp,
    }
    print(json.dumps(log))


def update_log(message, breach=False):
    """

    @param message: log message
    @type message: string
    @return: None
    @rtype: None
    """
    if breach:
        filename = "log/breach_info.log"
    else:
        filename = "log/scraper_info.log"

    log_folder = "log"
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.basicConfig(
        filename=filename, format="%(asctime)s %(message)s", filemode="a+"
    )
    # Creating an object
    logger = logging.getLogger()
    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.INFO)

    logger.info(message)

def update_main_log(message):
    """

    @param message: log message
    @type message: string
    @return: None
    @rtype: None
    """
    filename = "log/main_run_info.log"

    log_folder = "log"
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.basicConfig(
        filename=filename, format="%(asctime)s %(message)s", filemode="a+"
    )
    # Creating an object
    logger = logging.getLogger()
    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.INFO)

    logger.info(message)



def save_data(file, data_df, update=False):
    """

    @param file: data file path
    @type file: string
    @param data_df: data
    @type data_df: dataframe
    @param update: to update data
    @type update: Boolean
    @return: None
    @rtype: None
    """
    try:
        dir_path = os.path.join(PROJECT_DIR, "data")
        if not os.path.exists(dir_path):
            print("Creating data Dir at, ", dir_path)
            os.makedirs(dir_path)
        path = os.path.join(PROJECT_DIR, "data", file)

        if os.path.exists(path) and update:
            df = pd.read_parquet(path)
            df = pd.concat([df,data_df])
        else:
            df = data_df
        df.to_parquet(path)

    except Exception as e:
        print(e)


def update_data(file, data_df, not_breached_df, update=False):
    """

    @param file: data file path
    @type file: string
    @param data_df: data
    @type data_df: dataframe
    @param not_breached_df: data
    @type data_df: dataframe
    @param update: to update data
    @type update: Boolean
    @return: None
    @rtype: None
    """
    try:
        dir_path = os.path.join(PROJECT_DIR, "data")
        if not os.path.exists(dir_path):
            print("Creating data Dir at, ", dir_path)
            os.makedirs(dir_path)
        path = os.path.join(PROJECT_DIR, "data", file)

        if os.path.exists(path) and update:
            df = pd.read_parquet(path)
            df["key"] = (
                df["account_sid"]
                + "-"
                + df["mcc"].astype(str)
                + "-"
                + df["mnc"].astype(str)
            )
            df = df[~df["key"].isin(not_breached_df["key"])]
            df =pd.concat([df,data_df])
            df.sort_values("expiry_time", ascending=False, inplace=True)
            df.drop_duplicates(subset=["account_sid", "mnc", "mcc"], inplace=True)
            df = df[df["expiry_time"] > datetime.datetime.now(datetime.timezone.utc)]
        else:
            df = data_df
        df.to_parquet(path, index=False)

    except Exception as e:
        print("Error in updating data", e)


def move_to_s3(source, destination):
    """

    @param source:  local source path
    @type source: string
    @param destination: s3 destination path
    @type destination: string
    @return: None
    @rtype: None
    """
    cmd = "aws s3 cp {} {}".format(source, destination)
    os.system(cmd)


def move_from_s3(source, destination):
    """

    @param source: s3 source path
    @type source: string
    @param destination: local destination path
    @type destination: string
    @return: None
    @rtype: None
    """
    cmd = "aws s3 cp {} {}".format(source, destination)
    os.system(cmd)


def sync_s3(source, destination):
    """

    @param source: s3 source directory
    @type source: string
    @param destination: s3 destination directory
    @type destination: string
    @return: None
    @rtype: None
    """
    cmd = "aws s3 sync {} {}".format(source, destination)
    os.system(cmd)


def join_friendly_name(account_data, df_friendly_name):
    """

    @param account_data: Account data
    @type account_data: dataframe
    @param df_friendly_name: Friendly name data
    @type df_friendly_name: dataframe
    @return: Account data
    @rtype: dataframe
    """
    account_data["friendly_name"] = account_data["account_sid"].map(
        df_friendly_name.set_index("account_sid")["friendly_name"]
    )
    return account_data


def do_not_include_filter(df, conf):

    if "do_not_include" not in conf:
        return df

    df = df.copy()

    do_not_include = conf["do_not_include"]

    if ("mcc" in do_not_include) and (len(do_not_include["mcc"]) > 0):
        # df = df[~df['mcc'].isin(do_not_include['mcc'])]
        df.loc[df["mcc"].isin(do_not_include["mcc"]), "block"] = "No"

    if ("mcc_mnc" in do_not_include) and (len(do_not_include["mcc_mnc"]) > 0):
        df.loc[:, "mcc_mnc"] = df["mcc"].astype(str) + "_" + df["mnc"].astype(str)
        # df = df[~df['mcc_mnc'].isin(do_not_include['mcc_mnc'])]
        df.loc[df["mcc_mnc"].isin(do_not_include["mcc_mnc"]), "block"] = "No"
        df.drop("mcc_mnc", axis=1, inplace=True)

    if ("mcc_mnc_account" in do_not_include) and (
        len(do_not_include["mcc_mnc_account"]) > 0
    ):
        df.loc[:, "mcc_mnc_account"] = (
            df["mcc"].astype(str)
            + "_"
            + df["mnc"].astype(str)
            + "_"
            + df["account_sid"].astype(str)
        )
        # df = df[~df['mcc_mnc_account'].isin(do_not_include['mcc_mnc_account'])]
        df.loc[
            df["mcc_mnc_account"].isin(do_not_include["mcc_mnc_account"]), "block"
        ] = "No"
        df.drop("mcc_mnc_account", axis=1, inplace=True)

    return df


def check_skiplist_file(whitelist_path):

    env = os.getenv("TWILIO_ENVIRONMENT") or ""
    if env == "":
        if not os.path.exists(whitelist_path):
            return False
        else:
            return True
    else:
        # check file is in s3 bucket
        file = subprocess.getoutput("aws s3 ls {}".format(whitelist_path))
        if file == "":
            return False
        else:
            return True


def skiplist_numbers(toll_fraud_data, file):

    if file is not None and check_skiplist_file(file):
        skiplist_df = pd.read_parquet(file)
        skiplist_keys = skiplist_df["prefix"].unique()

        toll_fraud_data = toll_fraud_data[
            ~toll_fraud_data["phone_prefix"].isin(skiplist_keys)
        ]

    return toll_fraud_data


def timeit(func):
    """
    Custom decorator function to calculate time taken for specified function
    Args:
        func: Function to compute time taken
    Returns: None
    """

    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time

        message = f"Function {func.__name__} Took {total_time:.2f}s"
        # update_quantico_log(level="TIMEIT", message=message)
        update_log(message)
        return result

    return timeit_wrapper


def check_loadbalancer_status():
    r = requests.get("http://localhost:9999/v1/Hosts/ThisHost/Services")
    flag = r.json()[0]["is_lb_ready"]
    host_id = r.json()[0]["host_sid"]
    role = r.json()[0]["role"]
    host = r.json()[0]["host"]
    data = {"role": role, "host": host, "host_id": host_id}
    return data, flag


def hash_value(data_val, hash_function="sha256_hex"):
    """
    Function to hash a value given the hash function name to be used
    Arguments:
        data_val (str): value to be hashed
        hash_function (optional, str): hash function name
    Returns:
        hashed value
    """
    hash_function = hash_function or "sha256_hex"
    hashed_value = None
    if hash_function == "md5_hex":
        hashed_value = hashlib.md5(data_val.encode()).hexdigest()
    elif hash_function == "sha256_hex":
        hashed_value = hashlib.sha256(data_val.encode()).hexdigest()
    return hashed_value

