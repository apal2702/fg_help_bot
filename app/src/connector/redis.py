# import redis
# import pandas as pd
# import pyarrow as pa
# from src.utils.helper import hash_value , timeit

# class RedisConnector:
#     def __init__(
#         self, redis_host, redis_reader_host):
#         """
#         @param redis_host: Redis host
#         @type redis_host: string
#         """
#         #self.cluster_mode = cluster_mode
#         pool = redis.ConnectionPool(host=redis_host, port=6379)
#         self.redis_conn = redis.Redis(connection_pool=pool, decode_responses=True)

#     def set_expiry(self, key, time, value):
#         """
#         @param key: Redis Key pair
#         @type key: string
#         @param time: Expiry time
#         @type time: string
#         @param value:  Record time
#         @type value: string
#         @return: None
#         @rtype: None
#         """
#         self.redis_conn.setex(key, time, value)

#     def save_phone_prefix(self, df, col, record_col, expiry_col, expiry_time):
#         """
#         @param df: Toll fraud data
#         @type df: dataframe
#         @param expiry_time: Expiry time
#         @type expiry_time: string
#         @return: None
#         @rtype: None
#         """
#         ## To do Remove duplicate
#         if df.shape[0] > 0:
#             df.reset_index(inplace=True)
#             data = df[[col, 'mcc', 'mnc', record_col, expiry_col]].drop_duplicates(subset=[col, 'mcc', 'mnc'])
#             data_new = data.groupby([col, "mcc"], as_index=False).agg(lambda row: ",".join([val for val in row if str(val).strip() != ""]))
#             data = data_new.merge(data[[col, record_col, expiry_col]], on=[col], how='left')
#             data["expiry_time_range"] = data[expiry_col] - data[record_col]
#             data.reset_index(drop=True, inplace=True)
#             ##
#             # Split the data into batches of 1k for efficient set operations
#             batch_size = 1000
#             data_batches = [data[i: i + batch_size] for i in range(0, len(data), batch_size)]
#             for batch in data_batches:
#                 with self.redis_conn.pipeline() as pipe:
#                     min_index = batch.index.min()
#                     for i in range(min_index, len(batch)+min_index):
#                         prefix = data[col][i]
#                         pipe.setex(
#                             prefix,
#                             data["expiry_time_range"][i],
#                             str(
#                                 {
#                                     "mcc": data["mcc"][i],
#                                     "mnc": data["mnc"][i],
#                                     "expiry_time": data[expiry_col][i].strftime(
#                                         "%Y-%m-%d %H:%M:%S"
#                                     ),
#                                 }
#                             ),
#                         )
#                     pipe.execute()

#     def save_account_phone_prefix(self, df, expiry_time):
#         """

#         @param df: Toll fraud data
#         @type df: dataframe
#         @param expiry_time: Expiry time
#         @type expiry_time: string
#         @return: None
#         @rtype: None
#         """
#         ## To do Remove duplicate
#         if df.shape[0] > 0:
#             df.reset_index(drop = True, inplace=True)
#             df["prefix_key"] = df["account_sid"] + "_" + df["phone_prefix"]
#             col = 'prefix_key'
#             data = df[[col, 'mcc', 'mnc', "record_time", "expiry_time"]].drop_duplicates(subset=[col, 'mcc', 'mnc'])
#             data.reset_index(drop = True, inplace=True)
#             data_new = data.groupby([col, "mcc"], as_index=False).agg(lambda row: ",".join([val for val in row if str(val).strip() != ""]))
#             data_new.reset_index(drop=True, inplace=True)
#             data = data_new.merge(data[[col, "record_time", "expiry_time"]], on=[col], how='left')
#             data["expiry_time_range"] = data["expiry_time"] - data["record_time"]
#             data.reset_index(drop = True, inplace=True)

#             # Split the data into batches of 1k for efficient set operations
#             batch_size = 1000
#             data_batches = [data[i: i + batch_size] for i in range(0, len(data), batch_size)]

#             for batch in data_batches:
#                 with self.redis_conn.pipeline() as pipe:
#                     min_index = batch.index.min()
#                     for i in range(min_index, len(batch)+min_index):
#                         prefix = data["prefix_key"][i]
#                         pipe.setex(
#                             prefix,
#                             data["expiry_time_range"][i],
#                             str(
#                                 {
#                                     "mcc": data["mcc"][i],
#                                     "mnc": data["mnc"][i],
#                                     "expiry_time": data["expiry_time"][i].strftime(
#                                         "%Y-%m-%d %H:%M:%S"
#                                     ),
#                                 }
#                             ),
#                         )
#                     pipe.execute()

#             higher_prefix_df = df[df["higher_prefix_block_flag"] == "Yes"]
#             higher_prefix_df[['higher_prefix','higher_prefix_expiry_time','higher_prefix_record_time']].dropna(inplace = True)
#             higher_prefix_df.reset_index(drop=True, inplace=True)
#             higher_prefix_df["higher_prefix_key"] = (
#                 higher_prefix_df["account_sid"] + "_" + higher_prefix_df["higher_prefix"]
#             )
#             higher_prefix_df["expiry_time_range"] = (
#                 higher_prefix_df["higher_prefix_expiry_time"]
#                 - higher_prefix_df["higher_prefix_record_time"]
#             )
#             higher_prefix_df.reset_index(drop=True, inplace=True)

#             # Split the data into batches of 1k for efficient set operations
#             batch_size = 1000
#             data_batches = [higher_prefix_df[i: i + batch_size] for i in range(0, len(higher_prefix_df), batch_size)]

