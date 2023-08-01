import os
import openai
from flask import Flask, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from api.ai_services.appointment import get_appointment_category
from api.ai_services.business import get_business_detail
from api.ai_services.category import get_category
from api.ai_services.inventory import get_inventory_details

app = Flask(__name__)
app.config.from_pyfile('./config.py')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route('/health')
def health_check():
    # receive_message()
    return f"{app.config.get('SITE_TITLE')} Vin Solution Puller is OK"


@app.route('/version')
def version():
    return app.config.get("VERSION")


@app.route('/test/smai-gpt', methods=['POST'])
def smai_gpt():
    """take question and conversation_history as inputs and returns AI generated answeres based on the provided input.

    Body:
        {
            "question": "What would have happened if Goku never hit his head in the childhood?",
            "conversation_history": [],
        }

    Returns:
        response: 
        {
            "content": "If Goku never hit his head and lost his memories of his Saiyan heritage,
            he would have continued with his original Saiyan mission to conquer Earth.....",
            "role": "assistant"
        }
    """    
    data = request.json
    print("request_data", data)

    question = data.get('question')
    if question:
        openai.api_key = os.getenv('OPENAI_API_KEY')
        openai.organization_key = os.getenv('OPENAI_ORGANIZATION_KEY')
        category = get_category(question)
        print('category', category)
        response = {}
        if category == '1':
            response['appointment'] = get_appointment_category(question)
        elif category == '2':
            response['inventory'] = get_inventory_details(question)
        elif category == '3':
            response['business_details'] = get_business_detail(question)

        # TODO: if provided add the conversation history into the request
        conversation_history = data.get('conversation_history')


        # completion = openai.ChatCompletion.create(
        #     model="gpt-3.5-turbo",
        #     messages=[
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         {"role": "user", "content": question}
        #     ]
        # )

        # answer = completion.choices[0].message

        return response

    else:
        return {'status_code': 400, 'message': 'please provide question to be answered'}
