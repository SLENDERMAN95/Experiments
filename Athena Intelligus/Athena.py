from bs4 import BeautifulSoup
import requests
from googlesearch import search
import pyttsx3
import speech_recognition as speech
import datetime
import webbrowser


#Init Text->Speech
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
#0 for male, 1 for female
engine.setProperty('voice', voices[1].id)

#Google Search
def google_query(query):
    link = []
    for j in search(query, tld="ca", num=10, stop=10, pause=2):
        link.append(j)
    return link


#Open Browser

def open_browser(url):
    webbrowser.open_new_tab(url)

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
    print("Hi, I am Athena. Your virtual assistant. How can I help?")
    speak("Hi, I am Athena. Your virtual assistant. How can I help?")

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
        print("Instrunction not audible.")
        speak("Im sorry, I could not hear you")
    except speech.RequestError:
        print("Please repeat Intruction")
        speak("Can you say that again?")
        return "None"
    return query


if __name__ == "__main__":
    greet()
    while True:
        query = listen().lower()
        if 'browser' in query:
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
                    URL = google_query(query)[0]
                    open_browser(URL)
            except Exception as e:
                print("Browser could not be opened")
                speak("Browser could not be opened")
        elif 'hello athena' in query:
            speak("Hello, Garrett. How can I assist?")
        elif ('shutdown' in query and query[query.find('shutdown') + 4:query.find('shutdown') + 5] == '') or ('thank you' in query and query[query.find('thank you') + 9:query.find('thank you') + 10] == ''):
            print('Have a wonderful day!')
            speak('Have a wonderful day!')
            break