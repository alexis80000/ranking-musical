from flask import Flask, render_template, request, jsonify
import csv
import requests

app = Flask(__name__)

CSV_FILE = 'charts.csv'
SPOTIFY_CLIENT_ID = 'f20dfa6f158b4217aa4aa6dc432f6a88'
SPOTIFY_CLIENT_SECRET = '84eb369e461144cd87d103d8dc610375'

# Função para obter o token de acesso do Spotify
def get_spotify_token():
    url = "https://accounts.spotify.com/api/token"
    data = {"grant_type": "client_credentials"}
    auth = (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    response = requests.post(url, data=data, auth=auth)
    
    if response.status_code != 200:
        print("Erro ao obter token:", response.status_code, response.text)
        return None
    
    token = response.json().get("access_token")
    return token

# Função para buscar a capa do álbum no Spotify
def get_spotify_album(artist, title):
    token = get_spotify_token()
    if not token:
        print("Erro: Token não foi gerado.")
        return None

    headers = {"Authorization": f"Bearer {token}"}
    query = f"{title} {artist}"
    url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"
    response = requests.get(url, headers=headers)

    data = response.json()
    tracks = data.get("tracks", {}).get("items", [])
    if not tracks:
        return None

    return tracks[0]["album"]["images"][0]["url"]

# Função para carregar as músicas
def load_charts():
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            charts = list(reader)
            for i, song in enumerate(charts, start=1):
                song["position"] = i
                song["album_cover"] = get_spotify_album(song["artist"], song["title"])
            return charts
    except FileNotFoundError:
        return []

# Função para salvar as músicas
def save_charts(charts):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['position', 'title', 'artist', 'weeks', 'album_cover']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(charts)

@app.route('/')
def index():
    charts = load_charts()
    return render_template('index.html', charts=charts)

@app.route('/add', methods=['POST'])
def add_song():
    # Receber dados enviados via JSON
    data = request.get_json()
    title = data['title']
    artist = data['artist']
    weeks = data['weeks']
    
    album_cover = get_spotify_album(artist, title)
    charts = load_charts()
    new_song = {
        'position': len(charts) + 1,
        'title': title,
        'artist': artist,
        'weeks': weeks,
        'album_cover': album_cover
    }
    charts.append(new_song)
    save_charts(charts)  # Salvar as músicas no arquivo CSV
    
    return jsonify({'status': 'success'})  # Retornar sucesso

if __name__ == '__main__':
    app.run(debug=True)
