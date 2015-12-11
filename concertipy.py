#stuff we need.
import os
from flask import Flask, render_template, request, redirect
import simplejson
import requests
import base64
import json
import urllib
from bokeh.util.string import encode_utf8



app = Flask(__name__)

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters
with open("spotify.json.nogit") as fh:
        secrets = simplejson.loads(fh.read())
        
CLIENT_ID=secrets["client_id"]

CLIENT_SECRET=secrets["client_secret"]

REDIRECT_URI =secrets["redirect_uri"]

SCOPE = "user-follow-read"
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()


auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}

app.vars = {}

#Index page
@app.route('/')
def main():
    return redirect('/index')
    
      

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    
    else:
        app.vars['city'] = request.form['city']
        app.vars['State'] = request.form['State']
        return redirect('/login')
      
        
@app.route('/login')
def login():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key,urllib.parse.quote(val)) for key,val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    #user location
    usercity = app.vars['city']
    userstate = app.vars['State']
    userplace = "{},{}".format(usercity, userstate)
    userplace = userplace.replace(" ", "%20")
    userplace = "{}={}".format('location', userplace)
    
    
    
    
    # Auth Step 2: Requests refresh and access tokens
    auth_token = str(request.args["code"])
    code_payload = {"redirect_uri": REDIRECT_URI, "grant_type":"authorization_code", "code": auth_token}
    base64encoded = base64.b64encode(str(CLIENT_ID + ':' + CLIENT_SECRET).encode())
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, auth=(CLIENT_ID, CLIENT_SECRET))
    
    #Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    #Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer {}".format(access_token)}
    user_follow_read = requests.get("https://api.spotify.com/v1/me/following?type=artist&limit=50", headers=authorization_header)
    user_follow_read_data = json.loads(user_follow_read.text)
    artists = user_follow_read_data["artists"]["items"]
    
      
    #the good stuff
    artists_api = ''

    for i in range(len(artists)):
        lower = artists[i]["name"].lower()
        artist = "{}[]={}".format('artists', lower.replace(" ","%20"))
        artists_api = "{}&{}".format(artists_api, artist)
        
    
    #bandsintown api
    urlbtapi = 'http://api.bandsintown.com/events/search?'
    bttoken = '&format=json&app_id=concertipy'    
    userplace_radius = "{}&{}".format(userplace, 'radius=150')

           

    urlsearch =  "{}{}&{}{}".format(urlbtapi, artists_api, userplace_radius, bttoken)   
    r=requests.get(urlsearch)
    data = json.loads(r.text)
    
    #concert info
    allinfo = []
    for i in range(len(data)):
        
        date = data[i]["datetime"].replace("T", " at ")
        linkevent = data[i]["ticket_url"]
        Artistname = data[i]["artists"][0]["name"]
        venue = data[i]["venue"]["name"]
        eventloc = "{}, {}, {}".format(data[i]["venue"]["city"], data[i]["venue"]["region"], data[i]["venue"]["country"])
        
        allinfo.append((linkevent, Artistname, venue, eventloc, date))
        
    html = render_template('results.html', link=allinfo)
    return encode_utf8(html)
        
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 