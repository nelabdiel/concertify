#stuff we need.
import os
from flask import Flask, render_template, request, redirect
import simplejson
import requests
from requests_oauthlib import OAuth1
from bs4 import BeautifulSoup
from random import randint
import math
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

app.var={}

#Index page
@app.route('/')
def main():
    return redirect('/index')
    
      

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    
    else:
        return redirect('/login')
      
        
@app.route('/login')
def login():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key,urllib.parse.quote(val)) for key,val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
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
    Artistsname = []
    Artistslist = []

    for i in range(len(artists)):
        Artistsname.append(artists[i]["name"])
        lower = artists[i]["name"].lower()
        artist = lower.replace(" ","-")
        Artistslist.append(artist)       
        
        
    links = []

    for i in range(len(Artistslist)):
        links.append("".join(["http://concerts.eventful.com/", Artistslist[i]]))

    #Here we pull up the concerts for an artist
    x = randint(1, len(links)-1)


    while BeautifulSoup(requests.get(links[x]).content).find_all("tr") == [] or x==0:
        x = (x+1)%(len(links)-1)

    rows = BeautifulSoup(requests.get(links[x]).content).find_all("tr")    
    
    tdlist = []
    for row in rows:
        tdlist.append(row.find_all("td")) 
    

    linkx = []
    namex = []
    cityx = []
    placex = []
    datex = []
    Eventx = []
    for i in range(1, len(tdlist)): 
        for link in tdlist[i][1].find_all("a"):
            linkx.append(str(link.get("href")))    
    
        namex.append(str(tdlist[i][1].find_all("span"))[23:][:-8])
        cityx.append(str(tdlist[i][2].find_all("span")[2])[33:][:-7])
        placex.append(str(tdlist[i][2].find_all("span")[3])[31:][:-7])
        for element in tdlist[i][0].find_all("meta"):
            datex.append(element.get("content"))


        
    artist=Artistslist[x]
        
    html = render_template(
        'results.html',
        artist=Artistsname[x], link=linkx[0], name=namex[0], city=cityx[0], place=placex[0],
        date=datex[0]
    )
    return encode_utf8(html)
        
        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 