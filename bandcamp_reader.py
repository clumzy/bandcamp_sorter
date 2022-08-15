import os.path
import base64
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class BandcampReader():

    def __init__(self) -> None:
        #AUTH PART
        SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secret.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        #CONTENT PART
        

    def create_database(self):
        pass

    def get_content(self):
        links_payload = []
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=self.creds)
        mails = service.users().messages().list(userId='me',q="label:bandcamp-releases subject:'new+release'", maxResults=500).execute()
        messages = mails.get('messages')
        # messages is a list of dictionaries where each dictionary contains a message id.
        # iterate through all the messages
        for msg in messages[:]:
            print(msg['id'])
            # Get the message from its id
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            try:
                # Get value of 'payload' from dictionary 'txt'
                payload = txt['payload']
                # The Body of the message is in Encrypted format. So, we have to decode it.
                # Get the data and decode it with base 64 decoder.
                parts = payload.get('parts')[0]
                data = parts['body']['data']
                data = data.replace("-","+").replace("_","/")
                decoded_data = base64.b64decode(data)
                # Now, the data obtained is in lxml. So, we will parse 
                # it with BeautifulSoup library
                soup = BeautifulSoup(decoded_data , "lxml")
                links = str(soup.findAll("p")[0]).splitlines()
                first_link = [link.split('?')[0] for link in links if link[:5]=="https"][0]
                links_payload.append(first_link)
            except:
                print("Mail can't be decoded.")
                pass
        return links_payload