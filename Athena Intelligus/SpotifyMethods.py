import spotipy
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import asyncio
import config

scope = f"ugc-image-upload, user-read-playback-state, user-modify-playback-state, user-follow-modify, user-read-private, " \
        f"user-follow-read, user-library-modify, user-library-read, streaming, user-read-playback-position, " \
        f"app-remote-control, user-read-email, user-read-currently-playing, user-read-recently-played, " \
        f"playlist-modify-private, playlist-read-collaborative, playlist-read-private, user-top-read, playlist-modify-public"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=config.client_id, client_secret=
config.client_secret, redirect_uri="http://localhost:8888/callback"), requests_timeout=300)

#Client Controls

async def get_current_song(spotify: Spotify) -> str:
    if spotify.currently_playing() is None:
        return "Nothing is playing"
    song_name = spotify.currently_playing()['item']['name']
    artist_name = spotify.currently_playing()['item']['artists'][0]['name']
    return f"{song_name} - {artist_name}"

async def next_track(spotify: Spotify) -> Spotify:
    return spotify.next_track()

async def pause_track(spotify: Spotify) -> Spotify:
    try:
        if spotify.current_user_playing_track()['is playing'] is True:
            #Verbal paused
            return spotify.pause_playback()
        else:
            #verbal nothing playing
    except Exception as e:
        print(f'error: {e}')

async def resume_track(spotify: Spotify) -> Spotify:
    try:
        if spotify.current_user_playing_track()['is playing'] is False:
            #verval nothing playing
        else:
            return spotify.start_playback()
    except Exception as e:
        print(f'error : {e}')

async def change_volume(spotify: Spotify, volume: int) -> Spotify:
    if volume < 0 or volume > 100:
        #Verbal number between 1 and 100
    else:
        return spotify.volume(volume)

async def repeat_track(spotify: Spotify) -> Spotify:
    try:
        print('Track on Repeat')
        return spotify.repeat("track")
    except Exception as repeat_track_exception:
        print(f'error {repeat_track_exception}')

async def repeat_track(spotify: Spotify, state: str) -> Spotify:
  if state == "on":
      return spotify.shuffle(True)
  elif state == "off":
      return spotify.shuffle(False)
  else:
      raise ValueError("State msut be either on or off")

  #Music Selection

async def play_prev_song(spotify: Spotify) -> Spotify:
    return spotify.previous_track()

async def get_album_uri(spotify: Spotify, name: str) -> str:
    results = spotify.search(q=name, type='album')
    if len(results['albums']['items']) == 0:
        raise InvalidSearchError(f'No albums found with name {name}')
    return results['tracks']['items'][0]['uri']

async def play_album(spotify: Spotify, uri: str) -> str:
    return spotify.start_playback(context_uri=uri)

async def get_artist_uri(spotify: Spotify, name: str) -> str:
    results = spotify.search(q=name, type='album')
    if len(results['artists']['items']) == 0:
        raise InvalidSearchError(f'No artists found with name {name}')
    return results['artists']['items'][0]['uri']

async def play_artist(spotify: Spotify, uri: str) -> str:
    return spotify.start_playback(context_uri=uri)

async def get_track_uri(spotify: Spotify, name: str) -> str:
    results = spotify.search(q=name, type='album')
    if len(results['tracks']['items']) == 0:
        raise InvalidSearchError(f'No artists found with name {name}')
    return results['tracks']['items'][0]['uri']

async def play_track(spotify: Spotify, uri: str) -> str:
    return spotify.start_playback(uris=[uri])




