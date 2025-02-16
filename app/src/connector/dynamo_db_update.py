# import sys
# import boto3
# import time

# class DynamoDB:

#     def update_acc_metadata_dynamo(self,df,batch_size):

#         try:
#             table_name = 'dsg-flooding-metadata'
#             dynamodb = boto3.client('dynamodb', region_name='us-east-1')

#             # Define the attribute(s) to be updated
#             update_expression = 'SET #account_category = account_category, #block_ttl_mins = block_ttl_mins, #lookback_mins = lookback_mins,#default_threshold = default_threshold ,#observe = observe ,#optout = optout'
#             expression_attribute_names = {
#                                           '#account_category': 'account_category',
#                                           '#block_ttl_mins': 'block_ttl_mins',
#                                           '#lookback_mins': 'lookback_mins',
#                                           '#default_threshold': 'default_threshold',
#                                           '#observe': 'observe',
#                                           '#optout': 'optout',
#                                           }
#             # Define a list to hold the item updates
#             item_updates = []

#             # Iterate over each row in the DataFrame and add the item update to the list
#             for index, row in df.iterrows():
#                 # Define the item's primary key
#                 item_key = {'id': {'S': str(row['id'])}}

#                 # Define the expression attribute values
#                 expression_attribute_values = {
#                                                'account_category': {'S': str(row['account_category'])},
#                                                'block_ttl_mins': {'N': str(row['block_ttl_mins'])},
#                                                'lookback_mins': {'N': str(row['lookback_mins'])},
#                                                'default_threshold': {'N': str(row['default_threshold'])},
#                                                'optout': {'BOOL': row['optout']},
#                                                'observe': {'BOOL': row['observe']}
#                                                }


#                 # Add the item update to the list
#                 item_updates.append({
#                     'PutRequest': {
#                         'Item': {
#                             **item_key,
#                             **expression_attribute_values
#                         }
#                     }
#                 })

#                 # If the list reaches a batch size of 25 (the maximum number of items per batch), write the items to the table
#                 if len(item_updates) == batch_size:
#                     response = dynamodb.batch_write_item(
#                         RequestItems={
#                             table_name: item_updates
#                         }
#                     )
#                     item_updates = []

#             # Write any remaining items to the table
#             if len(item_updates) > 0:
#                 response = dynamodb.batch_write_item(
#                     RequestItems={
#                         table_name: item_updates
#                     }
#                 )

#         except Exception as err:
#             print(err)

#     def update_amm_threshold_dynamo(self,df, batch_size):

#         try:
#             table_name = 'dsg-flooding-threshold'
#             dynamodb = boto3.client('dynamodb', region_name='us-east-1')

#             # Define the attribute(s) to be updated
#             update_expression = 'SET #account_category = account_category, #ccr_label = ccr_label, #country_code = country_code, #mcc = mcc, #mnc = mnc, #block_ttl_mins = block_ttl_mins, #observe =  observe, #lookback_mins = lookback_mins, #thresholds = thresholds'
#             expression_attribute_names = {'#account_category': 'account_category',
#                                           '#ccr_label': 'ccr_label',
#                                           '#country_code': 'country_code',
#                                           '#mcc': 'mcc',
#                                           '#mnc': 'mnc',
#                                           '#observe': 'observe',
#                                           '#block_ttl_mins': 'block_ttl_mins',
#                                           '#lookback_mins': 'lookback_mins',
#                                           '#thresholds': 'thresholds',
#                                           }
#             # Define a list to hold the item updates
#             item_updates = []

#             # Iterate over each row in the DataFrame and add the item update to the list
#             for index, row in df.iterrows():
#                 # Define the item's primary key
#                 item_key = {'id': {'S': str(row['id'])}}

#                 # Define the expression attribute values
#                 expression_attribute_values = {'account_category': {'S': str(row['account_category'])},
#                                                'ccr_label': {'S': str(row['ccr_label'])},
#                                                'country_code': {'S': str(row['country_code'])},
#                                                'mcc': {'S': str(row['mcc'])},
#                                                'mnc': {'S': str(row['mnc'])},
#                                                'observe': {'BOOL': row['observe']},
#                                                'block_ttl_mins': {'N': str(row['block_ttl_mins'])},
#                                                'lookback_mins': {'N': str(row['lookback_mins'])},
#                                                'thresholds': {'L': [
#                                                    {
#                                                        "M": {
#                                                            "model_name": {
#                                                                "S": "account_ucl"
#                                                            },
#                                                            "model_type": {
#                                                                "S": "account"
#                                                            },
#                                                            "model_value": {
#                                                                "N": str(int(row['ucl']))
#                                                            }
#                                                        }
#                                                    },
#                                                    {
#                                                        "M": {
#                                                            "model_name": {
#                                                                "S": "three_sigma"
#                                                            },
#                                                            "model_type": {
#                                                                "S": "statistical"
#                                                            },
#                                                            "model_value": {
#                                                                "N": str(int(row['threshold']))
#                                                            }
#                                                        }
#                                                    }
#                                                ]}
#                                                }

#                 # Add the item update to the list
#                 item_updates.append({
#                     'PutRequest': {
#                         'Item': {
#                             **item_key,
#                             **expression_attribute_values
#                         }
#                     }
#                 })

#                 # If the list reaches a batch size of 25 (the maximum number of items per batch), write the items to the table
#                 if len(item_updates) == batch_size:
#                     response = dynamodb.batch_write_item(
#                         RequestItems={
#                             table_name: item_updates
#                         }
#                     )
#                     item_updates = []

#             # Write any remaining items to the table
#             if len(item_updates) > 0:
#                 response = dynamodb.batch_write_item(
#                     RequestItems={
#                         table_name: item_updates
#                     }
#                 )

#         except Exception as err:
#             print(err)
#             # End of Selection