import pandas as pd
import boto3
import openai
import threading
import backoff
import os
import io
import re
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain import PromptTemplate

# Connect to S3 bucket
s3 = boto3.client('s3')

# Specify the S3 bucket name and folder
bucket_name = "funnelai-datasets"
# folder_name = "ai-service-api/dev/vehicle-inventory/"
folder_name = "ai-service-api/dev/Vehicle_inventory_part_2/"

# Initialize the embedding and vector store variables
embeddings = None
vectorstore = None

# Function to get the list of file names in the S3 bucket folder
def get_file_names_from_s3(bucket_name, folder_name):
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
    file_names = []
    for obj in response.get('Contents', []):
        file_name = obj['Key']
        file_names.append(file_name)
    return file_names

def download_csv_from_s3(bucket_name, file_name):
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    content = response['Body'].read().decode('utf-8-sig', errors='replace')  
    try:
        df = pd.read_csv(io.StringIO(content))
    except pd.errors.EmptyDataError:
        return None
    return df

# Get the list of file names from S3 bucket
file_names = get_file_names_from_s3(bucket_name, folder_name)

# Download CSV files from S3 bucket and store in a list
data = []
for file_name in file_names:
    df = download_csv_from_s3(bucket_name, file_name)
    if df is not None:
        data.append(df)

if data:
    combined_data = pd.concat(data)
    # print(combined_data)  # Display the combined data

    # Convert all columns to string and concatenate them
    combined_data["text"] = combined_data.astype(str).agg(" ".join, axis=1)

    # Extract the text data from the DataFrame
    texts = combined_data["text"].tolist()

    # Define the prompt template
    template = """
    %INSTRUCTIONS:
    Ask me anything about the inventory information.
    If question is related to budget or price, provide the answer in this format: "This vehicle fits your budget."
    %TEXT:
    {text}
    """
    prompt_template = PromptTemplate(
        input_variables=["text"],
        template=template,
    )

    chain = None
    # Function to initialize embeddings and vectorstore
    def initialize_embeddings_vectorstore():
        global embeddings
        global vectorstore

        # Initialize OpenAI embeddings
        embeddings = OpenAIEmbeddings(openai_organization=openai.organization, openai_api_key=openai.api_key)

        # Create vectorstore using FAISS
        vectorstore = FAISS.from_texts(texts, embeddings)
        
        global chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.0, model_name='gpt-3.5-turbo-16k'),
            retriever=vectorstore.as_retriever())

    # Start a separate thread to initialize embeddings and vectorstore
    init_thread = threading.Thread(target=initialize_embeddings_vectorstore)
    init_thread.start()

# Function to perform chat with exponential backoff
@backoff.on_exception(backoff.expo, openai.error.RateLimitError, max_time=60)
def perform_chat_with_backoff(prompt):
    return chain(prompt)

def get_inventory_details(question):
    if data:
        history = []

        # Generate the final prompt by inserting the question into the prompt template
        final_prompt = template.format(text=question)
        print("------- Prompt Begin -------")
        print(final_prompt)
        print("------- Prompt End -------")

        # Wait for the initialization thread to finish before proceeding
        if init_thread:
            init_thread.join()

        # Pass the formatted prompt to the chain for generating a response with backoff
        result = perform_chat_with_backoff({"question": final_prompt, "chat_history": history})
        history.append((question, result["answer"], final_prompt))  

        # Remove the price figures and modify the answer
        modified_answer = result["answer"]
        modified_answer = re.sub(r"\s(\$[\d,]+)", "", modified_answer)  # Remove price figures
        modified_answer = re.sub(r"\d+\.\d+", "", modified_answer)  # Remove value figures
        modified_answer = re.sub(r"\s\S+\s(?:is priced at|with a price of|price of)", "", modified_answer)

        # Store the question, answer, and prompt in a DataFrame
        qa_data = pd.DataFrame(data=history, columns=["Question", "Answer", "Prompt"])

        qa_data.to_csv("inventory.csv", mode="a", header=not os.path.exists("inventory.csv"), index=False)
        return modified_answer.strip()
    else:
        default_prompt = "I'm sorry, but I don't have any specific information about that."
        return default_prompt