import google.generativeai as genai
from sensoai import SensoClient
import json
import time

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY in your .env file.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Configure Senso.ai
SENSO_API_KEY = os.getenv('SENSO_API_KEY')
if not SENSO_API_KEY:
    raise ValueError("Please set the SENSO_API_KEY in your .env file.")

senso_client = SensoClient(api_key=SENSO_API_KEY)

def load_conversation_context():
    """Load the conversation context from the JSON file."""
    try:
        with open('conversation_context.json', 'r') as f:
            context = json.load(f)
        return context
    except Exception as e:
        print(f"Error loading conversation context: {str(e)}")
        return None

def initiate_call(phone_number):
    """Initiate a call using Senso.ai."""
    print(f"Calling airline customer service at {phone_number}...")
    call = senso_client.make_call(phone_number)
    return call

def handle_conversation(call, context):
    """Handle the conversation with the airline's customer service agent/bot."""
    print("Conversation started...")
    
    while True:
        # Listen to the agent/bot's response
        agent_response = senso_client.listen(call)
        print(f"Agent/Bot: {agent_response}")

        # Use Gemini to generate a response
        prompt = f"""
        You are interacting with an airline customer service agent/bot to {context['user_request']}.
        The agent/bot said: {agent_response}
        Your task is to provide the following details and request assistance:
        - Confirmation code: {context['flights'][0]['flight_info']['confirmation_code']}
        - Passenger name: {context['flights'][0]['flight_info']['passenger_names'][0]}
        Generate an appropriate response.
        """
        gemini_response = model.generate_content(prompt)
        print(f"Gemini Response: {gemini_response.text}")

        # Speak the response using Senso.ai
        senso_client.speak(call, gemini_response.text)

        # Check if the conversation should end
        if "goodbye" in gemini_response.text.lower():
            print("Ending conversation...")
            break

        # Add a delay to simulate real-time conversation
        time.sleep(2)

def main():
    # Load conversation context
    context = load_conversation_context()
    if not context:
        print("No conversation context found. Please run the Gmail Input Handler first.")
        return

    # Airline customer service phone number
    airline_phone_number = "+1-800-123-4567"

    # Initiate the call
    call = initiate_call(airline_phone_number)

    # Handle the conversation
    handle_conversation(call, context)

if __name__ == "__main__":
    main()