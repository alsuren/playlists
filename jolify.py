import simplejson
import re

LISTING_FORMAT = ["link", "artist", "name",
        "label", "number", "matrix", "year", "artists"]

bracketmatcher = re.compile(r" *\(.*\)")
def delete_brackets(string):
    newstring = bracketmatcher.sub("", string)
    return newstring

quotesmatcher = re.compile(r""" *['"].*['"]""")
def delete_quotes(string):
    return quotesmatcher.sub("", string)

def normalize(string_):
    string = delete_brackets(string_)
    string = string.lower().strip()
    return string
        

def normalize_name_tag(string):
    name_tag = normalize(string).replace(':', '')
    for sep in [" - ", " feat. "]:
        name, sep, rest = name_tag.partition(sep)
	if rest:
	    return name
    return name_tag

def parse_artist_tag(string):
    artists = []
    artist_tag = normalize(string)
    for sep in [" w ", " et ", " and ", " & ", "'s ", " orch",
		" sextet", " quintet", " quartet", " trio"]:
        artist, sep, rest = artist_tag.partition(sep)
        if rest:
            artists.append(artist)
            break
    else:
        artists.append(artist_tag)

    for sep in [" feat. ", " w "]:
        artist, sep, feature = artist_tag.partition(sep)
        if feature:
            artists.append(feature)

    return artists

listings = open("listing.txt")
listings.next()
structured_listing = []
previous_line = ""
for lineno, line in enumerate(listings):
    splitline = line.split("\t")
    if len(splitline) < len(LISTING_FORMAT):
        print "problem on line", lineno
        print repr(previous_line)
        print repr(line)
        continue
    song = dict(zip(LISTING_FORMAT, splitline))
    structured_listing.append(song)
    previous_line = line

structured_listing.sort(key=lambda x: x["link"].rpartition('/')[-1])

def get_artist_list(song):
    artists = parse_artist_tag(song["artist"])
    artists_tag = normalize(song["artists"])
    artists_tag = artists_tag.replace(" and ", ", ")
    artists_tag = artists_tag.replace(" or ", ", ")
    artists_tag = re.sub("[^,]* by ", "", artists_tag)
    split_artists_tag = artists_tag.split(", ")
    split_artists_tag = [delete_quotes(name)
            for name in split_artists_tag if " " in name]
    if len(split_artists_tag) > 1:
            artists = artists + split_artists_tag

    return artists


songs_by_artist_name = {} # {artist: {name: [songdetails]}}
songs_by_name_artist = {} # {name: {artist: [songdetails]}}
for song in structured_listing:
    song_name = normalize_name_tag(song["name"])
    artists = get_artist_list(song)

    for artist in set(artists):
        songs_by_name = songs_by_artist_name.setdefault(artist, {})
        songs = songs_by_name.setdefault(song_name, [])
        songs.append(song)

#Transpose
for artist, songs_by_name in songs_by_artist_name.iteritems():
    for song_name, songs in songs_by_name.iteritems():
        by_artist = songs_by_name_artist.setdefault(song_name, {})
        songs = by_artist.setdefault(artist, songs)


playlist = simplejson.load(open("Filed/Bal/011--bal_killer--"
        "spotify_user_alsuren_playlist_6LaCJqhVMoM5dL8nxku9EP.json"))

for spotify_song in playlist["songs"]:
    if not spotify_song:
        continue
    song_name = normalize_name_tag(spotify_song["name"])
    if song_name not in songs_by_name_artist:
        print spotify_song
        continue
        
    songs_by_artist = songs_by_name_artist[song_name]
    for artist in spotify_song["artists"]:
        artist = normalize(artist)
        if artist in songs_by_artist:
            songs = songs_by_artist[artist]
            jol_links = spotify_song.setdefault("jol_links", [])
            for song in songs:
                jol_links.append(song["link"])
    if "jol_links" not in spotify_song:
        fallbacks = {}
	for artist, songs in songs_by_artist.items():
	    links = []
	    for song in songs:
	        links.append(song["link"])
	    fallbacks[artist] = links
	if fallbacks:
            spotify_song["jol_fallbacks"] = fallbacks
	else:
	    print spotify_song
	    continue

