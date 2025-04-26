from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from openai import OpenAI
import os
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
import json

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
        description="Whether this text describes an request relevant to a job recruiter."
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")

class RecruiterResponse(BaseModel):
    """Second LLM call: Parse specific role and required experience details"""

    name: str = Field(description="Name of the role")
    description: str = Field(
        description="Type of experience needed from candidate to fill an open position."
    )

class EventConfirmation(BaseModel):
    """Third LLM call: Generate confirmation message"""

    confirmation_message: str = Field(
        description="Natural language confirmation message"
    )

# Step 2: Define the functions:
def extract_outcome_info(user_input: str) -> EventExtraction:
    """First LLM call to determine if input is a task related to recruitment for a role with required experience"""
    logger.info("Starting outcome extraction analysis")
    logger.debug(f"Input text: {user_input}")

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"You are a job recruiter tasked with hiring at your organization. Analyze if the text is a request related to a task performed by a job recruiter seeking to hire qualified candidates for an open position.",
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
    """Second LLM call to determine the recruiter message"""
    logger.info("Starting to develop recruiter action")
    print("description::", description)
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"You are a professional job recruiter tasked with hiring at your organization. With the details provided, formulate a quality response to their request.",
            },
            {"role": "user", "content": description},
        ],
        response_format=RecruiterResponse,
    )
    result = completion.choices[0].message.parsed
    logger.info(
        f"Parsed response: {result.name}"
    )
    return result

def generate_confirmation(sequence_details: RecruiterResponse) -> EventConfirmation:
    """Third LLM call to generate a confirmation message"""
    logger.info("Generating confirmation message")

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Generate a natural language response as a professional job recruiter. This response will be used by a human at your organization to send to qualified candidates. Part of your response should be fulfilling the task of the user, and part of your response should be addressed to the user at your organization who will use your response to send to candidates. Ask the user if they would like any modifications to this response to qualified candidates.",
            },
            {"role": "user", "content": str(sequence_details.model_dump())},
        ],
        response_format=EventConfirmation,
    )
    result = completion.choices[0].message.parsed
    logger.info("Confirmation message generated successfully")
    return result

# --------------------------------------------------------------
# Step 3: Chain the functions together
# --------------------------------------------------------------

def process_request(user_input: str) -> Optional[EventConfirmation]:
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
    print('::', response_details)
    # Third LLM call: Generate confirmation
    confirmation = generate_confirmation(response_details)

    logger.info("Recruiter response confirmation generated successfully")
    return confirmation

# Initialize app and db:
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helix.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<User %r' % self.id

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    userId = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return '<Message %r' % self.id
    
with app.app_context():
        db.create_all()

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
        # Extract the string (example: assuming the data is a dictionary with a key "text")
        extracted_string = decoded_data.get("message", "")
        print(extracted_string)
    
        result = process_request(extracted_string)
        if result:
            return f"Confirmation: {result.confirmation_message}"
        else:
            return "This doesn't appear to be a request for a recruiter."

# Run
if __name__ == "__main__":
    app.run(port=8000, debug=True)