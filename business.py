from langchain import OpenAI, SQLDatabase, SQLDatabaseChain
from langchain.prompts.prompt import PromptTemplate
import csv
import os

llm = OpenAI(temperature=0)
SQLALCHEMY_DATABASE_URI = f'postgresql://postgres:root@localhost:5432/smai_local'
db = SQLDatabase.from_uri(
    SQLALCHEMY_DATABASE_URI, include_tables=[
        'company', 'location', 'company_working_hours'])


def get_business_detail(question):
    template = """Given an input question, first create a syntactically correct postgresql query to run, 
    then look at the results of the query and return the answer. Use the following format:
    
    Question: 'Question here'
    SQLQuery: 'SQL Query to run'
    SQLResult: 'Result of the SQLQuery'
    Answer: 'Final answer here'
    
    DO NOT make up an answer. Only answer based on the information you have.
    
    Points to consider while creating query:

    {table_info}
    Match all values fuzzily except week_day.
    If someone asks for working day or not. they really mean company_working_hours week_day column.
    While asking for working hours for any location check with location table and it's title fuzzily.  
    If someone asks for working hours provide start_time and end_time of days which are working.
    
    
    Question: {input}"""

    prompt = PromptTemplate(
        input_variables=['input', 'table_info'], template=template
    )

    db_chain = SQLDatabaseChain.from_llm(llm, db, prompt=prompt, verbose=True)
    data = db_chain(question)
    print('business_details', data['result'])
    
    # Store the results in the CSV file
    filename = 'buisness.csv'
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['question', 'prompt', 'answer'])

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            'question': question,
            'prompt': template,
            'answer': data['result']
        })

    return data['result']
