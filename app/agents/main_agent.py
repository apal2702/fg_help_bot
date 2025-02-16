from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ChatMessageHistory
#from langchain.memory import ConversationBufferMemory
from app.agents.fg_agents import Agent, Account, Issue, Product
from app.agents.presto_query_agent import AccountInfo
# Global dictionary
global_dict = {}

## Check Account SID
def check_account_sid_format(account_sid):
    if account_sid.startswith("AC"): #len(account_sid) == 34 
        return True
    else:
        return False
    
def decode_product(product_list):
    """
    # 1. Fraud Guard: Verify, Fraud Guard, Standard mode, max mode, basic mode, error code 60410
    # 2. SMS PP: Error code: 30450, api.dsg.smspumpingprotection.enable, pumping protection 
    # 3. Shadow mode: if Error code: 30453 , api.dsg.smspumpingprotection.shadowmode
    # 4. Algo mode: api.dsg.algomode
    """
    result = []
    for product in product_list:
        if any(keyword in str(product).lower() for keyword in ["1", "fraud guard", "fg", "guard", "fraud", "fraudguard", 'verify']):
            result.append("Fraud Guard")
        elif any(keyword in str(product).lower() for keyword in ["2", "sms pp", "pp", "pumping", "sms", "sms pumping protection"]):
           result.append("SMS PP")
        elif any(keyword in str(product).lower() for keyword in ["3", "shadow mode", "shadow", "shadowmode"]):
            result.append("Shadow mode")
        elif any(keyword in str(product).lower() for keyword in ["4", "algo mode", "algo", "algomode"]):
            result.append("Algo mode")
    return result

def decode_issue(response):
    """
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
    """
    # Using comments to create if-else logic for issue decoding

    # 1. Enablement related (date of enablement, mode enabled, history of modes)
    if "1" in str(response).lower() or "enablement" in str(response).lower() or "date of enablement" in str(response).lower() or "mode enabled" in str(response).lower() or "history of modes" in str(response).lower():
        return "Enablement related"
    # 2. Add/delete numbers to/from safelist
    elif "2" in str(response).lower() or "add" in str(response).lower() or "delete" in str(response).lower() or "numbers" in str(response).lower() or "safelist" in str(response).lower():
        return "Add/delete numbers to/from safelist"
    # 3. Missed detecting fraud
    elif "3" in str(response).lower() or "missed" in str(response).lower() or "detecting" in str(response).lower() or "fraud" in str(response).lower():
        return "Missed detecting fraud"
    # 4. blocked genuine messages or customers
    elif "4" in str(response).lower() or "blocked" in str(response).lower() or "genuine" in str(response).lower() or "messages" in str(response).lower() or "customers" in str(response).lower():
        return "Blocked genuine messages or customers"
    # 5. Requesting Credit Memo Or refund for missed fraud
    elif "5" in str(response).lower() or "requesting" in str(response).lower() or "credit memo" in str(response).lower() or "refund" in str(response).lower() or "missed fraud" in str(response).lower():
        return "Requesting Credit Memo Or refund for missed fraud"
    # 9. pricing or billind related issue
    elif "9" in str(response).lower() or "pricing" in str(response).lower() or "billind" in str(response).lower() or "related issue" in str(response).lower():
        return "Pricing or billind related issue"
    # 10. Off boarding request & refund of SMS PP charges
    elif "10" in str(response).lower() or "off boarding" in str(response).lower() or "refund" in str(response).lower() or "sms pp" in str(response).lower() or "charges" in str(response).lower():
        return "Off boarding request & refund of SMS PP charges"
    # 11. High volume of 30450 detected
    elif "11" in str(response).lower() or "high volume" in str(response).lower() or "30450" in str(response).lower() or "detected" in str(response).lower():
        return "High volume of 30450 detected"
    # 12. Add numbers to safelist, Problems with adding numbers to safelist
    elif "12" in str(response).lower() or "add numbers" in str(response).lower() or "safelist" in str(response).lower() or "problems" in str(response).lower() or "adding numbers" in str(response).lower():
        return "Add numbers to safelist, Problems with adding numbers to safelist"
    # 13. How to enable riskcheck, risk check related issue.
    elif "13" in str(response).lower() or "how to enable" in str(response).lower() or "riskcheck" in str(response).lower() or "risk check" in str(response).lower() or "related issue" in str(response).lower():
        return "How to enable riskcheck, risk check related issue."
    # 14. Unblocking of 30453 filtering & refund request for blocked messages
    elif "14" in str(response).lower() or "unblocking" in str(response).lower() or "30453" in str(response).lower() or "filtering" in str(response).lower() or "refund request" in str(response).lower() or "blocked messages" in str(response).lower():
        return "Unblocking of 30453 filtering & refund request for blocked messages"
    # 15. High volume of 30453 detected
    elif "15" in str(response).lower() or "high volume" in str(response).lower() or "30453" in str(response).lower() or "detected" in str(response).lower():
        return "High volume of 30453 detected"
    else:
        return "Others"

