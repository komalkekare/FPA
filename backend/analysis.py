# This is the overall chain where we run these two chains in sequence.
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains import SimpleSequentialChain
from langchain.chat_models import AzureChatOpenAI


from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    CallbackManagerForToolRun,
)
from typing import Optional
import os


os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-07-01-preview"
os.environ["OPENAI_API_BASE"] = "https://fpa-genai.openai.azure.com/"
os.environ["OPENAI_API_KEY"] = "be44f14be27a4e0d85be7a51f0e90d86"



class analysis(BaseTool):

     def _run(
        self, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        llm = AzureChatOpenAI(
            temperature=0,
            deployment_name="fpa-genai",
            model_name="gpt-35-turbo-16k",
            openai_api_base="https://fpa-genai.openai.azure.com/",
            openai_api_version="2023-07-01-preview",
            openai_api_key="be44f14be27a4e0d85be7a51f0e90d86",
            openai_api_type="azure")
        template = """You are a helpful agent which does calculations and analysis for the given input - {input}.
The calculations and analysis have to be according to the INSTRUCTIONS provided. 
Give properly formatted numeric answers.

INSTRUCTIONS - 
- If the input is a mathematical equation, you should calculate the answer and return it.
- If the input has a list[] and wants you to calculate mean, median, mode, standard deviation, variance, then you should calculate that accordingly and return the output.
- If the input  has a list[] and wants you to do statistical analysis then calculate mean, median, mode, standard deviation, variance and return them as output. 
  """

        prompt_template = PromptTemplate(input_variables=["input"], template=template)
        analysischain = LLMChain(llm=llm, prompt=prompt_template, output_key="review")
        analysisanswer = analysischain.run(self)
        return analysisanswer