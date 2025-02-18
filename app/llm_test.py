import ollama
import json
from pydantic import BaseModel
from openai import OpenAI
import requests
import os
import streamlit as st
from langchain.memory import ChatMessageHistory
from app.agents.fg_agents import Agent , local_llm_with_history, call_chatgpt_model

os.environ['OPENAI_API_KEY'] = 'sk-proj-lhm1tMlkwAXI'
ollama_models = ['deepseek-r1', 'llama3.1', 'mistral']
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

def call_chatgpt_model(input_text, model="gpt-4o-mini"):
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


def call_chatgpt_model_with_json(input_text, model="gpt-4o-mini"):
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
def local_llm_output(input_text,model):
    response = ollama.chat(model=model, messages=[
        {
            'role': 'user',
            'content': f'{input_text}' + "Do not wrap the json codes in JSON markers",
        },
        ])
    return response['message']['content']

def local_llm_output_wth_schema(input_text,schema,model):
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

class Agent1:
    def __init__(self, query, model,openai_flag = False):
        self.query = query
        self.model = model
        self.is_openai = openai_flag

    def _call_model(self, input_text):
        if self.is_openai == True:
            return call_chatgpt_model(input_text,self.model)
        else:
            return local_llm_output(input_text, self.model)

    def _call_model_with_schema(self, input_text, schema):
        if self.is_openai == True:
            return "OpenAI model does not support schema-based output."
        else:
            return local_llm_output_wth_schema(input_text, schema, self.model)
        
    def summary_agent(self,query):
        """
        Creates a summary response based on the input response.
        """
        prompt = """Summarize the response to include all relevant details."""
        summary_response = self._call_model(prompt + str(query))
        
        return summary_response    
    def agent1(self):
        prompt = """ You are an AI agent given below customer query extract below information from it. 
                        1. Account  Sid : It is an Alpa numeric number starts with AC* 
                        2. Country: A country name
                        3. MCC:  A country code 
                        4. MNC :  a country carrie
                        5. MCC-MNC: Country carrier code
                        6. Date: A date or month 
                        7. Error code: this is the error code which will be something like 60410 ,30450, 30453,30454 etc… a numeric number of length 5 digit. 
                            Extract all this in below json schema and if not present keep it None.
                            result  = {"account_sid": , "Country": , "date":, "error_code": }
                            Just follow json schema and no text before and after
                            json_structure: {json_structure}
                            """
        json_structure = """{{"account_sid":"" , "Country":"" , "date": "", "error_code":"" }}"""
                                                        
        query = "Query : " + self.query
        input_text = prompt + json_structure + query
        input_text = input_text.strip()
        agent_response = self._call_model(input_text)
        return agent_response
    
    def agent2(self):
        prompt = """
                    You are an AI agent given below customer query extract below information from it. 
                        Understand product whether it is 
                        1. Fraud Guard: Verify, Fraud Guard, Standard mode, max mode, basic mode, error code 60410
                        2. SMS PP: Error code: 30450, api.dsg.smspumpingprotection.enable, pumping protection 
                        3. Shadow mode: if Error code: 30453 , api.dsg.smspumpingprotection.shadowmode
                        4. Algo mode: api.dsg.algomode
                
                    If you are able to understand from text either one is present return that else return 0. 
                    Don’t give much explanation just return in below json format : 
                        {‘result’: }

                    Query : 
                 """
        agent_response = self._call_model(prompt + self.query)
        return agent_response


    def agent3(self):
        prompt = """
                     You are an AI agent given below customer query try to understand and categories the problem from below categories, If you are not able to detect return "Others"
                            1.  Enablement related (date of enablement, mode enabled, history of modes)
                            2.  Add/delete numbers to/from safelist
                            3.  Missed detecting fraud
                            4.  blocked genuine messages or customers
                            5.  Requesting Credit Memo Or refund for missed fraud
                            9.  pricing or billind related issue
                            10. Off boarding request & refund of SMS PP charges
                            11. High volume of 30450 detected
                            12. Add numbers to safelist, Problems with adding numbers to safelist
                            13. How to enable riskcheck, risk check related issue.
                            14. Unblocking of 30453 filtering & refund request for blocked messages
                            15. High volume of 30453 detected

                        Give answer in below json format- 
                        {"Category": , "reason":}
                     """
        agent_response = self._call_model(prompt + self.query)
        return agent_response

    def agent4(self,schema):
        prompt = """Just extract data from a given Query  in the json format and replace null with None"""
        agent_response = self._call_model_with_schema(prompt + self.query, schema)
        
        return agent_response

def run_agents(query):
    results = {}
    print("OpenAI")
    for model in openai_models:
        print("Model:", model)
        agent = Agent(query, model,openai_flag= True)
        results[model] = {
            'agent1': agent.agent1(),
            'agent2': agent.agent2(),
            'agent3': agent.agent3(),
            'agent4': "",
        }

    print("Ollama")
    for model in ollama_models:
        print("Model:", model)
        agent = Agent(query, model,openai_flag= False)
        results[model] = {
            'agent1': agent.agent1(),
            'agent2': agent.agent2(),
            'agent3': agent.agent3(),
            'agent4': agent.agent4(),
        }
    return results

