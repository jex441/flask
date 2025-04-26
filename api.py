from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from openai import OpenAI
import os
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
import json
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()

# Set up logging and ai api configuration:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = "gpt-4o"

# Step 1: Assess if request is a relevant recruiter task
class EventExtraction(BaseModel):
    """First LLM call: Extract basic event information"""

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

# Step 2: Define the functions:
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
    logger.info(
        f"Extraction complete - Is request related to a job recruiter: {result.is_recruiter_request}, Confidence: {result.confidence_score:.2f}"
    )
    return result

def get_recruiter_response(description: str) -> RecruiterResponse:
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"You are a helpful job recruiter assistant. Respond only to the most recent user message in the conversation. If the conversation history seems relevant to the task at hand, reference it in your response but try not to repeat yourself since the user has previous chat messages already.",
            },
            {"role": "user", "content": description},
        ],
        response_format=RecruiterResponse,
    )
    result = completion.choices[0].message.parsed

    return result

# --------------------------------------------------------------
# Step 3: Chain the functions together
# --------------------------------------------------------------

def process_request(user_input: str):
    """Main function implementing the prompt chain with gate check"""
    logger.info("Processing desired outcome")
    logger.debug(f"Raw input: {user_input}")

    # First LLM call: Extract basic info
    initial_extraction = extract_outcome_info(user_input)

    # Gate check: Verify if it's an outcome related to a job recruiter
    if (
        not initial_extraction.is_recruiter_request
        or initial_extraction.confidence_score < 0.7
    ):
        logger.warning(
            f"Gate check failed - is_recruiter_request: {initial_extraction.is_recruiter_request}, confidence: {initial_extraction.confidence_score:.2f}"
        )
        return None

    logger.info("Gate check passed, proceeding with recruiter response processing")

    # Second LLM call: Get detailed exercise information
    response_details = get_recruiter_response(initial_extraction.description)

    # Third LLM call: Generate confirmation
    # confirmation = generate_confirmation(response_details)

    logger.info("Recruiter response confirmation generated successfully")
    return response_details

# Initialize app and db:
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helix.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<User %r' % self.id

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
    
# with app.app_context():
#         db.create_all()

# Routes:
@app.route("/auth", methods=['POST', 'GET'])
def auth():
    if request.method == 'POST':
        # find or create user
        return 'USER'
    
@app.route("/messages", methods=['POST', 'PUT', 'GET'])
def messages():
    if request.method == 'POST':
        data = request.get_data().decode('utf-8')
        decoded_data = json.loads(data)
        print(decoded_data)

        # create message entry in db
        new_user_message = Message(role="user", content=decoded_data)
        db.session.add(new_user_message)
        db.session.commit()

        # return message history of conversation and pass to process_request
        messages = Message.query.order_by(Message.date_created.desc()).all()
        messages_dict = [msg.to_dict() for msg in messages]
        conversation = jsonify(messages_dict)

        system_response = process_request(conversation.get_data(as_text=True))

        if system_response is None:
            return jsonify({"error": "Not a recruiter request."})

        # create new message entry in db with response
        new_system_message = Message(role="system", content=system_response.confirmation, data=system_response.response)
        db.session.add(new_system_message)
        db.session.commit()
        print(system_response)

        if system_response:
            return jsonify({"message": system_response.confirmation, "data": list(system_response.response) if isinstance(system_response.response, set) else system_response.response})

    if request.method == "GET":
        messages = Message.query.order_by(Message.date_created.asc()).all()
        messages_dict = [msg.to_dict() for msg in messages]
        conversation = jsonify(messages_dict)
    return conversation

# Run
if __name__ == "__main__":
    app.run(port=8000, debug=True)