#             for batch in data_batches:
#                 with self.redis_conn.pipeline() as pipe:
#                     min_index = batch.index.min()
#                     for i in range(min_index, len(batch) + min_index):
#                         prefix = higher_prefix_df["higher_prefix_key"][i]
#                         pipe.setex(
#                             prefix,
#                             higher_prefix_df["expiry_time_range"][i],
#                             str(
#                                 {
#                                     "mcc": higher_prefix_df["mcc"][i],
#                                     "mnc": higher_prefix_df["mnc"][i],
#                                     "expiry_time": higher_prefix_df["higher_prefix_expiry_time"][i].strftime(
#                                         "%Y-%m-%d %H:%%M:%S"
#                                     ),
#                                 }
#                             ),
#                         )
#                     pipe.execute()

#     def save_allow_list(self, df, hash, expiry_time):
#         """

#         @param df: Toll fraud data
#         @type df: dataframe
#         @param expiry_time: Expiry time
#         @type expiry_time: string
#         @return: None
#         @rtype: None
#         """
#         df.reset_index(inplace=True)
#         df["expiry_time_range"] = df["expiry_time"] - df["record_time"]
#         if hash == "Yes":
#             df["phone_key"] = df["phone_number"].apply(
#                 lambda x: x if pd.isnull(x) else "allow_" + hash_value("+" + str(x))
#             )
#         else:
#             df["phone_key"] = df["phone_number"].apply(lambda x: "allow_" + str(x)[:])

#             # Split the data into batches of 1k for efficient set operations
#         batch_size = 1000
#         data_batches = [df[i: i + batch_size] for i in range(0, len(df), batch_size)]

#         for batch in data_batches:
#             with self.redis_conn.pipeline() as pipe:
#                 min_index = batch.index.min()
#                 for i in range(min_index, len(batch) + min_index):
#                     pipe.setex(
#                         df["phone_key"][i],
#                         df["expiry_time_range"][i],
#                         str(
#                             {
#                                 "mcc": df["mcc"][i],
#                                 "mnc": df["mnc"][i],
#                                 "expiry_time": df["expiry_time"][i].strftime(
#                                     "%Y-%m-%d %H:%M:%S"
#                                 ),
#                             }
#                         ),
#                     )
#                 pipe.execute()

#     ## Check Keys
#     def check_block_list(self, df):
#         df.reset_index(inplace=True)
#         df["already_blocked"] = "No"
#         df['phone_prefix_mnc'] = df['phone_prefix'] + "_" + df['mnc'].astype(str)
#         df['higher_prefix_mnc'] = df['higher_prefix'] + "_" + df['mnc'].astype(str)
#         r_keys = []
#         for key in self.redis_conn.scan_iter("*x"):
#             try:
#                 if type(key) == bytes:
#                     r_key = key.decode("utf-8")
#                 else:
#                     r_key = key
#                 r_val = self.redis_conn.get(r_key)
#                 r_mnc = str(eval(r_val)['mnc'])
#                 r_key_mnc = [r_key + "_" + x for x in r_mnc.split(",")]
#                 r_keys.extend(r_key_mnc)
#             except Exception as e:
#                 pass

#         df.loc[(df["phone_prefix_mnc"].isin(r_keys)), "already_blocked"] = "Yes"

#         df.loc[(df["higher_prefix_mnc"].isin(r_keys)), "already_blocked"] = "Yes"

#         df.loc[df["mode"] == "good", "already_blocked"] = "No"
#         df = df[df["already_blocked"] == "No"]

#         return df


#     def check_allow_list(self, df, hash=None):
#         df.reset_index(inplace=True)
#         df["already_blocked"] = "No"
#         if hash == "Yes":
#             df["phone_key"] = df["phone_number"].apply(
#                 lambda x: x if pd.isnull(x) else "allow_" + hash_value("+" + str(x))
#             )
#         else:
#             df["phone_key"] = df["phone_number"].apply(lambda x: "allow_" + str(x)[:])
#         r_keys = []
#         for key in self.redis_conn.scan_iter("allow*"):
#             if type(key) == bytes:
#                 r_keys.append(key.decode("utf-8"))

#         df.loc[df["phone_key"].isin(r_keys), "already_blocked"] = "Yes"
#         df = df[df["already_blocked"] == "No"]
#         return df

#     def delete_phone_prefix(self, df, col):
#         """

#         @param df: Toll fraud data
#         @type df: dataframe
#         @param expiry_time: Expiry time
#         @type expiry_time: string
#         @return: None
#         @rtype: None
#         """
#         ## To do Remove duplicate
#         df.reset_index(inplace=True)
#         with self.redis_conn.pipeline() as pipe:
#             for i in range(len(df)):
#                 prefix = df[col][i]
#                 pipe.delete(prefix)
#             pipe.execute()

#     def save_amm_flooding(self,df):

#         df["expiry_time_range"] = df["expiry_time"] - df["record_time"]
#         df.reset_index(inplace=True)
#         blocked = False
#         with self.redis_conn.pipeline() as pipe:
#             for i in range(len(df)):
#                 if self.redis_conn.get(df['amm'][i]) == None:
#                     pipe.setex(
#                         df['amm'][i],
#                         df["expiry_time_range"][i],
#                         df["expiry_time"][i].strftime("%Y-%m-%d %H:%M:%S")
#                     )
#                     blocked = True
#             pipe.execute()

#         return blocked
