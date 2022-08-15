import os.path
import base64
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import sqlite3

import argparse
import html
import json
import os
import re
import requests
import sys

from collections import namedtuple

from campdown import Downloader

from tqdm import tqdm

class BandcampReader():

    def __init__(self)->None:        
        
        #AUTH PART
        #ICI ON VERIFIE ET CREE SI IL MANQUE LE TOKEN QUI NOUS PERMET
        #D'ACCEDER A L'API

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
        #ICI ON VA SE CHARGER DE RAJOUTER LA PARTIE BDD QUI VA STOCKER LES SONS QUE
        #NOUS AVONS DEJA SCANNES
        self.db_links = sqlite3.connect('links.sqlite')
        cursor_links = self.db_links.cursor()
        query = """ SELECT name 
                    FROM sqlite_master 
                    WHERE type='table' 
                    AND name='links';"""
        if cursor_links.execute(query).fetchone() == None:
            query = """ CREATE TABLE links(
                        mail_id TEXT PRIMARY KEY UNIQUE,
                        link TEXT NOT NULL,
                        location TEXT);"""
            cursor_links.execute(query)
            print("Table links has been created !")
        else:
            print("Table links has been found. Connecting now !")
        cursor_links.close()

    def load_releases(self, verbose = False):
        
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=self.creds)
        mails = service.users().messages().list(userId='me',q="label:bandcamp-releases subject:'new+release'", maxResults=500).execute()
        messages = mails.get('messages')
        # messages is a list of dictionaries where each dictionary contains a message id.
        # iterate through all the messages

        # En premier on va récuperer la liste
        # Des id déjà existants dans la BDD

        cursor_links = self.db_links.cursor()
        query = """ 
                SELECT mail_id
                FROM LINKS"""
        ids = [id[0]for id in cursor_links.execute(query).fetchall()]
        cursor_links.close()
        for msg in messages[:]:
            if msg['id'] not in ids:
                # Get the message from its id
                txt = service.users().messages().get(userId='me', id=msg['id']).execute()
                # Get value of 'payload' from dictionary 'txt'
                payload = txt['payload']
                # The Body of the message is in Encrypted format. So, we have to decode it.
                # Get the data and decode it with base 64 decoder.
                parts = payload.get('parts')[0]
                data = parts['body']['data']
                data = data.replace("-","+").replace("_","/")
                decoded_data = base64.b64decode(data)
                soup = BeautifulSoup(decoded_data , "lxml")
                links = str(soup.findAll("p")[0]).splitlines()
                msg_id = msg['id']
                first_link = [link.split('?')[0] for link in links if link[:5]=="https"][0]
                query = """ INSERT INTO links(mail_id, link)
                            VALUES(?,?);"""
                cursor_links = self.db_links.cursor()
                cursor_links.execute(query, (msg_id, first_link))
                self.db_links.commit()
                cursor_links.close()
                if verbose: print(f"Loading release {msg['id']} in the DB.")
            else:
                if verbose: print(f"Release {msg['id']} is already in the DB.")
        return None

    def download_links(self)->None:
        cursor_links = self.db_links.cursor()
        query = """ 
            SELECT *
            FROM links;"""
        links = cursor_links.execute(query).fetchall()
        cursor_links.close()
        for l in tqdm(links[:]):
            downloader = Downloader(
                url = l[1],
                out = "output/",
                verbose=True,
                art_enabled=False)
            downloader.run()
