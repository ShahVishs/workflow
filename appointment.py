from langchain.llms import VertexAI
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain
import csv
import os

llm = VertexAI(temperature=0)


def get_appointment_category(question):
    
    template = """Given an input question, read it and try to understand it, 
    don't assume anything which is not related to that and answer only in digits from 1 to 3 like this:
    - reply 1 if it is related to new appointment.
    - reply 2 if it is related to reschedule an appointment.
    - reply 3 if it is related to cancel the appointment.


    Question: {input}"""
    prompt = PromptTemplate(
        input_variables=["input"], template=template
    )
    db_chain = LLMChain(llm=llm, prompt=prompt, verbose=True)

    result = db_chain(question)
    print('appointment_category', result['text'])
    
    # Store the results in the CSV file
    filename = 'appointment.csv'
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['question', 'answer', 'prompt'])

        if not file_exists:
            writer.writeheader()

        writer.writerow({'question': question, 'answer': result['text'], 'prompt': template})

    return result['text'].strip()