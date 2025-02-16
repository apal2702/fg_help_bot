# Import necessary libraries and define models for data schema
from pydantic import BaseModel
import ollama
import json
from openai import OpenAI
import requests
import os
from langchain.chat_models import ChatOllama
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.memory import ChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

os.environ['OPENAI_API_KEY'] = 'sk-proj-lhm1tMlkwAXIF'

ollama_models = ['deepseek-r1:14b', 'llama3.1', 'mistral']
openai_models = ['gpt-4o-mini', 'gpt-3.5-turbo-0125']

# Define schema for Accounts information
class Account(BaseModel):
    account_sid: str
    country: list[str]
    mcc: list[str]
    mnc: list[str]
    date: list[str]
    error_code: list[str]

# Define schema for Issue information
class Issue(BaseModel):
    category: list[str]
    reason: str

# Define schema for Product information
class Product(BaseModel):
    result: list[str]

# Function to call the ChatOllama model with memory
def call_chatollama_model(input_text, model="chat-ollama-mini"):
    """
    Calls the ChatOllama model with the given input text and model, and uses memory.
    Returns the response from the model.
    """
    # Initialize memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Initialize the ChatOllama model
    client = ChatOllama(model=model)

    # Create a conversation chain with memory
    conversation = ConversationChain(memory=memory, llm=client)

    # Get the response from the model
    response = conversation.predict(input=input_text)
    return response

# Function to call the OpenAI ChatGPT model
def call_chatgpt_model(input_text, model="gpt-4o-mini"):
    """
    Calls the OpenAI ChatGPT model with the given input text and model.
    Returns the response from the model.
    """
    client = OpenAI()

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"You are a helpful assistant. {input_text} Do not wrap the json codes in JSON markers"
            }
        ]
    )
    response = completion.choices[0].message.content
    return response

# Function to call the OpenAI ChatGPT model with JSON output
def call_chatgpt_model_with_json(input_text, model="gpt-4o-mini"):
    """
    Calls the OpenAI ChatGPT model with the given input text and model, expecting JSON output.
    Returns the response from the model.
    """
    client = OpenAI()

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"You are a helpful assistant. {input_text} Do not wrap the json codes in JSON markers"
            }
        ]
    )
    response = completion.choices[0].message.content
    return response

# Function to call the local Ollama model
def local_llm_output(input_text, model):
    """
    Calls the local Ollama model with the given input text and model.
    Returns the response from the model.
    """
    response = ollama.chat(model=model, messages=[
        {
            'role': 'user',
            'content': f'{input_text}' + "Do not wrap the json codes in JSON markers",
        },
        ])
    return response['message']['content']

# Function to call the local Ollama model
def local_llm_with_history(input_text, prompt,history,model):
    """
    Calls the local Ollama model with the given input text and model.
    Returns the response from the model.
    """
    history = ChatMessageHistory()

    chat = ChatOllama(model=model)
    print(model)
    # Extract only AI messages
    #ai_messages = [msg for msg in history.messages if isinstance(msg, HumanMessage)]
    previous_response  = ""
    ## Print extracted AI messages
    #for ai_msg in ai_messages:
     #   previous_response = previous_response + "\n" + ai_msg.content
    
    prompt = (prompt
                + " You must always consider the full user input exactly as it is provided, without summarizing it. "
                + "Maintain chat history to provide accurate and contextual responses."
                    )
    prompt = ChatPromptTemplate(
                                [
                                    (
                                        "system",
                                        f"{prompt}",
                                    ),
                                    MessagesPlaceholder(variable_name="chat_history"),
                                    ("human","{input}"),
                                ]
                            )

    chain = prompt | chat
    chain_with_message_history = RunnableWithMessageHistory(
                                chain,
                                lambda session_id: history,
                                input_messages_key="input",
                                history_messages_key="chat_history",
                                )
    input_data = previous_response + input_text
    print("-"*100)
    print(input_data)
    print("-"*100)
    response = chain_with_message_history.invoke(
                        {"input": input_data},
                        {"configurable": {"session_id": "unused"}},
                                )
    #print(history)
    return response.content
