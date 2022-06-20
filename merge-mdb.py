from pathlib import Path
import lxml.etree as ET


mdb_new = ET.parse(str(Path('musicdb_new.xml')), ET.XMLParser()).getroot()
mdb_omni = ET.parse(str(Path('musicdb_omni.xml')), ET.XMLParser()).getroot()


existing_new = []
for entry in mdb_new:
    existing_new.append(entry.find('mcode').text)

existing_omni =[]
for entry in mdb_omni:
    existing_omni.append(entry.find('mcode').text)

omni_songs = list(set(existing_omni) - set(existing_new))
new_songs = list(set(existing_new) - set(existing_omni))


ver = mdb_new[-1].find('series').text
if int(ver) >= 20:
    for entry in mdb_omni:
        # Set cs songs to latest series + 1 to hide them from arcade folders
        if entry.find('series').text == ver:
            entry.find('series').text = str(int(ver) + 1)
            # Set GP mcodes higher to not collide
            if int(entry.find('mcode').text) > 38000:
                entry.find('mcode').text = str(int(entry.find('mcode').text) + 20000)

# Merge new mdb into old mdb
for entry in mdb_new:
    if entry.find('mcode').text in new_songs:
        mdb_omni.append(entry)

# Generate unique title_yomi omnimix values so the game sorts entries alphabetically
alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
titles = []
for entry in mdb_omni:
    for sort_title in alphabet:
        if entry.find('title').text.lower().startswith(sort_title):
            titles.append(entry.find('title').text)

titles_sorted = sorted(titles, key=str.casefold)

title_yomi = {}
count = 0
current_letter = 'a'
previous_letter = 'a'
for entry in titles_sorted:
    for letter in alphabet:
        if entry.lower().startswith(letter):
            current_letter = letter
            if current_letter != previous_letter:
                count = 1
            else:
                count += 1
            previous_letter = letter
            title_yomi[entry] = letter+(str(count).zfill(4))

for entry in mdb_omni:
    k = entry.find('title').text
    if k in title_yomi.keys():
        entry.find('title_yomi').text = title_yomi.get(k)

#    if entry.find('mcode').text in omni_songs or int(entry.find('mcode').text) > 50000:
#        artist = entry.find('artist').text
#        if not artist.endswith(" (OmniMIX)"):
#            entry.find('artist').text = (artist + " (OmniMIX)")

mdb_diff = ET.parse(str(Path('musicdb_omni.xml')), ET.XMLParser()).getroot()
for entry in mdb_diff:
    # Create omni only mdb
    if entry.find('mcode').text not in omni_songs and int(entry.find('mcode').text) < 50000:
        mdb_diff.remove(entry)


for entry in sorted(mdb_omni, key=lambda x:int(x.find('mcode').text)):
    print(f"{entry.find('mcode').text} - {entry.find('artist').text} - {entry.find('title').text}")

## Sort mdb by mcode
#mdb_omni[:] = sorted(mdb_omni, key=lambda x:int(x.find('mcode').text))
open("musicdb_merged.xml", "wb").write(ET.tostring(mdb_omni, pretty_print=True, method='xml', encoding='utf-8', xml_declaration=True))
open("musicdb_diff.xml", "wb").write(ET.tostring(mdb_diff, pretty_print=True, method='xml', encoding='utf-8', xml_declaration=True))


#import subprocess
#from concurrent.futures import ThreadPoolExecutor
#
#def enc_file(song):
#    print(f'Encoding {song} to {song.stem}.wmv')
#    subprocess.run(f'ffmpeg -i {song} -q:v 1 -q:a 1 {song.stem}.wmv -loglevel error')
#
#songs = []
#for song in Path('.').glob('*m2v'):
#    songs.append(song)
#
#with ThreadPoolExecutor(max_workers=10) as executor:
#    executor.map(enc_file, songs)
