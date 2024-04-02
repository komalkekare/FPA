from langchain.chains.base import Chain
from pydantic import Extra
from typing import Any, Dict, List, Optional
from langchain.callbacks.manager import CallbackManagerForChainRun
import pyodbc
from langchain.chat_models.openai import ChatOpenAI
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

import os
os.environ['OPENAI_API_KEY']='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'

class QueryExecutorChain(Chain):
    input_key: str = "query"
    output_key: str = "text"
    user_query:str=""

    class Config:
        extra = Extra.forbid
        arbitrary_types_allowed = True
    
    @property
    def input_keys(self) -> List[str]:
        return [self.input_key]
    
    @property
    def output_keys(self) -> List[str]:
        """Will always return text key.

        :meta private:
        """
        return [self.output_key]

    def _call(self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None
    )-> Dict[str, Any]:
        intermediate_steps: List = []
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        _run_manager.on_text(inputs['query'], color="green", verbose=self.verbose)
        intermediate_steps.append(
                    inputs['query']
                ) 
        intermediate_steps.append({"sql_cmd": inputs['query']})
        # conn = (r'DRIVER={SQL Server};'
        # r'SERVER=(local)\SQLEXPRESS;'
        # r'DATABASE=myDb;'
        # r'Trusted_Connection=yes;')

        cnxn= pyodbc.connect(f'Driver={{ODBC Driver 17 for SQL Server}};'
                             f'Server=tcp:brl-bi-sqldb-stage.database.windows.net,1433;'
                             f'Database=insightsdbdevnew;'
                             f'TrustServerCertificate=yes;'
                             f'Connection Timeout=30;'
                             f'Authentication=ActiveDirectoryIntegrated')
        # cnxn= pyodbc.connect('Driver={ODBC Driver 17 for SQL Server};Server=tcp:brl-bi-sqldb-stage.database.windows.net,1433;Database=insightsdbdevnew;Uid=komal.kekare@brillio.com;Pwd=BuddyMeddi@2023;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;Authentication=ActiveDirectoryPassword')
        # cnxn = pyodbc.connect(connection_string)
        db=cnxn.cursor()
        db.execute(inputs['query'])
        results=db.fetchall()
        intermediate_steps.append(str(results))
        _run_manager.on_text("\nResult from database:"+str(results), color="green", verbose=self.verbose)
        # print(inputs)
        prompt="""You are a formatting expert, I will give you a question and a result from a database which contains the answer.
        Format the result in a human readable way.
        Question: """
        prompt+=self.user_query
        prompt+="""\nResult from Database: """
        prompt+=str(results)
        prompt+="""\nFormatted Answer: """
        _run_manager.on_text(str(prompt), color="green", verbose=self.verbose)
        
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613")
        answer=llm([HumanMessage(content=prompt)])
        _run_manager.on_text(str(answer), color="green", verbose=self.verbose)
        return {self.output_key:answer.content}
    
    @property
    def _chain_type(self) -> str:
        return "query_executor_chain"
    

# db_chain = QueryExecutorChain(verbose=True)

# print(db_chain.run(query="select sum(net_revenue) from [denorm].[fact_transaction_kpi]"))