import subprocess

import spotipy
from bs4 import BeautifulSoup
import requests, random
from googlesearch import search
import pyttsx3
import speech_recognition as speech
import datetime
import webbrowser
import speedtest
import config
import base64
from urllib.parse import urlencode
import kasa
import asyncio
import wikipedia as wiki
import os
import imdb
from spotipy import Spotify
import SpotifyMethods



#Init Text->Speech
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
#0 for male, 1 for female
engine.setProperty('voice', voices[1].id)

#Google Search
def google_query(query):
    print(f"in google_query: {query}")
    link = []
    for j in search(query, num_results=10):
        link.append(j)
        print(link)
    return link

#Speed Test
def speed_check():
    try:
        print('Testing...')
        speak('Running Speed Test')
        s = speedtest.Speedtest()
        s.get_best_server()
        s.download()
        s.upload()
        res = s.results.dict()
        server = []
        server.append(res["server"]["name"])
        server.append(res["server"]["country"])
        server.append(res["server"]["sponsor"])
        client = []
        client.append(res["client"]["ip"])
        client.append(res["client"]["isp"])
        speed = []
        ONE_MB = 1000000  #in bytes
        speed.append((round((res["download"]/ONE_MB), 2)))
        speed.append((round((res["upload"]/ONE_MB), 2)))
        speed.append((round((res["ping"]), 2)))
        
        speak( f'Download is {speed[0]} megabytes per second  upload speed is {speed[1]} megabytes per second, ping is {speed[2]} milliseconds ')
    except Exception as e:
        print(f"Could not execute speedtest {e}")
        speak("Could not execute speedtest")

#Open Browser
def open_browser(url):
    webbrowser.open_new_tab(url)

#Spotify API

# Async functions not implemented yet
async def get_current_song(spotify: Spotify) -> str:
    if spotify.currently_playing() is None:
        return "Nothing is playing"
    song_name = spotify.currently_playing()['item']['name']
    artist_name = spotify.currently_playing()['item']['artists'][0]['name']
    return f"{song_name} - {artist_name}"