@tool
def help_channel_agent(query, model, demo_ephemeral_chat_history_for_chain, flag):
    """Call different Agents for help channel related Query"""
    print("Hi, I will look into this query. Please wait...")
    if model in ['gpt-4o-mini', 'gpt-3.5-turbo-0125']:
        flag = True

    agent = Agent(query, model, demo_ephemeral_chat_history_for_chain, openai_flag=flag)
    agent_responses = get_agent_responses(agent)
    json_responses = convert_responses_to_json(agent,agent_responses)
    response = format_response(json_responses)

    account_check = check_account_sid_format(json_responses['agent1_json_response'].account_sid)
    product_info = decode_product(json_responses['agent2_json_response'].result)


    final_response = "Summary: " + agent_responses['summart_agent_response'] + "\n\n" + response
    #issue_category_info = decode_issue(json_responses['agent3_json_response'].category)
    ## Get Data from Presto If Account SID is present - 
    #get_account_info(account_check, json_responses)

    #account_sid_details = get_account_sid_details(account_check, json_responses['agent1_json_response'].account_sid)
    #product_details = get_product_details(product_info)
    #issue_details = get_issue_details(issue_category_info, json_responses['agent3_json_response'].reason)
    #final_response = generate_final_response(account_sid_details, product_details, issue_category_info)

    return final_response

## Get Data from Presto If Account SID is present - 
def get_account_info(account_check, json_responses):
    if account_check:
        account_sid = str(json_responses['agent1_json_response'].account_sid).strip()
        country = json_responses['agent1_json_response'].country
        mcc = json_responses['agent1_json_response'].mcc
        print("#"*100)
        print(f"account_sid:{account_sid} , country : {country}, mcc:{mcc}")
        acc_info_obj = AccountInfo(account_sid, country, mcc)
        acc_info_obj.get_account_info()

def get_agent_responses(agent):
    summart_agent_response = agent.summary_agent()  
    agent1_response = agent.fgagent1()
    agent2_response = agent.fgagent2()
    agent3_response = agent.fgagent3()
    agent4_response = agent.fgagent4(summart_agent_response)
    return {
        'summart_agent_response': summart_agent_response,
        'agent1_response': agent1_response,
        'agent2_response': agent2_response,
        'agent3_response': agent3_response,
        'agent4_response': agent4_response
    }

def convert_responses_to_json(agent,agent_responses):
    agent1_json_response = agent.json_response_agent(agent_responses['agent1_response'], Account)
    agent2_json_response = agent.json_response_agent(agent_responses['agent2_response'], Product)
    agent3_json_response = agent.json_response_agent(agent_responses['agent3_response'], Issue)
    agent4_json_response = agent.json_response_agent(agent_responses['agent4_response'], Issue)
    return {
        'agent1_json_response': agent1_json_response,
        'agent2_json_response': agent2_json_response,
        'agent3_json_response': agent3_json_response,
        'agent4_json_response': agent4_json_response
    }

def format_response(json_responses):
    response = f"""Agent 1: {json_responses['agent1_json_response']} ,
                    Agent 2: {json_responses['agent2_json_response']} ,
                    Agent 3: {json_responses['agent3_json_response']} ,
                    Agent 4: {json_responses['agent4_json_response']} """
    
    return response

def get_account_sid_details(account_check, account_sid):
    if account_check:
        return f"The Account for which you are facing issue is - Account SID : {account_sid}"
    else:
        return "Account SID is missing, can you please Account sid for which you are having issue."

