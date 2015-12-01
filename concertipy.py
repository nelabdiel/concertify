from flask import Flask, render_template, request, redirect
import simplejson
import requests
import spotipy
import spotipy.util as util
#from requests_oauthlib import OAuth1
from bs4 import BeautifulSoup
from random import randint
import math
from bokeh.util.string import encode_utf8



app = Flask(__name__)

app.vars = {}



#Index page
@app.route('/')
def main():
    return redirect('/index')


#Error page
@app.route('/error-page')
def error_page():
    return render_template('error.html')


#Collecting from index
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    else:
        app.vars['features'] = request.form.getlist('features')

        if app.vars['features'] == '':
            return redirect('/error-page')

        else:
            return redirect('/results')
        
        
@app.route('/results')
def graph():
    
    #Here we open the app credentials

    with open("spotify.json.nogit") as fh:
        secrets = simplejson.loads(fh.read())
    
    
    
    #Here we pull up the list of artists you follow

    token = util.prompt_for_user_token('user-follow-read', client_id = secrets["client_id"], client_secret = secrets["client_secret"], redirect_uri = secrets["redirect_uri"])
    

    if token:
        sp = spotipy.Spotify(auth=token)
        sp.trace = False
        results = sp.current_user_followed_artists(limit=50, after=None)        
    
    Artistsname = []
    Artistslist = []

    for i in range(len(results["artists"]["items"])):
        Artistsname.append(results["artists"]["items"][i]["name"])
        lower = results["artists"]["items"][i]["name"].lower()
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