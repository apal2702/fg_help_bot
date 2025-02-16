# import requests
# import pandas as pd
# import warnings
# import json
# from src.utils.helper import update_log

# warnings.filterwarnings("ignore")


# class ElasticSearchConnector:
#     def __init__(self, url, index):
#         # print("Connecting to elastic search")
#         self.url = url
#         self.index = index

#     def run_query(self, query, cols=[]):

#         """
#         Connect to Elastic Search and run given query in argument and fetch data

#         @param query: SQL Query
#         @type query: string
#         @param cols: dataframe columns
#         @type cols: list
#         @return: cursor_id , Dataframe data
#         @rtype: string, Dataframe
#         """

#         headers = {"Content-type": "application/json"}
#         payload = query
#         response = requests.request(
#             "GET", self.url, headers=headers, data=json.dumps(payload)
#         )
#         if response.ok:
#             if len(cols) < 1:
#                 col_names = response.json()["columns"]
#                 for i in range(len(col_names)):
#                     cols.append(col_names[i]["name"])

#             df = pd.DataFrame(response.json()["rows"], columns=cols)
#             try:
#                 cursor_id = response.json()["cursor"]
#             except KeyError:
#                 cursor_id = False

#             #update_log("The data extracted from elasticsearch query is : {}".format(df.shape))

#             return cursor_id, df
#         else:
#             print(
#                 "The response is not successful. Please check connection or the query"
#             )
#             print(response.text)
#             return 0
#             # End of Selection
