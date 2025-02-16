import os
import datetime
import pandas as pd
from src.utils.helper import move_to_s3, move_from_s3


class DataUtils:
    def __init__(self, connector, config):
        self.conn = connector
        self.config = config

    def move_data_to_s3(self, data_type=""):
        """
        @return: None
        @rtype: None
        """
        env = os.getenv("TWILIO_ENVIRONMENT")
        if env != "prod":
            return
        if self.config["s3_flag"] == "False":
            return
        PROJECT_DIR = os.path.abspath(
            os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
        )

        DATA_DIR = os.path.join(PROJECT_DIR, "data")

        cur_time = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M")
        cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
        ## Local Breach path
        breach_table_local = os.path.join(
            PROJECT_DIR, "data", self.config["breach_table_local"]
        )
        if data_type == 'breach':
            # Breach
            ## daily result file path
            daily_s3_breach_data = (
                self.config["s3_output"] + "breach_state_data/" + str(cur_date) + "/" + cur_time + ".gzip"
            )
            move_to_s3(breach_table_local, self.config["breach_table_s3"])

            ## Move backup data and daily data for Breach to S3
            move_to_s3(
                os.path.join(DATA_DIR, self.config["current_breach_table_local"]),
                daily_s3_breach_data,
            )
        elif data_type == 'flooding':

            # Sms Flooding data
            daily_s3_flooding_data = (
                    self.config["s3_output"] + "dynamic_flooding_data/" + str(cur_date) + "/" + cur_time + ".gzip"
            )

            ## Move Dynamic Flooding data
            move_to_s3(
                os.path.join(DATA_DIR, self.config["current_dynamic_flood_local"]),
                daily_s3_flooding_data,
            )

        else:
            ## Toll Fraud

            ## daily result file path
            daily_s3_tollfraud_data = (
                self.config["s3_output"] + "toll_phone_data/" + str(cur_date) + "/" + cur_time + ".gzip"
            )
            daily_s3_tollfraud_prefix_data = (
                self.config["s3_output"] + "higher_prefix_data/" + str(cur_date) + "/" + cur_time + ".gzip"
            )

            ## daily allow list file path
            allow_table_local = os.path.join(
                PROJECT_DIR, "data", self.config["allowlist_data_local"]
            )
            daily_s3_allow_list = (
                self.config["s3_allow_list"] + str(cur_date) + "/" + cur_time + ".gzip"
            )

            move_to_s3(
                os.path.join(DATA_DIR, self.config["current_toll_phone_table_local"]),
                daily_s3_tollfraud_data,
            )
            move_to_s3(
                os.path.join(DATA_DIR, self.config["current_toll_phone_prefix_local"]),
                daily_s3_tollfraud_prefix_data,
            )
            ## Allow state
            move_to_s3(allow_table_local, daily_s3_allow_list)

    def move_data_from_s3(self, PROJECT_DIR):
        """
        @param PROJECT_DIR: Project directory path
        @type PROJECT_DIR: string
        @return: None
        @rtype: None
        """
        env = os.getenv("TWILIO_ENVIRONMENT")
        if env != "prod":
            return

        breach_table_local = os.path.join(
            PROJECT_DIR, "data", self.config["breach_table_local"]
        )
        # toll_phone_table_local = os.path.join(
        #    PROJECT_DIR, "data", self.config["toll_phone_table_local"]
        # )

        move_from_s3(self.config["breach_table_s3"], breach_table_local)


class DataProcess:
    def preprocess_data(self,df,global_data_path,key):
        try:
            cols = df.columns
            last_amm_df = pd.read_parquet(global_data_path, columns=cols)
            merged_df = df.merge(last_amm_df, indicator=True, how='outer')
            new_df = merged_df[merged_df['_merge'] == 'left_only']
            new_df.drop_duplicates(subset=[key], inplace=True)
            new_df.reset_index(drop=True, inplace=True)
            new_df.drop('_merge', axis=1, inplace=True)
            merged_df.drop_duplicates(subset=[key], inplace=True)
            merged_df.reset_index(drop=True, inplace=True)
            merged_df.drop('_merge', axis=1, inplace=True)
        except Exception as err:
            df.drop_duplicates(subset=[key], inplace=True)
            new_df = df.copy()
            merged_df = df.copy()
            pass

        return merged_df, new_df

    def save_data(self, raw_df, df, delta_data_s3_path, master_data_s3_path,daily_run_s3_path,key,reset=False):

        ## Save Each Run Data
        if key == 'account_sid':
            daily_run_s3_path = daily_run_s3_path + "account_categorisation/"
        elif key == 'amm':
            daily_run_s3_path = daily_run_s3_path + "amm_threshold/"
        else:
            daily_run_s3_path = daily_run_s3_path + "unknown/"

        cur_time = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M")
        cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
        raw_df.to_parquet(daily_run_s3_path + str(cur_date) + "/" + str(cur_time) + ".gzip")

        if reset:
            merged_df = df
            new_df = df
        else:
            merged_df, new_df = self.preprocess_data(df, master_data_s3_path, key)
        # Save each AMM feature in global AMM threshold list
        merged_df.to_parquet(master_data_s3_path)
        ## The Delta data to update in Dynamo DB
        new_df.to_parquet(delta_data_s3_path)
        return merged_df, new_df