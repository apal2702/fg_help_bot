import pandas as pd
import prestodb
import os
import sys

from prestodb.exceptions import HttpError

class PrestoConnector:
    def __init__(self, username, password, host=None, port=None):
        self.cursor = None
        self.presto_host = host or "odin.prod.twilio.com"
        self.presto_port = port or 8443
        self.connect(username, password)

    def connect(self, username, password):
        """

        @param username: Presto username
        @type username: string
        @param password: Presto password
        @type password: string
        @return: None
        @rtype: None
        """
        conn = prestodb.dbapi.connect(
            host=self.presto_host,
            port=self.presto_port,
            user=username,
            catalog="hive",
            schema="public",
            http_scheme="https",
            auth=prestodb.auth.BasicAuthentication(username, password),
        )

        cur = conn.cursor()
        self.cursor = cur

        try:
            query = "Select 1+2"
            self.cursor.execute(query)
            print("Presto Connection Successful...!!!")
        except HttpError:
            print("Couldn't create connection. Check VPN Connection or Credentials.")
            sys.exit()

    def run_query(self, query):
        """
        @param query: SQL query
        @type query: string
        @return: DataFrame
        @rtype: DataFrame
        """
        self.cursor.execute(query)
        fetchall_data = self.cursor.fetchall()
        col_name = [desc[0] for desc in self.cursor.description]
        df = pd.DataFrame(fetchall_data, columns=col_name)
        return df


if __name__ == "__main__":
    username = ""
    password = ""

    presto = PrestoConnector(username, password)
    # query = "Select count(*) as count from hive.accsecai.disposable_numbers_lookup"
    # query = "Select * from accsecai.verify_revenue_top_accounts_countries"
    query = "Select * from public.accsec_verify_comms  limit 10"

    df = presto.run_query(query)
    print(df.head())
    # df.to_csv('output.csv', index=False)
