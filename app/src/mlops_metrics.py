import os
import time
import sys
import numpy as np
import pandas as pd
import rollbar
import datetime
from src.utils.config import load_config, load_credentials, load_rollbar_token

from src.utils.helper import update_log
from src.connector.connections import Connections
from src.utils.datadog_custom_metrics import log_datadog_metrics, log_datadog_event

class MlopsMetrics:
    def __init__(self, conn):
        self.conn = conn

    ## Get Active Accounts on Verify and PSMS

    ## Get FG Blocks vs Allowed traffic
    def get_daily_fg_metrics(self, days):
        query = f"""
                select  data_load_date,
                sum(case when reason = 'FraudGuardPrefixBlock' then 1 else 0 end) as classic_fg_block,
               sum(case when reason = 'FraudGuardSmsFloodingBlock' then 1 else 0 end) as spp_block,
                sum(case when reason = 'FraudGuardSmsPumpingRiskScoreBlock' then 1 else 0 end) as risk_score_block,
                sum(case when reason = 'fgl_safe_mcc_mnc' then 1 else 0 end) as fgl_safe_mcc_mnc,
               sum(case when reason = 'fgl_pass_safe_mcc_request' then 1 else 0 end) as fgl_pass_safe_mcc_request,
               sum(case when reason = '' then 1 else 0 end) as allowed_messages,
               count(*) as total_traffic
                from accsecai.dsg_fds_raw_events
                where date(data_load_date) > DATE (current_date - interval '{days}' day)
                    group by 1 order by 4 desc
                                
                """
        df_query_data = self.conn.run_query(query)

        return df_query_data

     ## Get SPP Blocks vs Allowed traffic
    def get_daily_spp_metrics(self, days):
        query = f"""
                select  data_load_date,
                sum(case when reason = 'FraudGuardSmsFloodingBlock' then 1 else 0 end) as spp_block,
                sum(case when reason = 'SmsPumpingRiskScoreBlock' then 1 else 0 end) as risk_score_block,
                sum(case when reason = 'fgl_safe_mcc_mnc' then 1 else 0 end) as fgl_safe_mcc_mnc,
               sum(case when reason = 'fgl_pass_safe_mcc_request' then 1 else 0 end) as fgl_pass_safe_mcc_request,
               sum(case when reason = '' then 1 else 0 end) as allowed_messages,
               count(*) as total_traffic
            from accsecai.dsg_fds_raw_events
             where date(data_load_date) > DATE (current_date - interval '{days}' day)
                 group by 1 order by 4 desc
                                
                """
        df_query_data = self.conn.run_query(query)

        return df_query_data


    def get_fg_block_data(self, start_date, end_date):
        query = f"""
                SELECT 
                SUM(CASE WHEN reason = 'FraudGuardPrefixBlock' THEN 1 ELSE 0 END) AS verify_prefix,
                SUM(CASE WHEN reason = 'FraudGuardSmsFloodingBlock' THEN 1 ELSE 0 END) AS spp,
                SUM(CASE WHEN reason = '' THEN 1 ELSE 0 END) AS allowed_messages
                FROM accsecai.dsg_fds_raw_events 
                WHERE 
                product_id = 'Verify' AND 
                data_load_date BETWEEN date('{start_date}') AND date('{end_date}')
                """
        df_query_data = self.conn.run_query(query)

        return df_query_data

    ## Get Account Category in last 30 days from Red and Yellow CCR
    def get_flooding_block_data(self, start_date, end_date):
        
        query = f"""
            SELECT 
            SUM(CASE WHEN reason = 'FraudGuardSmsFloodingBlock' THEN 1 ELSE 0 END) AS flooding_block,
            SUM(CASE WHEN reason = '' THEN 1 ELSE 0 END) AS allowed_messages
            FROM accsecai.dsg_fds_raw_events 
            WHERE product_id = 'Messaging'
                and 
                data_load_date BETWEEN date('{start_date}') AND date('{end_date}')
                """
        df_query_data = self.conn.run_query(query)

        return df_query_data

    def get_risk_score_block_data(self, start_date, end_date):
        query = f"""
                SELECT 
                    SUM(CASE WHEN reason = 'FraudGuardSmsPumpingRiskScoreBlock' THEN 1 ELSE 0 END) AS riskscore,
                    SUM(CASE WHEN reason = 'SmsPumpingRiskScoreBlock' THEN 1 ELSE 0 END) AS sppriskscore,
                    SUM(CASE WHEN reason = '' THEN 1 ELSE 0 END) AS allowed_messages
                FROM accsecai.dsg_fds_raw_events 
                WHERE 
                data_load_date BETWEEN date('{start_date}') AND date('{end_date}')
                        """
        df_query_data = self.conn.run_query(query)

        return df_query_data
    
    def get_fg_block_summary(self, start_date, end_date):
        query = f"""
                select count(distinct account_sid) as active_accounts,
                        sum(case when reason = 'FraudGuardPrefixBlock' then 1 else 0 end) as verify_prefix,
                        sum(case when reason = 'FraudGuardSmsFloodingBlock' then 1 else 0 end) as flooding,
                        sum(case when reason = 'FraudGuardSmsPumpingRiskScoreBlock' then 1 else 0 end) as riskscore,
                        sum(case when reason = 'GeopermissionCountryBlock' then 1 else 0 end) as geo_perm_country_block,
                        sum(case when reason = 'GeopermissionPrefixBlock' then 1 else 0 end) as geo_perm_prefix_block,
                        SUM(CASE WHEN reason = 'fgl_safe_mcc_mnc' THEN 1 ELSE 0 END) AS fgl_safe_mcc_mnc,
                        SUM(CASE WHEN reason = 'fgl_pass_safe_mcc_request' THEN 1 ELSE 0 END) AS fgl_pass_safe_mcc_request,
                        sum(case when reason = '' then 1 else 0 end) as allowed_messages,
                        sum(case when block != True then 1 else 0 end) as total_allowed,
                        sum(case when block = True then 1 else 0 end) as total_blocked
                        from accsecai.dsg_fds_raw_events where
                        product_id = 'Verify' and
                            data_load_date BETWEEN date('{start_date}') AND date('{end_date}')
                        """
        df_query_data = self.conn.run_query(query)

        return df_query_data
    

    def get_spp_block_summary(self, start_date, end_date):
        query = f"""
                select
                    count(distinct account_sid) as active_accounts,
                    sum(case when reason = 'FraudGuardSmsFloodingBlock' then 1 else 0 end) as flooding,
                    sum(case when reason = 'SmsPumpingRiskScoreBlock' then 1 else 0 end) as riskscore,
                    sum(case when reason = 'TrustGuardBlock' then 1 else 0 end) as tg_block,
                    SUM(CASE WHEN reason = 'fgl_safe_mcc_mnc' THEN 1 ELSE 0 END) AS fgl_safe_mcc_mnc,
                    SUM(CASE WHEN reason = 'fgl_safe_mcc_mnc' THEN 1 ELSE 0 END) AS fgl_safe_mcc_mnc,
                    SUM(CASE WHEN reason = 'fgl_pass_safe_mcc_request' THEN 1 ELSE 0 END) AS fgl_pass_safe_mcc_request,
                    sum(case when reason = '' then 1 else 0 end) as allowed_messages,
                    sum(case when block != True then 1 else 0 end) as total_allowed,
                    sum(case when block = True then 1 else 0 end) as total_blocked
                    from accsecai.dsg_fds_raw_events where
                    product_id = 'Messaging' and
                        data_load_date BETWEEN date('{start_date}') AND date('{end_date}')
                        """
        df_query_data = self.conn.run_query(query)

        return df_query_data
    





if __name__ == "__main__":

    env = os.getenv("TWILIO_ENVIRONMENT")
    rollbar_token = load_rollbar_token('fg_rollbar_access_token')
    rollbar.init(rollbar_token, env)
    try:
        role = sys.argv[1]
        reset = sys.argv[2]
        today = datetime.date.today()
        start_time = time.time()
        #update_account_category(role,reset)
        #log_datadog_metrics("asfd.psms_account_category_update_time", time.time() - start_time)

    except Exception as err:
        rollbar.report_exc_info()
        print("Error occurred in the PSMS FG Account categorisation code", err)
        log_datadog_event(err)
