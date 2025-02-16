import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError
from datetime import datetime
from dotenv import load_dotenv
import base64
import os
import json
import asyncio

# Load environment variables
load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY in your .env file.")

# Initialize Gemini client
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-001')

class GmailHandler:
    def __init__(self):
        # Load Gmail credentials
        load_dotenv()
        print("Loading credentials from .env file...")
        access_token = os.getenv('GMAIL_ACCESS_TOKEN')
        refresh_token = os.getenv('GMAIL_REFRESH_TOKEN')
        
        if not access_token or not refresh_token:
            raise ValueError("Missing tokens in .env file. Please ensure GMAIL_ACCESS_TOKEN and GMAIL_REFRESH_TOKEN are set.")
        
        print(f"Access Token (first 15 chars): {access_token[:15]}...")
        print(f"Refresh Token (first 15 chars): {refresh_token[:15]}...")
        
        self.initialize_credentials(access_token, refresh_token)
        
    def initialize_credentials(self, access_token, refresh_token):
        """Initialize Gmail credentials"""
        print("\nInitializing Gmail credentials...")
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id='407408718192.apps.googleusercontent.com',
            client_secret='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',
            scopes=['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']
        )
        self.service = build('gmail', 'v1', credentials=self.credentials)
        print("Gmail service initialized successfully")

    def search_flight_emails(self, start_date=None, end_date=None, airline=None, departure_city=None, destination_city=None):
        """
        Search for flight confirmation emails within a date range
        Args:
            start_date (str): Start date in YYYY/MM/DD format
            end_date (str): End date in YYYY/MM/DD format
            airline (str): Specific airline email domain to search for
            departure_city (str): Departure city to search for
            destination_city (str): Destination city to search for
        """
        try:
            # Construct search query
            query = ''
            
            # Add date range to query
            if start_date:
                query += f'after:{start_date} '
            if end_date:
                query += f'before:{end_date} '
            
            if airline:
                query += f'from:{airline} '
            
            # Add departure and destination cities to query
            if departure_city:
                query += f'"{departure_city}" '
            if destination_city:
                query += f'"{destination_city}" '
                        
            print(f"\nSearching emails with query: {query}")

            # Execute search
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()

            messages = results.get('messages', [])
            print(f"Found {len(messages) if messages else 0} matching emails")
            
            flight_details = []
            for idx, message in enumerate(messages, 1):
                try:
                    details = self.extract_flight_details(message['id'])
                    if details:
                        flight_details.append(details)
                except Exception as e:
                    print(f"Error processing message {message['id']}: {str(e)}")
                    continue
                    
            return flight_details

        except RefreshError:
            print("Token expired - please get new tokens from OAuth Playground")
            raise
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

    def extract_flight_details(self, message_id):
        """Extract relevant flight information from email"""
        try:
            # Get the email content
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            print("Retrieved email content")

            # Get email payload
            payload = message['payload']
            headers = payload['headers']

            # Extract subject and date
            subject = next(h['value'] for h in headers if h['name'] == 'Subject')
            date = next(h['value'] for h in headers if h['name'] == 'Date')

            # Get email body
            if 'parts' in payload:
                parts = payload['parts']
                data = parts[0]['body'].get('data', '')
            else:
                data = payload['body'].get('data', '')

            # Decode email body
            if data:
                text = base64.urlsafe_b64decode(data).decode('utf-8')
                print("Successfully decoded email body")
            else:
                print("No email body found")
                text = ''

            # Use Gemini to extract flight details
            print("Sending email content to Gemini for parsing...")
            flight_info = self.parse_flight_details_with_gemini(subject, text)

            return {
                'message_id': message_id,
                'subject': subject,
                'date': date,
                'body': text[:500] + '...' if len(text) > 500 else text,  # Truncate long bodies for display
                'flight_info': flight_info  # Add parsed flight details
            }

        except Exception as e:
            print(f"Error extracting details from message {message_id}: {str(e)}")
            return None

    def parse_flight_details_with_gemini(self, subject, body):
        """Use Gemini to extract flight details from email content"""
        try:
            # Construct a prompt for Gemini
            prompt = f"""
            Extract the following flight details from the email subject and body:
            - Confirmation code
            - Ticket number
            - Passenger name(s)
            - Departure city
            - Destination city
            - Flight date(s)
            - Connecting flight details (if any)
            - Airline name

            Email Subject: {subject}
            Email Body: {body}

            Return the details in JSON format.
            """

            # Send the prompt to Gemini
            response = model.generate_content(prompt)

            # Preprocess the response to remove Markdown code block markers
            response_text = response.text.strip()
            if response_text.startswith("```json") and response_text.endswith("```"):
                response_text = response_text[7:-3].strip()  # Remove ```json and ```

            # Parse the response as JSON
            flight_info = json.loads(response_text)
            return flight_info

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Gemini response: {str(e)}")
            print("Raw Gemini Response:", response.text)
            return None
        except Exception as e:
            print(f"Error parsing flight details with Gemini: {str(e)}")
            return None

    def draft_response_email(self, user_request, flight_details):
        """Use Gemini to draft a response email based on the user's request and flight details"""
        try:
            # Construct a prompt for Gemini
            prompt = f"""
            The user has requested the following: {user_request}

            Here are the flight details:
            {json.dumps(flight_details, indent=2)}

            Please draft a response email addressing the user's request. Include all relevant flight details and any necessary instructions or information.
            """

            # Send the prompt to Gemini
            response = model.generate_content(prompt)
            print("Gemini Response:", response.text)

            return response.text

        except Exception as e:
            print(f"Error drafting response email with Gemini: {str(e)}")
            return None

    def send_email(self, to, subject, body):
        """Send an email using Gmail API"""
        try:
            message = {
                'raw': base64.urlsafe_b64encode(
                    f"To: {to}\nSubject: {subject}\n\n{body}".encode('utf-8')
                ).decode('utf-8')
            }
            self.service.users().messages().send(userId='me', body=message).execute()
            print(f"Email sent to {to}")
        except Exception as e:
            print(f"Error sending email: {str(e)}")