def get_product_details(product_info):
    if product_info is not []:
        return f"Issue is related to Product : {product_info}"
    else:
        return "Product details are missing can you please share more details around it."

def get_issue_details(issue_category_info, issue_reason):
    if issue_category_info is not None:
        return f"Issue is : {issue_category_info} \n - Reason : {issue_reason}"
    else:
        if "Others" in issue_category_info:
            return f"Issue - Not able to debug  \n - Reason : {issue_reason}"
        else:
            return f"Issue is : {issue_category_info} \n - Reason : {issue_reason}"

def generate_final_response(account_sid_details, product_details, issue_details):
    final_response = f"""Hi, Thanks for sharing your Query. I will try my best to get more details around your issue
      \n From above query I was able to detect that 
        \n 1. {account_sid_details} 
        \n 2. {product_details} 
        \n 3. {issue_details} \n
        """
    return final_response


@tool
def general_chat_agent(query: str) -> str:
    """General Chat, Like hi, hello"""
    print("Hi, I will assist you today.")
    return "Hi, I am GUI Help Channel BOT SAAST AI. How can I assist you today? Please provide your query."

@tool
def get_details_from_presto(query: str) -> str:
    """Get more details from Presto"""
    print("Cool, We are working on it")
    print()
    #updated_info = update_memory({query + "Cool, We are working on it" })
    #print(updated_info)
    #with open('response_data.txt', 'r') as file:
    #    return file.read()
        
    return ("Cool, We are working on it")


class MainAgent:
    def __init__(self, question: str, llm_model: str,history,demo_ephemeral_chat_history_for_chain):
        self.history = history
        self.demo_ephemeral_chat_history_for_chain = demo_ephemeral_chat_history_for_chain   
        self.question = question
        self.llm_model = llm_model
        if llm_model in ('deepseek-r1:14b','gpt-4o-mini', 'gpt-3.5-turbo-0125'):
            llm_model = 'llama3.1'
        self.model = ChatOllama(model=llm_model)

    def process_query(self):
        tools = [help_channel_agent, general_chat_agent,get_details_from_presto]
        
        model_with_tools = self.model.bind_tools(tools)
        prompt = ChatPromptTemplate.from_template(
                        """
                        You are an AI assistant responsible for handling user queries efficiently by selecting the appropriate tool.

                        **Tool Selection Criteria:**
                        - Use **'general_chat_agent'** if the query is a general conversation or assistance request **not related** to a specific customer concern.
                        - Use **'help_channel_agent'** if the query is related to a specific **customer help channel request** and if it is to provide relevant information for input query.
                        - Use **'get_details_from_presto'** if the query is a **response to the last message** and it is confimration (e.g., confirmations like "correct," "confirm," "yes," etc 
                         
                         **Note:** Ensure that user-provided information (like account sid, updates, or corrections) trigger the 'help_channel_agent' tool only.

                        **User Query:**  
                        {question}
                        """
                    )
        
        qa_rag_chain = prompt | model_with_tools
        #print(self.question)
        #print(len(self.question))
        response = qa_rag_chain.invoke({'question': self.question, "chat_history": self.history})
        print(response)
        if response.tool_calls:
            tool_call_map = {
                'help_channel_agent': help_channel_agent,
                'general_chat_agent': general_chat_agent,
                'get_details_from_presto': get_details_from_presto
            }
            tool_call = response.tool_calls[0]
            selected_tool = tool_call_map.get(tool_call["name"].lower())
            
            if selected_tool:
                print(f"Calling tool: {tool_call['name']}")
                tool_args = tool_call["args"]
                if tool_call["name"] == "help_channel_agent":
                    tool_args["query"] = self.question  # Pass LLM model name
                    tool_args["model"] = self.llm_model  # Pass LLM model name
                    tool_args["flag"] = False  # Example flag value
                    tool_args["demo_ephemeral_chat_history_for_chain"] = self.demo_ephemeral_chat_history_for_chain  # Example flag value
                tool_output = selected_tool.invoke(tool_call["args"])
                #print(tool_output)
                return tool_output
        
        return "I'm unable to process your request at the moment."