class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"

    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_client_credentials(self):
        client_id = self.client_id
        client_secret = self.client_secret
        if client_secret == None or client_id == None:
            raise Exception("You must set client_id and client_secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            "Authorization": f"Basic {client_creds_b64}"
        }

    def get_token_data(self):
        return {
            "grant_type": "client_credentials"
        }

    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        
        if r.status_code not in range(200, 299):
            raise Exception(f"Could not authenticate client.{r.status_code}")
            # return False
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in']  # seconds
        expires = now + datetime.timedelta(seconds=expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True

    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token

    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers

    def get_resource(self, lookup_id, resource_type='albums', version='v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()

    def get_album(self, _id):
        return self.get_resource(_id, resource_type='albums')

    def get_artist(self, _id):
        return self.get_resource(_id, resource_type='artists')

    def base_search(self, query_params):  # type
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()

    def search(self, query=None, operator=None, operator_query=None, search_type='artist'):
        try:
            if query == None:
                raise Exception("A query is required")
            if isinstance(query, dict):
                query = " ".join([f"{k}:{v}" for k, v in query.items()])
            if operator != None and operator_query != None:
                if operator.lower() == "or" or operator.lower() == "not":
                    operator = operator.upper()
                    if isinstance(operator_query, str):
                        query = f"{query} {operator} {operator_query}"
            query_params = urlencode({"q": query, "type": search_type.lower()})
        except Exception as e:
            print(f"error {e}")
            return False
        return self.base_search(query_params)

# Spotify Search Method
def song_credits(song):
    try:
        client_id = config.client_id
        client_secret = config.client_secret
        spotify = SpotifyAPI(client_id, client_secret)
        print("SC1")
        spotify.get_access_token()
        data = spotify.search(song, search_type="track")
        print(data)
        print(song)
    except IndexError as e:
        return False
    return data

#Time function
def what_time():
    hour = int(datetime.datetime.now().hour)
    minute = int(datetime.datetime.now().minute)
    time = " ".join([str(hour),str(minute)])
    if hour >= 0 and hour < 12:
        speak(f"Good Morning! the time is {time}")
    elif hour >= 12 and hour < 16:
        speak(f"Good Afternoon! the time is {time}")
    elif hour >= 16 and hour < 23:
        speak(f"Good Evening! the time is {time}")

def rand_agent():
    user_agent_list = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
    ]
    for _ in user_agent_list:
        # Pick a random user agent
        user_agent = random.choice(user_agent_list)
        headers = {'User-Agent': user_agent}

    return headers


#headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54'}
URL = ''

#Location Function
def get_location():
    try:
        URL = 'https://iplocation.com/'
        page = requests.get(URL, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        city = soup.find(class_='city').get_text()
        country = soup.find(class_='country_name').get_text()
        latitude = soup.find(class_='lat').get_text()
        longitude = soup.find(class_='lng').get_text()
        return city, country, latitude, longitude
    except Exception as e:
        print(f'Error, location could not be retrieved {e}')
        speak('Error, location could not be retrieved')

# Check Weather
def weather(latitude, longitude):
    try:
        api_key = config.api_key
        base_url = 'http://api.openweathermap.org/data/2.5/weather?'
        complete_url = base_url + "lat=" + \
            str(latitude) + "&lon=" + str(longitude) + "&appid=" + api_key
        response = requests.get(complete_url)
        x = response.json()
    except Exception as e:
        print("An error occurred while retrieving weather information")
        speak("An error occurred while retrieving weather information")
    if x["cod"] != "404":
        return x
    else:
        return False

#Kasa API Integration

def kasa_discover():
    found_devices = asyncio.run(kasa.Discover.discover())
    print(found_devices)


#Greeting
def greet():
    hour = int(datetime.datetime.now().hour)
    minute = int(datetime.datetime.now().minute)
    if minute < 10:
        time = " oh ".join([str(hour), str(minute)])
    else:
        time = " ".join([str(hour),str(minute)])
    if hour >= 0 and hour < 12:
        speak(f"Good Morning! the time is {time}")
        print(f"Good Morning! the time is {time}")
    elif hour >= 12 and hour < 16:
        speak(f"Good Afternoon! the time is {time}")
        print(f"Good Afternoon! the time is {time}")
    elif hour >= 16 and hour < 23:
        speak(f"Good Evening! the time is {time}")
        print(f"Good Evening! the time is {time}")
    
    #Demo mode stuff. Slows down experience
    #print("Hello, I am Athena. Your virtual assistant. How can I help?")
    #speak("Hello, I am Athena. Your virtual assistant. How can I help?")

#Get top google result and solution from stack overflow
def stackoverflow(url):
    SITE = url
    print(SITE)
    page = requests.get(SITE, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')

    for correct in soup.find_all('div', attrs={'class': 'answer js-answer accepted-answer js-accepted-answer'}):
        answer = correct.find('div', attrs={'class': 's-prose js-post-body'})
        ##formatted = ""
        # for paragraph in answer.find_all('p'):
        #  formatted += paragraph.text
        #  formatted += '\n'
        print('answer found')
        return answer.text

def wookiepedia(url):
    SITE = url
    print(SITE)
    page = requests.get(SITE, headers=headers)
    soup = BeautifulSoup(page.content, 'html.parser')

    for correct in soup.find_all('div', attrs={'class': 'main-container'}):
        answer = correct.find('div', attrs={'class': 'resizable-container'})
        answer = correct.find('div', attrs={'class': 'page has-right-rail'})
        answer = correct.find('div', attrs={'class': 'page_main'})
        answer = correct.find('div', attrs={'class': 'content'})
        answer = correct.find('div', attrs={'class': 'mw-content-text'})
        answer = correct.find('div', attrs={'class': 'mw-parser-output'})
        answer = correct.find_all('p')
        print('answer found')
        return(answer[7].text)


#Speaking
def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def listen():
    r = speech.Recognizer()
    with speech.Microphone() as source:
        print("Adjusting for noise")
        r.pause_threshold = 0.5
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        print("Intrepreting...")
        #Ding of death
        #config.function_sound()
        query = r.recognize_google(audio, language='en-CA')
        print("User said: {}".format(query))
    except speech.UnknownValueError:
        print("Instruction not audible.")
        speak("Im sorry, I could not hear you")
        return "None"
    except speech.RequestError:
        print("Instruction Unknown")
        speak("Can you say that again?")
        return "None"
    return query
#Rotten Tomatoes

def rotten_tomatoes_score(query):
    try:
        query += query + " Rotten Tomatoes"
        URL = google_query(query)[0]
        page = requests.get(URL, headers=headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        res = soup.find(class_='mop-ratings-wrap__percentage').get_text()
        check = res.split(' ')
        for i in check:
            if len(i) > 1:
                return i
    except Exception as e:
        print(f'Could not retrieve tomatometer score{e}')
        speak('Could not retrieve tomatometer score')

#IMDB
def find_imdb(query):
    try:
        query += ' IMDB'
        URL = google_query(query)[0]
        page = requests.get(URL, headers=headers)
        html_content = page.text
        soup = BeautifulSoup(html_content, 'lxml')
        title = soup.title.string
        title = title[0:-7]
        return title
    except Exception as e:
        print(f'Movie could not be found: {e}')
        speak('Movie could not be found')


if __name__ == "__main__":
    greet()
    headers = rand_agent()
    city, country, latitude, longitude = get_location()
    #kasa_discover()

    while True:
        query = listen().lower()
        if 'athena' in query:  #Wake Keyword
            speak("How can I help?")
            query = listen().lower()
            if 'open' in query:
                try:
                    print('Opening..')
                    speak('Opening')
                    if 'facebook' in query:
                        open_browser('https://www.facebook.com')
                    elif 'reddit' in query:
                        open_browser('https://www.reddit.com')
                    elif 'youtube' in query:
                        open_browser('https://www.youtube.com')
                    else:
                        query = query.replace('open ', '')
                        query += ' website '
                        URL = google_query(query)[1]

                        open_browser(URL)
                except Exception as e:
                    print(f"Browser could not be opened {e} ")
                    speak("Browser could not be opened")
            elif 'run' in query:
                if 'task manager' in query:
                    current_dir = r"C:\WINDOWS\system32"
                    subprocess.Popen(os.path.join(current_dir, "Taskmgr.exe"))
                elif 'steam' in query:
                    current_dir = r"C:\Program Files (x86)\Steam"
                    subprocess.Popen(os.path.join(current_dir, "steam.exe"))
                elif 'spotify' in query:
                    current_dir = r"C:\Users\guita\AppData\Roaming\Spotify"
                    subprocess.Popen(os.path.join(current_dir, "Spotify.exe"))


            elif 'search' in query:
                query = query.replace('for', '')
                if "wikipedia" in query:
                    try:
                        print('Searching...')
                        speak('Searching...')
                        query = query.replace('search ', '')
                        query = query.replace(' wikipedia', '')


                        results = wiki.summary(query, sentences=1)
                        speak("According to Wikipedia")
                        print("According to Wikipedia : {} ".format(results))
                        speak(results)
                    except Exception as e:
                        print("Could not search wikipedia")
                        speak("Could not search wikipedia")
                if 'movie' in query or 'documentary' in query or 'movies' in query:
                    try:
                        check = query.find(' movies')

                        if check == -1:
                            query = query.replace(' documentary', '')
                        else:
                            query = query.replace(' movies', '')
                            query = query.replace('search', '')
                        print(f'Searching for {query}...')
                        speak(f'Searching database for {query}')
                        moviesDB = imdb.IMDb()
                        movies = moviesDB.search_movie(find_imdb(query))
                        id = movies[0].getID()
                        score = rotten_tomatoes_score(find_imdb(query))
                        movie = moviesDB.get_movie(id)
                        title = movie['title']
                        year = movie['year']
                        rating = movie['rating']
                        directors = movie['directors']
                        casting = movie['cast']
                        this = ''
                        for i in range(8):
                            this += str(casting[i]) + ', '
                        if len(directors) != 1:
                            out = (f'Directed by {str(directors[0])} and ')
                            del directors[0]
                            for i in range(len(directors)):
                                if i != len(directors) - 1:
                                    out += (f'{str(directors[i])} and ')
                                else:
                                    out += (str(directors[i]))
                        else:
                            out = (f'Directed by : {str(directors[0])}')
                        print(
                            f'{title} ({year})\nIMDB - {rating}\nRotten Tomato - {score}')
                        print(out)
                        print(f'Cast includes : {this}')
                        speak(
                            f'{title} is a {year} movie with an IMDB rating of {rating} and a Rotten Tomato score of {score} {out}. Notable cast members include {this}')
                        print('Would you like to hear the synopsis?')
                        speak('Would you like to hear the synopsis?')
                        query = listen().lower()
                        keys = list(movie.keys())
                        if 'yes' in query:
                            if 'plot outline' not in keys:
                                synopsis = movie['plot'][0]
                            else:
                                synopsis = movie['plot outline']
                            print(synopsis)
                            speak(synopsis)
                    except Exception as e:
                        print(f'Could not retrive movie title {e}')
                        speak('Could not retrive movie title')
                elif 'actor' in query or 'actress' in query or 'producer' in query or 'writer' in query or 'director' in query:
                    try:
                        check = {'actor': query.find('actor'), 'actress': query.find('actress'), 'producer': query.find(
                            'producer'), 'writer': query.find('writer'), 'director': query.find('director')}
                        keys = list(check.keys())
                        role = ''
                        for j in keys:
                            if check[j] != -1:
                                query = query.replace(f' {j}', '')
                                role = j
                                break
                        print(f'Searching for {query}...')
                        speak(f'Searching database for {query}')
                        peopleDB = imdb.IMDb()
                        people = peopleDB.search_person(query)
                        id = people[0].getID()
                        person = peopleDB.get_person(id)
                        name = person['name']
                        birth = person['birth date']
                        bio = str(person['mini biography'][0])
                        res = [i for i in range(
                            len(bio)) if bio.startswith('. ', i)]
                        for i in res:
                            if i >= 500:
                                bio = bio[0:i]
                                break
                        keys = list(person['filmography'][0].keys())
                        films = person['filmography'][0][keys[0]]
                        this = ''
                        for i in range(10):
                            this += str(films[i]) + ', '
                            this = this.replace(' ()', '')
                        print(f'{bio}\n{name} is known for {this}')
                        speak(f'{bio}\n{name} is known for {this}')
                    except Exception as e:
                        print('Could not retrive requested information')
                        speak('Could not retrive requested information')
                elif 'series' in query or 'tv' in query:
                    try:
                        check = query.find(' series')
                        if check == -1:
                            query = query.replace(' tv', '')
                        else:
                            query = query.replace(' series', '')
                        print(f'Searching for {query}...')
                        speak(f'Searching database for {query}')
                        seriesDB = imdb.IMDb()
                        query = find_imdb(query)
                        query = query[0:query.find('(TV Series')]
                        res = seriesDB.search_movie(query)
                        id = res[0].getID()
                        score = rotten_tomatoes_score(query)
                        series = seriesDB.get_movie(id)
                        name = series['smart canonical title']
                        kind = series['kind']
                        length = series['series years']
                        keys = list(series.keys())
                        if 'seasons' in keys:
                            seasons = series['seasons']
                        else:
                            seasons = ''
                        rating = series['rating']
                        if 'plot outline' not in keys:
                            synopsis = series['plot'][0]
                        else:
                            synopsis = series['plot outline']
                        casting = series['cast']
                        if seasons != '':
                            print(
                                f'{name} is a {kind} that has an IMDB rating of {rating} and a Rotten Tomato score of {score} with {seasons} seasons. The series has been ongoing from {length}')
                            speak(
                                f'{name} is a {kind} that has an IMDB rating of {rating} and a Rotten Tomato score of {score}with {seasons} seasons. The series has been ongoing from {length}')
                        else:
                            print(
                                f'{name} is a {kind} that has an IMDB rating of {rating} and a Rotten Tomato score of {score}. The series has been ongoing from {length}')
                            speak(
                                f'{name} is a {kind} that has an IMDB rating of {rating} and a Rotten Tomato score of {score}. The series has been ongoing from {length}')
                        this = ''
                        for i in range(8):
                            this += str(casting[i]) + ', '
                        print(f'Cast includes : {this}')
                        speak(f'Cast includes : {this}')
                        print('Would you like to hear the synopsis?')
                        speak('Would you like to hear the synopsis?')
                        query = listen().lower()
                        if 'yes' in query:
                            print(f'{synopsis}')
                            speak(synopsis)
                    except Exception as e:
                        print('Could not retrive requested information')
                        speak('Could not retrive requested information')

                elif 'galaxy' in query:
                    try:
                        query = query.replace('search', '')
                        query = query.replace('galaxy', 'starwars.fandom.com: ')
                        query = query.replace('the', '')
                        query = query.replace('for', '')

                        URL = google_query(query)
                        print(f"the url is {URL[1]}")
                        speak(wookiepedia(URL[1]))
                    except Exception as e:
                        speak("Too many requests")
                elif 'google' in query:
                    try:
                        speak("Searching...")
                        query = query.replace('search ', '')
                        query = query.replace('google ', '')
                        query = query.replace('for ', '')
                        URL = google_query(query)[1]
                        open_browser(URL)
                    except Exception as e:
                        speak("Too many requests")
                elif 'stackoverflow' in query or 'stack overflow' in query:
                    try:
                        speak("Searching...")
                        query = query.replace('search ', '')
                        query = query.replace('stack overflow', 'stackoverflow.com:')
                        query = query.replace('stackoverflow', 'stackoverflow.com:')
                        print(query)
                        query = query.replace('for', '')
                        URL = google_query(query)[0]
                        print(f"the selected url is {URL}")
                        speak(stackoverflow(URL))
                    except Exception as e:
                        speak("Too many requests")

            elif 'what time is it' in query:
                what_time()
            elif 'speed test' in query:
                speed_check()
            elif 'song' in query:
                try:
                    index = query.find('song') + 5
                    if index == 4:
                        print("Please repeat your query")
                        speak("Please repeat your query")
                    else:
                        song = query[index:]
                        data = song_credits(song)
                        print(data)
                        artists = []
                        if data['tracks']['total'] == 0:
                            print("Song could not be found")
                            speak("Song could not be found")
                        else:
                            for i in range(len(data['tracks']['items'][0]['artists'])):
                                artists.append(data['tracks']['items']
                                            [0]['artists'][i]['name'])
                            if artists == 1:
                                print(
                                    f'The artist who sang this song is {artists}')
                                speak(
                                    f'The artist who sang this song is {artists}')
                            else:
                                print(
                                    f'The artists who sang this song are {artists}')
                                speak(
                                    f'The artists who sang this song are {artists}')
                except Exception as e:
                    print(f"An error occured while fetching song data {e}")
                    speak("An error occured while fetching song data")
            elif "turn" in query:
                smartbulb = kasa.SmartBulb(config.bulb1)
                asyncio.run(smartbulb.update())

                if "lights" in query:
                    current_bright = smartbulb.brightness
                    if "off" in query:
                        speak("Turning off lights")
                        asyncio.run(smartbulb.turn_off())
                    elif "on" in query:
                        speak("Turning on lights")
                        asyncio.run(smartbulb.turn_on())
                    elif "down" in query:
                        speak("Dimming lights")
                        if current_bright < 25:
                            speak("Turning off lights")
                            asyncio.run(smartbulb.turn_off())
                        else:
                            try:
                                asyncio.new_event_loop().run_until_complete(smartbulb.set_brightness(current_bright - 25))
                                asyncio.new_event_loop().run_until_complete(smartbulb.update())
                            except Exception as e:
                                speak("Sorry, there was an error")
                                print(e)
                    elif "up" in query:
                        speak("Turning brightness up")
                        print(current_bright)
                        if current_bright > 75:
                            try:
                                asyncio.new_event_loop().run_until_complete(smartbulb.set_brightness(100))
                                asyncio.new_event_loop().run_until_complete(smartbulb.update())
                            except Exception as e:
                                speak("Sorry, there was an error")
                                print(e)
                        else:

                            try:
                                asyncio.new_event_loop().run_until_complete(smartbulb.set_brightness(current_bright + 25))
                                asyncio.new_event_loop().run_until_complete(smartbulb.update())
                            except Exception as e:
                                speak("Sorry, there was an error")
                                print(e)

                    elif "red" in query:
                        try:
                            asyncio.new_event_loop().run_until_complete(smartbulb.set_hsv(0,98,85))
                            asyncio.new_event_loop().run_until_complete(smartbulb.update())
                        except Exception as e:
                            speak("Sorry. error in color change")

                    elif "white" in query:
                        try:
                            asyncio.new_event_loop().run_until_complete(smartbulb.set_hsv(0, 0, 100))
                            asyncio.new_event_loop().run_until_complete(smartbulb.update())
                        except Exception as e:
                            speak("Sorry. error in color change")

                    elif "warm" in query:
                        try:
                            asyncio.new_event_loop().run_until_complete(smartbulb.set_hsv(51, 13, 95))
                            asyncio.new_event_loop().run_until_complete(smartbulb.update())
                        except Exception as e:
                            speak("Sorry. error in color change")

            elif 'location' in query:
                location = get_location()
                print(location)
                speak(f"You are in {location[0]}, {location[1]} at {location[2]} latitude, {location[3]} longitude")
            elif 'weather' in query or 'temperature' in query:
                if 'in' in query and query[query.find('in') + 2:query.find('in') + 3] == ' ':
                    try:
                        city_name = query[query.find('in') + 3:]
                        api_key = config.api_key
                        base_url = 'http://api.openweathermap.org/data/2.5/weather?'
                        complete_url = base_url + "q=" + city_name + "&appid=" + api_key
                        response = requests.get(complete_url)
                        x = response.json()
                        print(x)
                    except Exception as e:
                        print("City could not be found")
                        speak("City could not be found")
                    if x["cod"] == "404":
                        print('Please try again')
                        speak('Please try again')
                    else:
                        temp = (int)(((x["main"]["temp"]) - 273.15)*(9/5)+32)
                        feel = (int)(((x["main"]["feels_like"]) - 273.15)*(9/5)+32)
                        min_ = (int)(((x["main"]["temp_min"]) - 273.15)*(9/5)+32)
                        max_ = (int)(((x["main"]["temp_max"]) - 273.15)*(9/5)+32)
                        sunrise = x["sys"]["sunrise"]
                        sunrise = datetime.datetime.fromtimestamp(
                            sunrise).strftime('%H:%M')
                        sunset = x["sys"]["sunset"]
                        sunset = datetime.datetime.fromtimestamp(
                            sunset).strftime('%H:%M')
                        description = x["weather"][0]["description"]
                        print(
                            f'The temperature is {temp}°F and it feels like {feel} °F\nThe low is {min_}°F and the high is {max_}°F\nThe predicted forecast is {description}')
                        speak(
                            f'The temperature is {temp} degrees Farenheit. It feels like {feel} degrees Farenheit. The low is {min_} degrees Farenheit and the high is {max_} degrees Farenheit. The predicted forecast is {description}')
                else:
                    x = weather(latitude, longitude)
                    if x == False:
                        print('Please try again')
                        speak('Please try again')
                    else:
                        temp = (int)(((x["main"]["temp"]) - 273.15)*(9/5)+32)
                        feel = (int)(((x["main"]["feels_like"]) - 273.15)*(9/5)+32)
                        min_ = (int)(((x["main"]["temp_min"]) - 273.15)*(9/5)+32)
                        max_ = (int)(((x["main"]["temp_max"]) - 273.15)*(9/5)+32)
                        sunrise = x["sys"]["sunrise"]
                        sunrise = datetime.datetime.fromtimestamp(
                            sunrise).strftime('%H:%M')
                        print(sunrise)
                        sunset = x["sys"]["sunset"]
                        sunset = datetime.datetime.fromtimestamp(
                            sunset).strftime('%H:%M')
                        print(sunset)
                        description = x["weather"][0]["description"]
                        print(
                            f'The temperature is {temp}°F and it feels like {feel} °F\nThe low is {min_}°F and the high is {max_}°F\nThe predicted forecast is {description}')
                        speak(
                            f'The temperature is {temp} degrees Farenheit. It feels like {feel} degrees Farenheit. The low is {min_} degrees Farenheit and the high is {max_} degrees Farenheit. The predicted forecast is {description}')
                        speak(f"The sun will rise at {sunrise} and set at {sunset}")

            if "thank you" in query:
                break    
        
        elif "shutdown" in query or "shut down" in query:
            print('Have a wonderful day!')
            speak('Have a wonderful day!')
            break
