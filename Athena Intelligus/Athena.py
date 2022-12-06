from bs4 import BeautifulSoup
import requests
from googlesearch import search
import pyttsx3
import speech_recognition as speech
import datetime
import webbrowser
import speedtest

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
    print("Hello, I am Athena. Your virtual assistant. How can I help?")
    speak("Hello, I am Athena. Your virtual assistant. How can I help?")

#Speaking

def speak(audio):
    engine.say(audio)
    engine.runAndWait()

def listen():
    r = speech.Recognizer()
    with speech.Microphone() as source:
        print("Awaiting Command")
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
        print("Please repeat Instruction")
        speak("Can you say that again?")
        return "None"
    return query


if __name__ == "__main__":
    greet()
    while True:
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
                    print('103')
                    query += ' website '
                    print("105")
                    print(query)
                    URL = google_query(query)[1]
                    
                    print(URL)
                    open_browser(URL)
            except Exception as e:
                print(f"Browser could not be opened {e} ")
                speak("Browser could not be opened")
        elif 'hello athena' in query:
            speak("Hello, Garrett. How can I assist?")
        elif 'what time is it' in query:
            what_time()
        elif 'speed test' in query:
            speed_check()
        elif ('shutdown' in query and query[query.find('shutdown') + 4:query.find('shutdown') + 5] == '') or ('thank you' in query and query[query.find('thank you') + 9:query.find('thank you') + 10] == ''):
            print('Have a wonderful day!')
            speak('Have a wonderful day!')
            break
