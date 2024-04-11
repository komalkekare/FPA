from __future__ import annotations

from pydantic import Extra

from langchain.schema.language_model import BaseLanguageModel
from langchain.callbacks.manager import (
    AsyncCallbackManagerForChainRun,
    CallbackManagerForChainRun,
)
from langchain.chains.base import Chain
from langchain.prompts.base import BasePromptTemplate
from langchain.callbacks.stdout import StdOutCallbackHandler
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import BaseMemory
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

import os
os.environ['OPENAI_API_KEY']='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'

class SqlQueryChain(Chain):
    """
    An example of a custom chain.
    """

    prompt: BasePromptTemplate
    """Prompt object to use."""
    llm: BaseLanguageModel
    output_key: str = "text"  #: :meta private:

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Will be whatever keys the prompt expects.

        :meta private:
        """
        return self.prompt.input_variables

    @property
    def output_keys(self) -> List[str]:
        """Will always return text key.

        :meta private:
        """
        return [self.output_key]

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        # Your custom chain logic goes here
        # This is just an example that mimics LLMChain
        prompt_value = self.prompt.format_prompt(**inputs)

        # Whenever you call a language model, or another chain, you should pass
        # a callback manager to it. This allows the inner run to be tracked by
        # any callbacks that are registered on the outer run.
        # You can always obtain a callback manager for this by calling
        # `run_manager.get_child()` as shown below.
        response = self.llm.generate_prompt(
            [prompt_value], callbacks=run_manager.get_child() if run_manager else None
        )

        # If you want to log something about this run, you can do so by calling
        # methods on the `run_manager`, as shown below. This will trigger any
        # callbacks that are registered for that event.
        if run_manager:
            run_manager.on_text("Generating the SQL query")

        return {self.output_key: response.generations[0][0].text}

    async def _acall(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        # Your custom chain logic goes here
        # This is just an example that mimics LLMChain
        prompt_value = self.prompt.format_prompt(**inputs)

        # Whenever you call a language model, or another chain, you should pass
        # a callback manager to it. This allows the inner run to be tracked by
        # any callbacks that are registered on the outer run.
        # You can always obtain a callback manager for this by calling
        # `run_manager.get_child()` as shown below.
        response = await self.llm.agenerate_prompt(
            [prompt_value], callbacks=run_manager.get_child() if run_manager else None
        )

        # If you want to log something about this run, you can do so by calling
        # methods on the `run_manager`, as shown below. This will trigger any
        # callbacks that are registered for that event.
        if run_manager:
            await run_manager.on_text("Log something about this run")

        return {self.output_key: response.generations[0][0].text}

    @property
    def _chain_type(self) -> str:
        return "my_custom_chain"
    
def SQLAgent(table_schemas):

    # tools=[
    # Tool.from_function(func=CustomSearchTool._run,
    #                    name="azure_sql_connector",
    #                    description="A sql database with information on topics like Company/Organisation Revenue, Cost, Employee Details.Input to this tool is a detailed and correct SQL query, output is a result from the database. If the query is not correct, an error message will be returned. If an error is returned, rewrite the query, and try again")
    # ]
    template="""
    As an SQL Agent, your task is to generate SQL queries based on input questions.

    Your Goal: Create syntactically correct MSSQL queries that extract relevant information from the database by strictly following guidelines, important notes and notes.
    
    Guidelines:
    - When question asks something for 'each month' run a loop from 1 to 12 and use the counter as the month. Such as 'What are the top 5 clients by revenue for each month in 2022?', then write a while loop that iterates through every month of the year and searches for the top 5 clients for each month from january to december like - 
    'DECLARE @counter INT = 1
    WHILE @counter <= 12
    BEGIN
        ```Enter the sql query````
        -- For example, you can print the current number
        PRINT 'Current number: ' + CAST(@counter AS VARCHAR(2))
        -- Increment the counter
        SET @counter = @counter + 1
    END'.
    - Construct queries that request only relevant columns.
    - Utilize the given column names from the Table Metadata.
    - Employ the 'LIKE' operator for string comparisons within subqueries.For string comparisons, use 'LIKE' like this: WHERE [column_name] LIKE '%value%'.
    - Always enclose column names in brackets []. Example: SELECT [column_name] FROM denorm.<table_name>.
    - When dealing with multiple values, use 'IN' and compare against the subquery's output.

    Important Notes:
    - Avoid DML operations (INSERT, UPDATE, DELETE, DROP, etc.).
    - Ensure adherence to the provided table structures and relationships.
    - Specifically, consider the table metadata for 'denorm.fact_transaction_kpi'.

    Notes:
    - Always give queries in single line.
    - Use MSSQL queries, do not use mysql or postgresql query.
    1. Enclose the column name in square brackets ([]) if you are using Microsoft SQL Server. Example: SELECT [Practice Name] FROM YourTable;
    - YTD means current year to current date and QTD means current quarter to current date.
    - Always use like operator in where clauses to compare strings. where <column_name> like '%value%.
    - Join 2 or more tables to produce better results
    - consider the Column names from the tables like [Practice Name[] from the schema for ex. What are the top 5 practice by total revenue in 2023? What are the total revenue by practice name in 2023?
    - Always join the table name if you are using any column of that table from table metadata.
    - Do not use The ORDER BY clause in inline functions, derived tables, subqueries, and common table expressions. For ex. SELECT TOP 5 [Practice Name] FROM denorm.dim_practice WHERE [Practice_SK] IN ( SELECT TOP 5 [Practice_SK] FROM (SELECT [Practice_SK], SUM([net_revenue]) as total_revenue FROM denorm.fact_transaction_kpi WHERE YEAR([period_date]) = 2023 GROUP BY [Practice_SK]) subquery ORDER BY total_revenue DESC) ORDER BY [Practice Name];
    - Always type table name as 'denorm.<table_name>'. Example: 'select * from denorm.<table_name>'. Example denorm.dim_practice
    - All the column names in the query should be surrounded by []. Example: select [column 1],[column 2] from denorm.<table_name>
    - Always use 'like' for string comparisons in subqueries as following - where <column_name> like "%value%. Example - select sum(net_revenue) as total_revenue from denorm.fact_transaction_kpi where [Client_sk] in (select [Client_SK] from denorm.dim_client where [Client Name] like '%CVENT%').
    - If multiple instances are found in where clause in subquery, then check whether the value is in the output of the subquery. Example - select sum(net_revenue) as total_revenue from denorm.fact_transaction_kpi where [Client_sk] in (select [Client_SK] from denorm.dim_client where [Client Name] like '%CVENT%). The subquery in this returns an array and 'in' is used to check the values.
    - Relationship and structure of tables below. Do not use any other relationship types or properties that are not provided.
    - If the metadata has column name with a space, then it should be be in the query also. Example: For |Region Name|varchar|Name of Region|Practice Name|Project Name| ,the query will be like select [Project Name], [Practice Name] from denorm.<table name> where [Region Name]=<value>.

    NOTE: Always respond in plain text, convert query to ONE line.
    
    Table Metadata:
    ````
    """
    
    # template="""
    # As an SQL Agent, your task is to generate syntactically correct MSSQL queries that extract relevant information from the database and give the result in single line

    # Guidelines:
    # - Construct queries that request only relevant columns.
    # - Utilize the given column names from the Table Metadata.
    # - Refrain from querying all columns; select only necessary ones.
    # - Employ the 'LIKE' operator for string comparisons within subqueries.For string comparisons, use 'LIKE' like this: WHERE [column_name] LIKE '%value%'.
    # - Always enclose column names in brackets []. Example: SELECT [column_name] FROM denorm.<table_name>.
    # - When dealing with multiple values, use 'IN' and compare against the subquery's output.
    # - Retrieve the Year-till-Date (YTD) and Quarter-till-Date (QTD) Data by querying the data. Ensure that the calculation for YTD refers to the data accumulated from the beginning of the current year up to the current date, while the QTD calculation covers the data from the start of the current quarter up to the current date.

    # Important Notes:
    # - Avoid DML operations (INSERT, UPDATE, DELETE, DROP, etc.).
    # - Ensure adherence to the provided table structures and relationships.
    # - Specifically, consider the table metadata for 'denorm.fact_transaction_kpi'.

    # Notes:
    # - Always give queries in single line
    # - Always use like operator in where clauses to compare strings. where <column_name> like '%value%.
    # - Join 2 or more tables if necessary to produce better results
    # - Always type table name as 'denorm.<table_name>'. Example: 'select * from denorm.<table_name>'
    # - All the column names in the query should be surrounded by []. Example: select [column 1],[column 2] from denorm.<table_name>
    # - Always use 'like' for string comparisons in subqueries as following - where <column_name> like "%value%. Example - select sum(net_revenue) as total_revenue from denorm.fact_transaction_kpi where [Client_sk] in (select [Client_SK] from denorm.dim_client where [Client Name] like '%CVENT%').
    # - If multiple instances are found in where clause in subquery, then check whether the value is in the output of the subquery. Example - select sum(net_revenue) as total_revenue from denorm.fact_transaction_kpi where [Client_sk] in (select [Client_SK] from denorm.dim_client where [Client Name] like '%CVENT%). The subquery in this returns an array and 'in' is used to check the values.
    # - Relationship and structure of tables below. Do not use any other relationship types or properties that are not provided.
    # - If the metadata has column name with a space, then it should be be in the query also. Example: For |Region Name|varchar|Name of Region| ,the query will be like select * from denorm.<table name> where [Region Name]=<value>

    # NOTE: Always respond in plain text, convert query to ONE line.
    
    # Table Metadata:
    # ````
    # """
#     template += """
# Table Name: denorm.fact_transaction_kpi
# Table Description: This table describes Cost and Revenue Data across various projects and verticals.
# Table Structure:
# |column_name|data_type|description|
# |---|---|---|
# |net_revenue|float|Total amount gained as net revenue
# |Total_Direct_Cost|float|Total direct cost incurred
# |Sales_Marketing_Cost|float|Cost related to sales and marketing activities
# |Total_Practice_Bench_Cost|float|Total cost of the practice bench
# |SG&A_Cost|float|Selling, General, and Administrative costs.
# |Total_Non_GAAP_items|float|Total cost related to Non-GAAP items.
# |total|float|
# |sales_commission|float|
# |Customer_Success|float|
# |Practice_sk|int|Foreign key which maps to column 'Practice_SK' of table 'dim_practice'|
# |Region_sk|int|Foreign key which maps to column 'Region_SK' of table 'dim_region'|
# |Client_sk|int|Foreign key which maps to column 'Client_SK' of table 'dim_client'|
# |period_date|date|
# |project_sk|int|Foreign key which maps to column 'Project_SK' table 'dim_project'|
# |billing_type_sk|int|Foreign key which maps to column 'Billing_Type_SK' of table 'dim_billing_type'|
# |onsite_offsite_sk|int|Foreign key which maps to column 'Onsite_Offsite_SK' of table 'dim_onsite_offsite'|
# |Direct_Margin|float|
# |customer_margin|float|
# |regional_margin|float|
# |contribution_margin|float|
# |EBIDTA_GAAP|float|Earnings Before Interest, Taxes, Depreciation, and Amortization (GAAP).
# |EBIDTA_NonGAAP|float|Earnings Before Interest, Taxes, Depreciation, and Amortization (Non-GAAP).
# |Net_Margin|float| 
# |adjusted cs|float| 
# |ado costs|float| 
# |total practice cost|float|
# |practice_margin|float| 
# |Forex Impact - Direct|float|
# |People_cost|float| 
# |Other_Direct_Cost|float| 
# |Offshore_Facility_Cost|float|
# |person_type_sk|int|Foreign key which maps to column 'Person_SK' of table 'dim_person_type'|
# |work_location_sk|int|Foreign key which maps to column 'Work_location_sk' of table name 'dim_work_location'|
# |salary_cost_cost_per_fte|float| 
# |revenue_num_revenue_per_fte|float|Revenue per full-time equivalent employee
# |cost_contractor_analysis|float|
# |revenue_contractor_analysis|float|
# |onsite_offsite_revised_sk|int|Foreign key which maps to column 'onsite_offsite_revised_sk' of table 'dim_onsite_offsite_revised'|
# |dm_classification_sk|int|Foreign key which maps to column 'dm_classification_sk' of table 'dim_dm_classification'|
# |DM_percentage_contractor_analysis|float|
# |Onsite_Offsite_SK_RA|int|
# |currency_sk|int|Foreign key which maps to column 'currency_sk' of table 'dim_currency'|
# |Transaction_Amount|float|
# |amount|float|
# |Amount_USD_Constant_Curreny_flag|int|
# |employee_sk|int|Foreign key which maps to column 'employee_sk' of table 'dim_employee'|
# |revenue_fte_analysis|float|
# |cost_fte_analysis|float|
# |Vertical_sk|int|Foreign key which maps to column 'vertical_sk' of table 'dim_vertical_market_delivery'|
# |sga_cost|float|
# |bench_cost|float|
# |employee_level_sk|int|Foreign key which maps to column 'employee_sk' of table 'dim_employee_level'|
# |Project_Sold_Margin|float|
# |Customer_Sold_Margin|float|
# |Delivery Partner|float|
# |Softblock Unbilled|float|
# |cost_head_detailed_sk|int|Foreign key which maps to column 'cost_head_detailed_sk' of table 'dim_cost_head_detailed'|
# |cost_head_sk|int|Foreign key which maps to column 'cost_head_sk' of table 'dim_cost_head'|
# |tb_reco_sk|int|Foreign key which maps to column 'tb_reco_sk' of table 'dim_tb_reco'|
# |subsidiary_sk|int|Foreign key which maps to column 'Subsidiary_sk' of table 'dim_subsidiary'|
# |hiring_fee_direct|float|
# |practice_bench|float|
# |Reversal_of_Facility_Cost|float|
# |gross_margin|float|
# |Softblock Unbilled - dm|float|
# |Account Unbilled|float|
# |Unbilled - DMs|float|
# |Account Unallocated|float|
# |vertical_margin|float|
# |Alliances|float|
# |Regional_Management|float|
# |CRO_Management|float|
# |Regional_Sales|float|
# |SET|float|
# |AVA|float|
# |Marketing|float|
# |Vertical Capability|float|
# |Vertical CTO|float|
# |Vertical Delivery|float|
# |Vertical Head|float|
# |Vertical Ops|float|
# |Vertical Leadership|float|
# |Vertical Sales|float|
# |Vertical Operational Excellence|float|
# |Vertical Presales & Support|float|
# |Bonus-DM|float|"""
    template+="\n\n----------------\n"
    for schema in table_schemas:
        template+=schema
        template+="\n\n----------------\n"
    
    template+="""
    ````
    =======
    Input: {question}
    =======
    """
    
    prompt_template = PromptTemplate(input_variables=["question"], template=template)
    sql_chain = SqlQueryChain(llm=ChatOpenAI(temperature=0), prompt=prompt_template)
    # sql_chain = SqlQueryChain(
    #     llm=ChatOpenAI(temperature=0),
    # )

    return sql_chain
