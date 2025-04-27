from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import json
from flask_cors import CORS

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o"

class EventExtraction(BaseModel):
    description: str = Field(description="Raw description of the request")
    is_recruiter_request: bool = Field(
        description="Whether this text describes a request relevant to a job recruiter assistant."
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")

class RecruiterResponse(BaseModel):
    response: str = Field(
        description="Natural language response to the user's request. If no action is needed just return an empty string."
    )
    confirmation: str = Field(description="A confirmation message to the user and and offer for further assistance.")

def extract_outcome_info(user_input: str) -> EventExtraction:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful job recruiter assistant. Analyze only the most recent message in the conversation history. Check if it is related to a task performed by a job recruiter.",
            },
            {"role": "user", "content": user_input},
        ],
        response_format=EventExtraction,
    )
    result = completion.choices[0].message.parsed
    return result

def get_recruiter_response(description: str, history: str) -> RecruiterResponse:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful job recruiter assistant. Conversation history (for context only): {history}",
            },
            {"role": "user", "content": description},
        ],
        response_format=RecruiterResponse,
    )
    result = completion.choices[0].message.parsed

    return result

async def process_request(user_input: str, history):
    # First LLM call: Extract basic info
    initial_extraction = extract_outcome_info(user_input)

    # Gate check: Verify if it's an outcome related to a job recruiter
    if (
        not initial_extraction.is_recruiter_request
        or initial_extraction.confidence_score < 0.7
    ):
        return None

    response_details = get_recruiter_response(initial_extraction.description, history)
    return response_details

# Initialize app and db:
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helix.db'
db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    data = db.Column(db.Text(), nullable=True)
    conversationId = db.Column(db.Integer, nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.now())

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "data": self.data,
            "date_created": self.date_created,
        }
    
@app.route("/messages", methods=["POST", "GET"])
async def messages():
    if request.method == 'POST':
        data = request.get_data()
        decoded_data = json.loads(data.decode('utf-8'))

        # create message entry in db
        new_user_message = Message(role="user", content=decoded_data)
        db.session.add(new_user_message)
        db.session.commit()

        # return message history of conversation and pass to process_request
        messages = Message.query.order_by(Message.date_created.desc()).all()
        messages_dict = [msg.to_dict() for msg in messages]
        conversation = jsonify(messages_dict)
        
        # Awaiting the async process request to make sure the response is ready
        system_response = await process_request(decoded_data, conversation.get_data(as_text=True))

        if system_response is None:
            return jsonify(
            {"role": "user", "content": decoded_data},
            {"role": "system", "content": "I'm sorry, that doesn't appear to be related to job recruitement. If you have questions or need further assistance with job recruitment, feel free to ask!"}
            )

        # create new message entry in db with response
        new_system_message = Message(role="system", content=system_response.confirmation, data=system_response.response)
        db.session.add(new_system_message)
        db.session.commit()
        
        # Return response once everything is done
        return jsonify(
            {"role": "user", "content": decoded_data},
            {"date_created": datetime.now(), "role": "system", "content": system_response.confirmation, "data": system_response.response if isinstance(system_response.response, list) else system_response.response}
        )

    elif request.method == "GET":
        messages = Message.query.order_by(Message.date_created.asc()).all()
        messages_dict = [msg.to_dict() for msg in messages]
        conversation = jsonify(messages_dict)
        return conversation
    
# Run
if __name__ == "__main__":
    app.run(port=8000, debug=True)