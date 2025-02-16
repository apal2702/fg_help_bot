
import os
import time
import sys
import numpy as np
import pandas as pd
import rollbar
import datetime
from app.src.utils.config import load_config, load_credentials, load_rollbar_token
from app.src.utils.helper import update_log
from app.src.connector.connections import Connections
from app.src.utils.datadog_custom_metrics import log_datadog_metrics, log_datadog_event

class FGAccountStatus:
    def __init__(self, conn):
        self.conn = conn

    def is_account_active(self,account_sid):
        query = f""" select * from accsecai.dsg_all_account_features 
                                where account_sid = '{account_sid}' order by data_load_date desc limit 1
                """
        
        df = self.conn.run_query(query)
        
        return df

        #return self.conn.run_query(query)  


    def get_fg_account_status(self, account_sid):
        query = f"""
                SELECT account_sid, service_sid, fraud_guard, fraud_guard_mode, updated_at,
                       CASE WHEN LAG(fraud_guard_mode, 1) OVER(RANGE UNBOUNDED PRECEDING) <> fraud_guard_mode
                            THEN 'Change' ELSE 'No-Change' END AS ModeChange
                FROM (
                    SELECT DISTINCT account_sid, service_sid, friendly_name AS final_account_name,
                           CASE WHEN CAST(JSON_EXTRACT(configuration, '$.allowTollFraudAutoBlockingEnabled') AS BOOLEAN)
                                THEN 'enable' ELSE 'disable' END AS fraud_guard,
                           CAST(JSON_EXTRACT(configuration, '$.fraudGuardMode') AS VARCHAR) AS fraud_guard_mode,
                           updated_at,
                           DENSE_RANK() OVER (PARTITION BY account_sid ORDER BY updated_at DESC) AS rank_desc
                    FROM accsec_verify.accsec_service_events
                    WHERE account_sid LIKE '{account_sid}'
                ) ORDER BY updated_at DESC
                """
        return self.conn.run_query(query)

    def get_fg_account_data(self, account_sid, days):
        query = f"""
                SELECT data_load_date, mcc, mnc,
                       SUM(total_count) AS daily_message_count,
                       AVG(cr) AS daily_avg_cr
                FROM accsecai.amm_historic_feature 
                WHERE account_sid = '{account_sid}' 
                  AND DATE(data_load_date) > DATE(CURRENT_DATE - INTERVAL '{days}' DAY)
                GROUP BY 1, 2, 3
                """
        return self.conn.run_query(query)

    def get_fg_block_data(self, account_sid, days):
        query = f"""
                SELECT data_load_date, mcc, mnc,
                       COUNT(*) AS total_traffic,
                       SUM(CASE WHEN reason = 'FraudGuardPrefixBlock' THEN 1 ELSE 0 END) AS classic_fg,
                       SUM(CASE WHEN reason = 'FraudGuardSmsFloodingBlock' THEN 1 ELSE 0 END) AS spp_block,
                       SUM(CASE WHEN reason = 'FraudGuardSmsPumpingRiskScoreBlock' THEN 1 ELSE 0 END) AS risk_score_block,
                       SUM(CASE WHEN reason = 'fgl_safe_mcc_mnc' THEN 1 ELSE 0 END) AS fgl_safe_mcc_mnc,
                       SUM(CASE WHEN reason = 'fgl_pass_safe_mcc_request' THEN 1 ELSE 0 END) AS fgl_pass_safe_mcc_request,
                       SUM(CASE WHEN reason = '' THEN 1 ELSE 0 END) AS allowed_messages
                FROM accsecai.dsg_fds_raw_events 
                WHERE product_id = 'Verify'
                  AND account_sid = '{account_sid}' 
                  AND DATE(data_load_date) > DATE(CURRENT_DATE - INTERVAL '{days}' DAY)
                GROUP BY 1, 2, 3
                """
        return self.conn.run_query(query)

    def get_fg_account_mcc_data(self, account_sid, mcc, days):
        query = f"""
                SELECT data_load_date, mcc, mnc,
                       SUM(total_count) AS daily_message_count,
                       AVG(cr) AS daily_avg_cr
                FROM accsecai.amm_historic_feature 
                WHERE account_sid = '{account_sid}'
                  AND mcc = '{mcc}'
                  AND DATE(data_load_date) > DATE(CURRENT_DATE - INTERVAL '{days}' DAY)
                GROUP BY 1, 2, 3
                """
        return self.conn.run_query(query)

    def get_fg_block_mcc_data(self, account_sid, mcc, days):
        query = f"""
                SELECT data_load_date, mcc, mnc,
                       COUNT(*) AS total_traffic,
                       SUM(CASE WHEN reason = 'FraudGuardPrefixBlock' THEN 1 ELSE 0 END) AS classic_fg,
                       SUM(CASE WHEN reason = 'FraudGuardSmsFloodingBlock' THEN 1 ELSE 0 END) AS spp_block,
                       SUM(CASE WHEN reason = 'FraudGuardSmsPumpingRiskScoreBlock' THEN 1 ELSE 0 END) AS risk_score_block,
                       SUM(CASE WHEN reason = 'fgl_safe_mcc_mnc' THEN 1 ELSE 0 END) AS fgl_safe_mcc_mnc,
                       SUM(CASE WHEN reason = 'fgl_pass_safe_mcc_request' THEN 1 ELSE 0 END) AS fgl_pass_safe_mcc_request,
                       SUM(CASE WHEN reason = '' THEN 1 ELSE 0 END) AS allowed_messages
                FROM accsecai.dsg_fds_raw_events 
                WHERE product_id = 'Verify'
                  AND account_sid = '{account_sid}'
                  AND mcc = '{mcc}'
                  AND DATE(data_load_date) > DATE(CURRENT_DATE - INTERVAL '{days}' DAY)
                GROUP BY 1, 2, 3
                """
        return self.conn.run_query(query)

