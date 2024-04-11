import os
from flask import Flask, request, jsonify
from langchain.vectorstores import Chroma
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.callbacks.stdout import StdOutCallbackHandler
from langchain.document_loaders import DirectoryLoader
from custom_sql_query import SQLAgent
from langchain.agents import AgentExecutor


# app = Flask(__name__)
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
# llm=OpenAI(model_name='gpt-3.5-turbo-16k-0613')
# toolkit = SQLDatabaseToolkit(db=db, llm=llm, reduce_k_below_max_tokens=True)
# agent_executor = create_sql_agent(
#     llm=llm,
#     toolkit=toolkit,
#     verbose=True
# )

def create_embeddings(query):
    global db
    text = DirectoryLoader(f'table_structures', glob="./*.txt")
    text_documents = text.load()
    db = Chroma.from_documents(text_documents, embedding_function)
    tables = similarity_search(query)
    return tables

# db = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)


def similarity_search(query):
    docs = db.similarity_search(query)
    tables=[]
    for table in docs:
        tables.append(table.page_content)
        print(table.metadata)
    return tables


# sql_query = SQLAgent(tables)

# agent,tools=SQLAgent(tables)
# agent_executor=AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)
# print(agent_executor.run(query))
# @app.route('/dbtest',methods=["POST"])
# def processdocs():
#     try:
#         input_json = request.get_json(force=True)
#         query = input_json["query"]
#         print(input_json)
#     except:
#         return jsonify({"Status":"Failure --- Something Unexpected Happened"})
#     output_json = agent_executor.run(query)
#     print(output_json)
#     return output_json

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=8091, debug=False)