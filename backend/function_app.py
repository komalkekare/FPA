import azure.functions as func
import logging
from langchain.chains import SimpleSequentialChain
from querycheckchain import querycheckfunc
from ExecutorChain import QueryExecutorChain
from custom_sql_query import SQLAgent
from database_test import similarity_search
from database_test import create_embeddings
from flask import Flask, request, jsonify
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# @app.route(route="fpa")
# def fpa(req: func.HttpRequest) -> func.HttpResponse:
#     logging.info('Python HTTP trigger function processed a request.')

#     name = req.params.get('name')
#     if not name:
#         try:
#             req_body = req.get_json()
#         except ValueError:
#             pass
#         else:
#             name = req_body.get('name')

#     if name:
#         return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
#     else:
#         return func.HttpResponse(
#              "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
#              status_code=200
#         )

@app.route(route="fpa_backend", methods=['POST'])
def fpa_backend(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # query = "What are the total gross margin of subsidiaries by name?"
        # data = request.get_json()
        query = req.params.get('query')
        memory = req.params.get('memory')

        print(query, memory)

        tables = create_embeddings(query)

        sql_chain  = SQLAgent(tables)
        querycheckchain=querycheckfunc(tables)

        executorchainobj=QueryExecutorChain(user_query=query)
        # executorchainobj.user_query = query
        overall_chain = SimpleSequentialChain(chains=[sql_chain, querycheckchain, executorchainobj], 
                                            verbose=True
                                            )
        answer = overall_chain.run(query)
        print(answer)
        response = {"answer": answer}
        return jsonify(response)
    except Exception as e:
        print(f"Error: {e}")
        response = {"answer":"Sorry, We could not retrieve any information for this query. Please try again with detailed question."}
        # return jsonify({"error": str(e)})
        return response

@app.route(route="fpa", auth_level=func.AuthLevel.ANONYMOUS)
def fpa(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )