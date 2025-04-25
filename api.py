from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from openai import OpenAI
import os
import logging
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
import urllib.parse
import json
import re

# Load environment variables from .env file
load_dotenv()
# Set up logging configuration

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
        description="Whether this text describes an request for a recruiter email sequence to a job candidate"
    )
    confidence_score: float = Field(description="Confidence score between 0 and 1")

class SequenceDetails(BaseModel):
    """Second LLM call: Parse specific role and required experience details"""

    name: str = Field(description="Name of the role")
    description: str = Field(
        description="Type of experience needed from candidate to fill role"
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
                "content": f"Analyze if the text is a request for an email sequence related to recruiting a qualified candidate for a job position.",
            },
            {"role": "user", "content": user_input},
        ],
        response_format=EventExtraction,
    )
    result = completion.choices[0].message.parsed
    logger.info(
        f"Extraction complete - Is request related to a job recruitment email sequence: {result.is_recruiter_request}, Confidence: {result.confidence_score:.2f}"
    )
    return result

def get_recruiter_sequence(description: str) -> SequenceDetails:
    """Second LLM call to determine the recruiter message"""
    logger.info("Starting to develop outreach message")

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"Generate an email as a recruiter based on the provided details.",
            },
            {"role": "user", "content": description},
        ],
        response_format=SequenceDetails,
    )
    result = completion.choices[0].message.parsed
    logger.info(
        f"Parsed email outreach: {result.name}"
    )
    return result

def generate_confirmation(sequence_details: SequenceDetails) -> EventConfirmation:
    """Third LLM call to generate a confirmation message"""
    logger.info("Generating confirmation message")

    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Generate a natural response to accompany the email outreach to a qualified candidate and offer to provide additional steps, details, or modifications.",
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

    # Gate check: Verify if it's an outcome related to physical fitness with sufficient confidence
    if (
        not initial_extraction.is_recruiter_request
        or initial_extraction.confidence_score < 0.7
    ):
        logger.warning(
            f"Gate check failed - is_recruiter_request: {initial_extraction.is_recruiter_request}, confidence: {initial_extraction.confidence_score:.2f}"
        )
        return None

    logger.info("Gate check passed, proceeding with email outreach processing")

    # Second LLM call: Get detailed exercise information
    sequence_details = get_recruiter_sequence(initial_extraction.description)

    # Third LLM call: Generate confirmation
    confirmation = generate_confirmation(sequence_details)

    logger.info("Recruiter sequence confirmation generated successfully")
    return confirmation

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

@app.route("/auth", methods=['POST', 'GET'])
def index():
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

if __name__ == "__main__":
    app.run(port=8000, debug=True)