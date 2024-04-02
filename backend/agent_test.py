from langchain.agents import Tool
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from seqchain import sequentialchain
from analysis import analysis
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import MessagesPlaceholder
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.chat_models import AzureChatOpenAI
from langchain.llms import AzureOpenAI


from flask import Flask, request, jsonify

app = Flask(__name__)


import os
# os.environ['OPENAI_API_KEY']='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'

#For Azure Open AI
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-07-01-preview"
os.environ["OPENAI_API_BASE"] = "https://fpa-genai.openai.azure.com/"
os.environ["OPENAI_API_KEY"] = "be44f14be27a4e0d85be7a51f0e90d86"



agent_kwargs = {
    "extra_prompt_messages": [MessagesPlaceholder(variable_name="chat_history")],
}

from langchain import OpenAI, LLMMathChain

llm = AzureChatOpenAI(
    temperature=0,
    deployment_name="fpa-genai",
    model_name="gpt-35-turbo-16k",
    openai_api_base="https://fpa-genai.openai.azure.com/",
    openai_api_version="2023-07-01-preview",
    openai_api_key="be44f14be27a4e0d85be7a51f0e90d86",
    openai_api_type="azure")

llm_math = LLMMathChain.from_llm(llm=llm, verbose=True)


tools=[
    Tool.from_function(func=sequentialchain._run,
                    name="tool1",
                    description="Useful when user wants information about revenue, margin, employee and projects. Input is a descriptive plain text formed using user question and chat history and output is the result."
    ),
    # Tool(
    #     name="tool2",
    #     func=llm_math.run,
    #     description="Useful when you want to do some calculations using the result from tool1. Input is only a mathematical equation of numbers and output is result. DO not use this tool for statistical analysis.",
    # ),
    Tool.from_function(func=analysis._run,
                    name="tool2",
                    description="Useful when you want to do some calculations and statistical analysis using the memory. Input is a list of numbers with description of what is to be done to it or a mathematical equation of number and output is result."
    )
    ]

memory = ConversationBufferWindowMemory(memory_key="chat_history",return_messages=True,k=7)
llm = AzureChatOpenAI(
    temperature=0,
    deployment_name="fpa-genai",
    model_name="gpt-35-turbo-16k",
    openai_api_base="https://fpa-genai.openai.azure.com/",
    openai_api_version="2023-07-01-preview",
    openai_api_key="be44f14be27a4e0d85be7a51f0e90d86",
    openai_api_type="azure"
)
agent_chain=initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    agent_kwargs=agent_kwargs,
    memory=memory,
)


@app.route('/getanswer',methods=["POST"])
def processdocs():
    try:
        input_json = request.get_json(force=True)
        query = input_json["query"]
        messages=input_json["memory"]
        memory.clear()
        for chat in messages:
            memory.save_context(chat[0],chat[1])
        answer=agent_chain.run(query)
        return answer
    
    except:
        return "I am having trouble querying the database. Can you please break down your question into smaller chunks or reframe the question."
    
@app.route('/clearmemory',methods=["GET"])
def clearmem():
    try:
        memory.clear()
        return {"response":"memory cleared"}
    
    except:
        return {"response":"memory not cleared"}
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8091, debug=True)