# Function to call the local Ollama model with schema-based output
def local_llm_output_wth_schema(input_text, schema, model):
    """
    Calls the local Ollama model with the given input text, schema, and model.
    Validates the response against the schema and returns the validated data.
    """
    response = ollama.chat(
                      messages=[
                        {
                          'role': 'user',
                          'content':  f'{input_text}',
                        }
                      ],
                      model=model,
                      format=schema.model_json_schema(),
                    )

    account_details = schema.model_validate_json(response['message']['content'])

    return account_details

# Agent class to handle interactions with models
class Agent:
    def __init__(self, query, model,history, openai_flag=False):
        """
        Initializes the Agent with a query, model, and a flag indicating if OpenAI model should be used.
        """
        self.query = query
        self.model = model
        self.is_openai = openai_flag
        self.history = history

    def _call_model(self, input_text,prompt):
        """
        Calls the appropriate model based on the openai_flag.
        """
        if self.is_openai:
            print("Calling OpenAI LLM")
            return call_chatgpt_model(input_text, self.model)
        else:
            print("Calling Local LLM")
            return local_llm_with_history(input_text, prompt,self.history, self.model)

    def _call_model_with_schema(self, input_text, schema):
        """
        Calls the appropriate model with schema-based output based on the openai_flag.
        """
        #print(self.is_openai)
        if self.is_openai:
            return "OpenAI model does not support schema-based output."
        else:
            return local_llm_output_wth_schema(input_text, schema, self.model) 


    def summary_agent(self):
        """
        Creates a summary response based on the input response.
        """
        prompt = """You are an AI agent for Help channel query related to Fraud Guard and SMS PP ( SMS Pumping protection ) product for Twilio 
                    Your task is to crerate short Summarize from the user input and
                     extract all the  relevant information like detailed around account sid, country, Product impact, Issue, Customer impact etc.. in short.  """
        summary_response = self._call_model(str(self.query),prompt)
        
        return summary_response
 
        
    def fgagent1(self):
        """
        Handles the interaction with the model for extracting account information.
        """
        prompt = """ You are an AI agent tasked with analyzing customer queries to extract specific details. Your goal is to identify and extract the following information if present in the query.

                    Extraction Criteria:
                        1. Account Sid → An alphanumeric string starting with AC* , also known as account or account id or account sid. 
                        2. Country → List of country names mentioned in the text
                        3. MCC (Mobile Country Code) → List of country codes present in the text
                        4. MNC (Mobile Network Code) → List of mobile carrier identifiers found in the text
                        5. MCC-MNC → List of country-carrier code combinations if mentioned
                        6. Date → Any date or month present in the text
                        7. Error Code → A 5-digit numeric error code (e.g., 60410, 30450, 30453, 30454)
                    Response Format:
                        Return extracted values in the below JSON format. If a field is not present in the query, return None or an empty list [].

                    Example Output:
                    ✅ If all values are found:
                        {{
                        "account_sid": "AC123456789",
                        "Country": ["United States", "Canada"],
                        "MCC": ["310", "405"],
                        "MNC": ["260", "12"],
                        "MCC-MNC": ["310-260", "405-12"],
                        "date": ["January 2024"],
                        "error_code": ["60410"]
                        }}
                    ✅ If only some values are found:
                        {{
                        "account_sid": "AC987654321",
                        "Country": [],
                        "MCC": ["310"],
                        "MNC": [],
                        "MCC-MNC": [],
                        "date": ["March 2023"],
                        "error_code": []
                        }}
                    ✅ If nothing is found:
                        {{
                        "account_sid": null,
                        "Country": [],
                        "MCC": [],
                        "MNC": [],
                        "MCC-MNC": [],
                        "date": [],
                        "error_code": []
                        }}
                    Instructions:
                        Return only the JSON output—no additional text or explanations.

                   """
        #json_structure = """{{"account_sid":"" , "Country":[] , "date": [], "error_code":[] }}"""
                                                        
        query = "Query : " + self.query

        prompt = prompt #+ json_structure 
        input_text = query.strip()
        agent_response = self._call_model(input_text,prompt)
        return agent_response
    
    def fgagent2(self):
        """
        Handles the interaction with the model for identifying product information.
        """
        prompt = """ You are an AI agent tasked with analyzing customer queries to extract product-related information. 
                  Your goal is to determine whether the query is related to any of the following products and return the result in a structured format.

                            Products and Identifiers:
                            1. Fraud Guard → Keywords: "Verify", "Fraud Guard", "Standard mode", "Max mode", "Basic mode", Error code: 60410
                            2. SMS PP (SMS Pumping Protection) → Keywords: Error code: 30450, "api.dsg.smspumpingprotection.enable", "Pumping Protection", "Programmable SMS", "SMS PP"
                            3. Shadow Mode → Keywords: Error code: 30453, "api.dsg.smspumpingprotection.shadowmode", "shadow mode
                            4. Algo mode  → Keywords: api.dsg.algomode
                            Response Format:
                            If any product is identified in the query, return its name(s) in a JSON format. If no product is detected, return an empty array.

                            Example Output:
                            If "Fraud Guard" is detected:
                            {{"result": ["Fraud Guard"]}}
                            If "Fraud Guard" and "SMS PP" are detected:
                            {{"result": ["Fraud Guard", "SMS PP"]}}
                            If no matching product is found:
                            {{"result": []}}
                            Instructions:
                            Extract product names based on keywords and error codes.
                            Return only the JSON output without any additional explanation.
                        Query : 
                 """
        agent_response = self._call_model(self.query,prompt)
        return agent_response


    def fgagent3(self):
        """
        Handles the interaction with the model for categorizing issues.
        """
        prompt = """You are an AI agent responsible for analyzing customer queries and categorizing the problem based on predefined categories.  
                    Your task is to:  
                    1. Understand the issue described in the query.  
                    2. Match it with the most relevant category from the list below.  
                    3. If multiple categories apply, include all relevant ones.  
                    4. If no suitable category is found, return "Others".  
                    
                    ### **Categories:**  
                    1. **Enablement** – Queries related to Fraud Guard or SPP enablement, mode settings (e.g., date of enablement, mode enabled, history of modes).  
                    2. **SafeList** – Issues with adding or removing numbers from the safelist.  
                    3. **Risk Check** – Issues related to enabling or using risk check.  
                    4. **False Negative** – Fraud detection failures (e.g., missed fraud, low conversion rate, high volume of messages passing through).  
                    5. **False Positive** – Genuine messages being blocked (e.g., customers reporting blocked messages).  
                    6. **Refund** – Requests for credit memo, refunds due to missed fraud, or SMS PP charge refunds.  
                    7. **Billing** – Issues related to pricing or billing discrepancies.  
                    8. **60410** – High volume of 60410 detected in Fraud Guard, requests for unblocking 30453 filtering, refund requests for blocked messages.  
                    9. **30450** – High volume of 30450 detected in SPP.  
                    10. **30453** – High volume of 30453 detected, unblocking 30453 filtering, refund requests for blocked messages.  
                    
                    ### **Response Format:**  
                    Your response should be in valid JSON format:  
                    ```json
                    {{
                      "Category": ["<Category Name(s)>"],
                      "reason": "<Concise reason extracted from query>"
                    }}                
                     """
        agent_response = self._call_model(self.query,prompt)
        return agent_response
    
    def fgagent4(self,query):
        """
        Handles the interaction with the model for categorizing issues.
        """
        prompt = """You are an AI agent responsible for analyzing customer queries and categorizing the problem based on predefined categories.  
                    Your task is to:  
                    1. Understand the issue described in the query.  
                    2. Match it with the most relevant category from the list below.  
                    3. If multiple categories apply, include all relevant ones.  
                    4. If no suitable category is found, return "Others".  
                    
                    ### **Categories:**  
                    1. **Enablement** – Queries related to Fraud Guard or SPP enablement, mode settings (e.g., date of enablement, mode enabled, history of modes).  
                    2. **SafeList** – Issues with adding or removing numbers from the safelist.  
                    3. **Risk Check** – Issues related to enabling or using risk check.  
                    4. **False Negative** – Fraud detection failures (e.g., missed fraud, low conversion rate, high volume of messages passing through).  
                    5. **False Positive** – Genuine messages being blocked (e.g., customers reporting blocked messages).  
                    6. **Refund** – Requests for credit memo, refunds due to missed fraud, or SMS PP charge refunds.  
                    7. **Billing** – Issues related to pricing or billing discrepancies.  
                    8. **60410** – High volume of 60410 detected in Fraud Guard, requests for unblocking 30453 filtering, refund requests for blocked messages.  
                    9. **30450** – High volume of 30450 detected in SPP.  
                    10. **30453** – High volume of 30453 detected, unblocking 30453 filtering, refund requests for blocked messages.  
                    
                    ### **Response Format:**  
                    Your response should be in valid JSON format:  
                    ```json
                    {{
                      "Category": ["<Category Name(s)>"],
                      "reason": "<Concise reason extracted from query>"
                    }}                
                     """
        agent_response = self._call_model(query,prompt)
        return agent_response

    def json_response_agent(self,response,schema):
        """
        Handles the interaction with the model for schema-based output.
        """
        if self.model == 'deepseek-r1:14b':
            next_query = response.split("</think>")[1].split()
        else:
            next_query = response
        self.model = ollama_models[2]
        self.is_openai = False
        prompt = """Just extract data from a given Query  in the json format and replace null with None"""
        agent_response = self._call_model_with_schema(prompt + str(next_query), schema)
        
        return agent_response
    
    def response_framer_agent(self,response):
        """
        Processes the response from the model and returns the final response.
        """
        prompt = """ Just get data from different agent and create a response is anything is Null and not none ignore, 
                    If you do not find accont_sid, Please ask customer to prodive, 
                    If you are not able to understand Issue from Agent 3 , ask specific detail to explain little more in detail what exactly is customer issue. 
                    Only if Agent 3 response is Others or null
                """
        self.model = ollama_models[2]
        self.is_openai = False
        agent_response = self._call_model(str(response),prompt )
        
        return agent_response

    def final_response_agent(self, response):
        """
        Processes the response from the model and returns the final response based on the issue reason.
        """
        prompt = """Based on the issue reason, create a short response. If the account_sid is not found, ask the customer to provide it. 
                    If the issue from Agent 3 is not understood, ask for specific details to explain the customer's issue in more detail. 
                    This is only applicable if Agent 3's response is 'Others' or null.

                    If Agent 3 reponse is related to : 
                        **SafeList** – Issues with adding or removing numbers from the safelist.  
                        Answer : Use Safelist API (https://www.twilio.com/docs/usage/global-safe-list) to safe list phone numbers and if you need help in bulk update. Please message #help-growth-user-intelligence and 
                                and tag @demand-dsg-pd to help you with. 
                        **Risk Check** – Issues related to enabling or using risk check.  
                            Answer : Follow this link (https://www.twilio.com/docs/messaging/features/sms-pumping-protection-programmable-messaging#riskcheck-parameter) to use Risk check parameter. Please message #help-growth-user-intelligence and 
                                and tag @demand-dsg-pd to help you with more details.
                        **False Negative** – Fraud detection failures (e.g., missed fraud, low conversion rate, high volume of messages passing through).
                        Answer :We are looking into Issue Please message #help-growth-user-intelligence and 
                                and tag @demand-dsg-data-pd to help you with more details.
                        **False Positive** – Genuine messages being blocked (e.g., customers reporting blocked messages). 
                        Answer :We are looking into Issue Please message #help-growth-user-intelligence and 
                                and tag @demand-dsg-data-pd to help you with more details. Meanwhile we request you to use Safelist for 
                                Verify and Risk check parameter for SPP solution to avoid more FP. 
                        **Refund** – Requests for credit memo, refunds due to missed fraud, or SMS PP charge refunds.  
                        Answer : For refund related questions please write to #help-sms-pumping-credit-memos. 
                        **Billing** – Issues related to pricing or billing discrepancies.  
                        Answer :For billing related questions please write to #help-sms-pumping-credit-memos
                        **60410** – High volume of 60410 detected in Fraud Guard, requests for unblocking 30453 filtering, refund requests for blocked messages. 
                        **30450** – High volume of 30450 detected in SPP.  
                        **30453** – High volume of 30453 detected, unblocking 30453 filtering, refund requests for blocked messages.
                        Answer :We are looking into Issue Please message #help-growth-user-intelligence and 
                                and tag @demand-dsg-data-pd to help you with more details. Meanwhile we request you to use Safelist for 
                                Verify and Risk check parameter for SPP solution to avoid more False Positive. 

                        Provide a very small 2 line Answer to the customer based on above details.  
                """
        #self.model = ollama_models[2]
        #self.is_openai = False
        agent_response = self._call_model(response, prompt)
        
        return agent_response