from bs4 import BeautifulSoup
import requests
from googlesearch import search
import pyttsx3
import speech_recognition as speech
import datetime
import webbrowser
import speedtest
import config
import base64
from urllib.parse import urlencode
import config
import kasa
import asyncio

#Init Text->Speech
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
#0 for male, 1 for female
engine.setProperty('voice', voices[1].id)

#Google Search
def google_query(query):
    print("in google_query")
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

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
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

#Weather Function
import config
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

#Speaking

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def listen():
    r = speech.Recognizer()
    with speech.Microphone() as source:
        print("Adjusting for noise")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        print("Intrepreting...")
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


if __name__ == "__main__":
    greet()
    city, country, latitude, longitude = get_location()
    while True:
        query = listen().lower()
        if 'hey athena' in query:  #Wake Keyword
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
                if "lights" in query:
                    smartbulb = kasa.SmartBulb(config.bulb1)
                    if "off" in query:
                        speak("Turning off lights")
                        asyncio.run(smartbulb.turn_off())
                    elif "on" in query:
                        speak("Turning on lights")
                        asyncio.run(smartbulb.turn_on())

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
                        #Something Broken here. Lotta drama for what can be done in one line
                        #now = int(datetime.datetime.now().hour)
                        #temp = sunrise[0:2]
                        #temp = int(temp)
                        #delta_og = int(sunset[0:2])
                        #if delta_og > 12:
                        #    delta = delta_og - 12
                        #if now > temp and now < delta_og:
                        #    minutes = sunset.find(":")
                        #    time = '' + str(delta) + sunset[minutes:]
                        #    print(f"The sun will fall at {time} pm today")
                        #    speak(f"The sun will fall at {time} pm today")
                        #elif now < temp:
                        #    print(f"The sun will rise at {sunrise} am today")
                        #    speak(f"The sun will rise at {sunrise} am today")
            if "thank you" in query:
                break    
        
        elif "shutdown" in query or "shut down" in query:
            print('Have a wonderful day!')
            speak('Have a wonderful day!')
            break