def speak_with_gemini(text):
    """Use Gemini to convert text to speech"""
    try:
        generation_config = {
            "temperature": 0.9,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": 2048,
            "output_modality": "audio"
        }
        response = model.generate_content(text, generation_config=generation_config, stream=True)
        for chunk in response:
            print(chunk.text)  # Stream the audio response
    except Exception as e:
        print(f"Error generating speech with Gemini: {str(e)}")

def main():
    # Example usage with date range
    gmail_handler = GmailHandler()
    
    try:
        # Get user input for date range
        print("\nEnter date range for search (format: YYYY/MM/DD)")
        start_date = input("Start date (press Enter for no start date): ").strip()
        end_date = input("End date (press Enter for no end date): ").strip()
        airline = input("Enter airline domain (e.g., delta.com, or press Enter for all): ").strip()
        departure_city = input("Enter departure city (press Enter for any): ").strip()
        destination_city = input("Enter destination city (press Enter for any): ").strip()
        
        # Validate dates if provided
        if start_date:
            try:
                datetime.strptime(start_date, '%Y/%m/%d')
            except ValueError:
                print("Invalid start date format. Using no start date.")
                start_date = None
                
        if end_date:
            try:
                datetime.strptime(end_date, '%Y/%m/%d')
            except ValueError:
                print("Invalid end date format. Using no end date.")
                end_date = None
        
        # Search for flight emails
        print("\nSearching for flight confirmation emails...")
        flights = gmail_handler.search_flight_emails(
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
            airline=airline if airline else None,
            departure_city=departure_city if departure_city else None,
            destination_city=destination_city if destination_city else None
        )
        
        # Process results
        # print("\nSearch Results:")
        # print("=" * 50)
        # for idx, flight in enumerate(flights, 1):
        #     print(f"\nFlight Confirmation #{idx}:")
        #     print(f"Subject: {flight['subject']}")
        #     print(f"Date: {flight['date']}")
        #     print(f"Preview of body: {flight['body'][:200]}...")
        #     print("Flight Details:")
        #     print(flight['flight_info'])
        #     print("-" * 50)

        # If multiple flights found, ask the user which one they need help with
        if len(flights) > 1:
            speak_with_gemini("I found multiple flight records. Please specify which one you need help with by entering the corresponding number.")
            selected_flight = int(input("Enter the number of the flight you need help with: ")) - 1
            flight_details = flights[selected_flight]
        else:
            flight_details = flights[0]

        # Ask the user what they need help with
        speak_with_gemini("What do you need help with? For example, you can say change flight or cancel booking.")
        user_request = input("What do you need help with? (e.g., change flight, cancel booking): ").strip()
        print(f"User request: {user_request}")

        # Draft a response email using Gemini
        response_email = gmail_handler.draft_response_email(user_request, flight_details)
        if response_email:
            print("\nDrafted Response Email:")
            print("=" * 50)
            print(response_email)
            print("=" * 50)
        else:
            print("Failed to draft a response email.")

        # Send the email to a hardcoded recipient
        to = "test@example.com"  # Hardcoded for testing
        subject = "Re: Your Flight Inquiry"
        gmail_handler.send_email(to, subject, response_email)

        # Store the conversation context
        context = {
            'flights': flights,
            'user_request': user_request,
            'response_email': response_email
        }
        with open('conversation_context.json', 'w') as f:
            json.dump(context, f)
        print("Conversation context saved to conversation_context.json")

    except RefreshError:
        print("Need to refresh tokens. Please get new tokens from OAuth Playground")
    except HttpError as error:
        print(f"HTTP error occurred: {error}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()