class SPPAccountStatus:
    def __init__(self, conn):
        self.conn = conn
    def is_account_active_on_psms(self,account_sid):
        query = f"""
                select *  
                    FROM accsecai.dsg_active_psms_accounts
                      WHERE account_sid = '{account_sid}'
                """
        df= self.conn.run_query(query)
        print(df)
        return not df.empty
    
    def get_spp_account_status(self, account_sid):
        query = f"""
                SELECT account_sid, service_sid, fraud_guard, fraud_guard_mode, updated_at,
                       CASE WHEN LAG(fraud_guard_mode, 1) OVER(RANGE UNBOUNDED PRECEDING) <> fraud_guard_mode
                            THEN 'Change' ELSE 'No-Change' END AS ModeChange
                FROM (
                    SELECT DISTINCT account_sid, service_sid, friendly_name AS final_account_name,
                           CASE WHEN CAST(JSON_EXTRACT(configuration, '$.allowTollFraudAutoBlockingEnabled') AS BOOLEAN)
                                THEN 'enable' ELSE 'disable' END AS fraud_guard,
                           CAST(JSON_EXTRACT(configuration, '$.fraudGuardMode') AS VARCHAR) AS fraud_guard_mode,
                           updated_at,
                           DENSE_RANK() OVER (PARTITION BY account_sid ORDER BY updated_at DESC) AS rank_desc
                    FROM accsec_verify.accsec_service_events
                    WHERE account_sid LIKE '{account_sid}'
                ) ORDER BY updated_at DESC
                """
        return self.conn.run_query(query)

    def get_spp_account_data(self, account_sid, days):
        query = f"""
                SELECT data_load_date, mcc, mnc,
                       SUM(total_count) AS daily_message_count
                FROM accsecai.psms_amm_historic_feature 
                WHERE account_sid = '{account_sid}' 
                  AND DATE(data_load_date) > DATE(CURRENT_DATE - INTERVAL '{days}' DAY)
                GROUP BY 1, 2, 3
                """
        return self.conn.run_query(query)

    def get_spp_block_data(self, account_sid, days):
        query = f"""
                SELECT data_load_date, mcc, mnc,
                       COUNT(*) AS total_traffic,
                       SUM(CASE WHEN reason = 'FraudGuardSmsFloodingBlock' THEN 1 ELSE 0 END) AS spp_block,
                       SUM(CASE WHEN reason = 'SmsPumpingRiskScoreBlock' THEN 1 ELSE 0 END) AS risk_score_block,
                       SUM(CASE WHEN reason = 'fgl_safe_mcc_mnc' THEN 1 ELSE 0 END) AS fgl_safe_mcc_mnc,
                       SUM(CASE WHEN reason = 'fgl_pass_safe_mcc_request' THEN 1 ELSE 0 END) AS fgl_pass_safe_mcc_request,
                       SUM(CASE WHEN reason = '' THEN 1 ELSE 0 END) AS allowed_messages
                FROM accsecai.dsg_fds_raw_events 
                WHERE product_id = 'Messaging'
                  AND account_sid = '{account_sid}' 
                  AND DATE(data_load_date) > DATE(CURRENT_DATE - INTERVAL '{days}' DAY)
                GROUP BY 1, 2, 3
                """
        return self.conn.run_query(query)

    def get_spp_account_mcc_data(self, account_sid, mcc, days):
        query = f"""
                SELECT data_load_date, mcc, mnc,
                       SUM(total_count) AS daily_message_count
                FROM accsecai.psms_amm_historic_feature 
                WHERE account_sid = '{account_sid}' 
                  AND mcc = '{mcc}'
                  AND DATE(data_load_date) > DATE(CURRENT_DATE - INTERVAL '{days}' DAY)
                GROUP BY 1, 2, 3
                """
        return self.conn.run_query(query)

    def get_spp_block_mcc_data(self, account_sid, mcc, days):
        query = f"""
                SELECT data_load_date, mcc, mnc,
                       COUNT(*) AS total_traffic,
                       SUM(CASE WHEN reason = 'FraudGuardSmsFloodingBlock' THEN 1 ELSE 0 END) AS spp_block,
                       SUM(CASE WHEN reason = 'SmsPumpingRiskScoreBlock' THEN 1 ELSE 0 END) AS risk_score_block,
                       SUM(CASE WHEN reason = 'fgl_safe_mcc_mnc' THEN 1 ELSE 0 END) AS fgl_safe_mcc_mnc,
                       SUM(CASE WHEN reason = 'fgl_pass_safe_mcc_request' THEN 1 ELSE 0 END) AS fgl_pass_safe_mcc_request,
                       SUM(CASE WHEN reason = '' THEN 1 ELSE 0 END) AS allowed_messages
                FROM accsecai.dsg_fds_raw_events 
                WHERE product_id = 'Messaging'
                  AND account_sid = '{account_sid}' 
                  AND mcc = '{mcc}'
                  AND DATE(data_load_date) > DATE(CURRENT_DATE - INTERVAL '{days}' DAY)
                GROUP BY 1, 2, 3
                """
        return self.conn.run_query(query)

if __name__ == "__main__":
    env = os.getenv("TWILIO_ENVIRONMENT")
    rollbar_token = load_rollbar_token('fg_rollbar_access_token')
    rollbar.init(rollbar_token, env)
    try:
        role = sys.argv[1]
        reset = sys.argv[2]
        today = datetime.date.today()
        start_time = time.time()
        # Uncomment the following lines if needed:
        # update_account_category(role, reset)
        # log_datadog_metrics("asfd.psms_account_category_update_time", time.time() - start_time)
    except Exception as err:
        rollbar.report_exc_info()
        print("Error occurred in the PSMS FG Account categorisation code", err)
        log_datadog_event(err)
