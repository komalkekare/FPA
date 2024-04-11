# This is the overall chain where we run these two chains in sequence.
from langchain.chains import SimpleSequentialChain
from querycheckchain import querycheckfunc
from ExecutorChain import QueryExecutorChain
from custom_sql_query import SQLAgent
from database_test import similarity_search
from database_test import create_embeddings
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# create_embeddings()
@app.route('/execute-fpa-python', methods=['POST'])
def execute_source_python():
    try:
        # query = "What are the total gross margin of subsidiaries by name?"
        data = request.get_json()
        query = data.get('query')
        memory = data.get('memory')

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

if __name__ == '__main__':
    app.run(debug=True)
