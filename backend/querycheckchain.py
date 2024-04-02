from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.callbacks.stdout import StdOutCallbackHandler
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.prompts import StringPromptTemplate
from typing import List, Union
from langchain.agents import Tool
from database_test import similarity_search

import os
os.environ['OPENAI_API_KEY']='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'


def querycheckfunc(table_meta):
# query = "select [PracticeName], sum(gross_margin) as total_margin from denorm.fact_transaction_kpi where period_date >= '2022-07-01' and period_date <= '2022-09-30' group by [Practice Name]"
  table_schemas=table_meta
  # table_schemas = similarity_search("Top regions in descending order by the difference in their total revenue and margins displayed with their revenues and margins")
  llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-16k-0613")
  template = """You are a helpful agent which fixes sql queries.
The fixes have to be according to the INSTRUCTIONS provided. 
Only give fixed sql query as output in plain text. Do not provide any explanations with it.

SQL Query- {query}

INSTRUCTIONS - 
- All Column Names in the query have to be placed inside [].
- Always type table name as 'denorm.<table_name>'. Example: 'select * from denorm.<table_name>'. Example denorm.dim_practice
- All Column Names mentioned in the query should be exactly present in the TABLE SCHEMAS provided. If the Column Names in the query are not exactly present in the TABLE SCHEMA of the relevant table, find the most similar Column Names in TABLE SCHEMA of the relevant table and substitute them in the query. Eg - For query "select [Region Name], (sum(revenue) - sum(gross_margin)) as revenue_margin_difference from denorm.fact_transaction_kpi join denorm.dim_region on denorm.fact_transaction_kpi.Region_sk = denorm.dim_region.Region_SK group by [Region Name] order by revenue_margin_difference desc" column Practice Name is not available in schema the. The most similar column name is practice_sk. The column name "revenue" is not available in the relevant TABLE SCHEMA(fact_transaction_kpi).The most similar column name available is "net_revenue". So the query after the fix is - select [Region Name], (sum(net_revenue) - sum(gross_margin)) as revenue_margin_difference from denorm.fact_transaction_kpi join denorm.dim_region on denorm.fact_transaction_kpi.Region_sk = denorm.dim_region.Region_SK group by [Region Name] order by revenue_margin_difference desc"
TABLE SCHEMAS - 

  """

  for schema in table_schemas:
    template+=schema
    template+="\n\n----------------\n"

  template+="""


"""

  prompt_template = PromptTemplate(input_variables=["query"], template=template)
  query_check_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="review")
#   review = query_check_chain.run("""select top 10 [region_Name], [Total_Revenue_2023], [Gross_Margin_2023], ([Total_Revenue_2023] - [Gross_Margin_2023]) as [Difference]
# from denorm.dim_region
# join (
#     select sum(net_revenue) as [Total_Revenue_2023], sum(Gross margin) as [Gross_Margin_2023], Region sk
#     from denorm.fact_transaction_kpi
#     where year(period_date) = 2023
#     group by Region sk
# ) as t on denorm.dim_region.Region SK = t.Region sk
# order by [Difference] desc""")
  # print(review)
  return query_check_chain
  # query_check_chain({"topic": "callbacks"}, callbacks=[StdOutCallbackHandler()])

# querycheckfunc()

