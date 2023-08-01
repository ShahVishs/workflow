from langchain.llms import VertexAI
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain
import csv
import os

llm = VertexAI(temperature=0)


def get_category(question):
    template = """Given an input question, read it and try to understand it, 
    don't assume anything that is not related to the question, and answer only in digits from 1 to 3 like this:
    - Reply 1 if the question is related to appointments (come/can't come).
    - Reply 2 if the question is related to inventory, such as vehicles or price or other inventory-related information.
    - Reply 3 if the question is related to the company, such as business operations or working days and hours.
     
    Question: {input}"""
    prompt = PromptTemplate(
        input_variables=["input"], template=template
    )
    db_chain = LLMChain(llm=llm, prompt=prompt, verbose=True)

    result = db_chain(question)
    # Store the results in the CSV file
    filename = 'category.csv'
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=['question', 'prompt', 'category'])

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'question': question,
            'prompt': template,
            'category': result['text']
        })

    return result['text']