def agent4_inaction(response, model,schema):
    if model == 'deepseek-r1:14b':
        next_query = response.split("</think>")[1].split()
    else:
        next_query= response
    agent = Agent(str(next_query), ollama_models[2],openai_flag = False)
    final_response = agent.agent4(schema)
    
    return final_response

def llm_test():
    #st.set_page_config(layout="wide")  # Increase overall size for window

    page = st.sidebar.selectbox(
        "Select a page",
            ["FG Agents Testing", "PromptTesting"] #"Threshold Override", "mlops_v2","mlops_v2_metrics"]
    )
    if page == "PromptTesting":
        st.title("Prompt Testing with different Model Comparison: ")
        prompt = st.text_area("Enter your Prompt:", height=100)  # Increase height for text input
        query_input = st.text_area("Enter your query:", height=100)  # Increase height for text input   

        model_select = st.multiselect("Select Models", ollama_models + openai_models)
        columns = st.columns(len(model_select) if model_select else 1)

        button = st.button("Run Agents")

        if button:
            history = ChatMessageHistory()
            for i, col in enumerate(columns):
                with col:
                    model = model_select[i]
                    
                    if model in ollama_models:
                        st.subheader("OLLAMA Model: ")
                        st.subheader(model,divider=True)
                        response = local_llm_with_history(query_input, prompt , history, model) 
                    elif model in openai_models:
                        st.subheader("CHATGPT Model: ")
                        st.subheader(model,divider=True)
                        response = call_chatgpt_model(prompt + query_input, model) 
                    st.write(response)

    elif page == "FG Agents Testing":
            
        st.title("FG Agent with Model Comparison: ")

        query_input = st.text_input("Enter your query:")  # Increase height for text input

        model_select = st.multiselect("Select Models", ollama_models + openai_models)
        columns = st.columns(len(model_select) if model_select else 1)

        button = st.button("Run Agents")

        if button:
            demo_ephemeral_chat_history_for_chain = ChatMessageHistory()
            for i, col in enumerate(columns):
                with col:
                    model = model_select[i]
                    
                    if model in ollama_models:
                        agent = Agent(query_input, model, demo_ephemeral_chat_history_for_chain,False)
                        st.subheader("OLLAMA Model: ") 
                    elif model in openai_models:
                        agent = Agent(query, model, demo_ephemeral_chat_history_for_chain,True)
                        st.subheader("CHATGPT Model: ") 
                    st.subheader(model,divider=True)

                    st.subheader("🤖 Summary Agent:")
                    summary_response = agent.summary_agent()
                    st.markdown(":red[Summary Agent tried to summarize the response to include all relevant details.] ")
                    st.write(summary_response)

                    ## Agent 1 Extract info and Send to Agent 4 to extract info - 
                    st.subheader("🤖 Agent 1:")
                    agent1_response = agent.fgagent1()    
                    st.markdown(":red[Agent 1 tried to extract meaningful info like Acc sid, Country, MCC_MNC, Date, Error Code etc..] ")
                    ## Pass this to another function extract info from it
                    extracted_fields = agent.json_response_agent(agent1_response,Account)
                    print(extracted_fields)
                    st.write("Account SID : " + extracted_fields.account_sid)
                    st.write("Country : " + str(extracted_fields.country))
                    st.write("DATE : " + str(extracted_fields.date))
                    st.write("MCC : " + str(extracted_fields.mcc))
                    st.write("Error Code : " + str(extracted_fields.error_code))

                    ## Agent 2 to extract Product
                    ## Agent 2 Extract info and Send to Agent 4 to extract info - 
                    st.subheader("🤖 Agent 2:")
                    agent2_response = agent.fgagent2()
                    st.markdown(":red[Agent 2 tried to detect Product] ")
                    ## Pass this to another function extract info from it
                    extracted_fields = agent.json_response_agent(agent2_response,Product)
                    print(extracted_fields)
                    st.write("Product:"+ str(extracted_fields.result))

                    ## Agent 3 to extract Product
                    ## Agent 3 Extract info and Send to Agent 4 to extract info - 
                    st.subheader("🤖 Agent 3:")
                    agent3_response = agent.fgagent3()
                    st.markdown(":red[Agent 3 tried to understand Issues] ")
                    ## Pass this to another function extract info from it
                    extracted_fields = agent.json_response_agent(agent3_response,Issue)
                    print(extracted_fields)
                    st.write("Category:" + str(extracted_fields.category))
                    st.write("Reason:" + str(extracted_fields.reason))

                    ## Take Action
                    ## Check Account SID
                    def check_account_sid_format(account_sid):
                        if len(account_sid) == 34 and account_sid.startswith("AC"):
                            return True
                        else:
                            return False