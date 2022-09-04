import os.path
import base64
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import sqlite3

import html
import json
import os
import re
import requests
import sys
from collections import namedtuple
Album = namedtuple('Album', 'artist title release_date tracks')
Track = namedtuple('Track', 'number title url duration released')


from campdown import Downloader
from tqdm import tqdm

def decode(content):
    """Decode the content of a Bandcamp page.
    Args:
        content (str): HTML content.
    """

    # Search album data.
    matches = re.search('data-tralbum=\"([^\"]*)\"', content)

    if not matches:
        sys.exit('error: could not find any tracks.')

    # Get album data.
    data = matches.group(1)
    # Decode HTML.
    data = html.unescape(data)
    # Decode to JSON.
    data = json.loads(data)

    return Album(
        artist=data['artist'],
        title=data['current']['title'],
        release_date=data['current']['release_date'],
        tracks=[Track(
            number=track['track_num'],
            title=track['title'],
            url=(track['file'] or {}).get('mp3-128', None),
            duration=track['duration'],
            released=not track['unreleased_track']
            ) for track in data['trackinfo']]
    )

def download(album:Album, destination)->str:
    """A function that downloads the appropriate files from a Bandcamp album.
    It returns the list of file paths.

    Args:
        album (Album): The Album in Album format, as described in the named Tuple in the file.
        destination (str): Destination for the downloaded files.

    Returns:
        str: A CSV formatted list of filepaths.
    """    
    # Create array to store the filepaths
    paths = []
    # Create folder.
    os.makedirs(destination, exist_ok=True)

    print('Downloading album into %s' % destination)

    # Notify for unreleased tracks.
    if (any((not track.released for track in album.tracks))):
        print('\nWARNING: some tracks are not released yet! '
              'I will ignore them.\n')

    # Download tracks.
    for track in album.tracks:
        if not track.released:
            continue
        title = re.sub(r'[\:\/\\]', '', track.title)  # Strip unwanted chars.
        file = '%s - %s.mp3' % (album.artist, title)
        path = os.path.join(destination, file)
        downloaded = download_file(track.url, path, file)
        if downloaded: paths.append(path)
    return ";".join(paths)

def download_file(url, target, name)->bool:
    """Download a file.
    Adapted from https://stackoverflow.com/q/15644964/9322103.
    Args:
        url (str):    URL of the file.
        target (str): Target path.
        name (str):   Title of the download.
    """
    if not url:
        print("Erreur sur le fichier.")
        return False
    with open(target, 'wb') as f:
        response = requests.get(url, stream=True)
        size = response.headers.get('content-length')

        if size is None:
            print('%s (unavailable)' % name)
            return False

        downloaded = 0
        size = int(size)
        for data in response.iter_content(chunk_size=4096):
            downloaded += len(data)
            f.write(data)
            progress = int(20 * downloaded / size)
            sys.stdout.write(
                '\r[%s%s] %s' % ('#' * progress, ' ' * (20 - progress), name))
            sys.stdout.flush()
        sys.stdout.write('\n')
    return True


class BandcampReader():
    def __init__(self)->None:        
        #AUTH PART
        #ICI ON VERIFIE ET CREE SI IL MANQUE LE TOKEN QUI NOUS PERMET
        #D'ACCEDER A L'API

        SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify']
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
        mails = service.users().messages().list(userId='me',q="label:bandcamp-releases subject:\"new+release\" -\"just+announced\" -\"SAMPLE+PACK\"", maxResults=500).execute()
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
        if messages != None:
            for msg in tqdm(messages[:]):
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
        else:
            print("All the messages have already been downloaded.")
        return None

    def download_links(self)->None:
        cursor_links = self.db_links.cursor()
        query = """ 
            SELECT *
            FROM links
            WHERE location IS NULL;"""
        links = cursor_links.execute(query).fetchall()
        cursor_links.close()
        for l in tqdm(links[:]):
            try:
                response = requests.get(l[1])
            except Exception:
                sys.exit('error: could not parse this page.')
            album = decode(response.text)
            locations = download(album, destination="output/")
            cursor_links = self.db_links.cursor()
            query = """
                    UPDATE links
                    SET location = ?
                    WHERE mail_id == ?"""
            cursor_links.execute(query, (locations, l[0]))
            self.db_links.commit()
            cursor_links.close()

    def remove_tracks_from_gmail(self)->None:
        cursor_links = self.db_links.cursor()
        query = """ 
            SELECT *
            FROM links
            WHERE location IS NOT NULL;"""
        links = cursor_links.execute(query).fetchall()
        cursor_links.close()
        missing_links = []
        for l in links:
            locations = [os.path.exists(loc) for loc in l[2].split(';')]
            if False in locations: missing_links.append((l[0], l[1]))
        print(missing_links)
