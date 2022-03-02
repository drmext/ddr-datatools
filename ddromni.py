from pathlib import Path
import subprocess
import sys
from shutil import copyfile, rmtree
import re
import json
import math
import lxml.etree as ET
from lxml.builder import E

#### hashing the mcode resulted in collisions
####
#
# def crc16_arc(data):
#     crc = 0x0000
#     for i in (range(0, len(data))):
#         crc ^= data[i]
#         for j in range(0, 8):
#             if (crc & 0x0001) > 0:
#                 crc = (crc >> 1) ^ 0xA001
#             else:
#                 crc = crc >> 1
#     return crc     

required = [
    'ffmpeg.exe',
    'magick.exe',
    Path('x86', 'XactBld.exe'),
    'jacket_thumbnails_ja_8.arc',
    'startup.arc',
]
missing = []
for file in required:
    if not Path(file).exists():
        missing.append(file)
if missing:
    raise SystemExit("MISSING REQUIRED FILES:\n" + '\n'.join(map(str, missing)))

if not Path('packages').is_dir():
    raise SystemExit("MISSING packages FOLDER FROM ddrextreme_omnimix.rar")

contents = Path('contents')
output = Path('output')
xact = Path('x86', 'XactBld.exe')
Path(contents, 'data', 'arc', 'jacket').mkdir(parents=True, exist_ok=True)
Path(contents, 'data', 'arc', 'thumbnail').mkdir(parents=True, exist_ok=True)
Path(contents, 'data', 'mdb_apx', 'ssq').mkdir(parents=True, exist_ok=True)
Path(contents, 'data', 'sound', 'win', 'dance').mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, 'arcutils_extract.py', 'startup.arc'])
Path.rename(Path('data'), Path('startup'))
if Path('jacket_thumbnails_ja_8.arc').is_file():
    region = 'ja'
elif Path('jacket_thumbnails_ua_8.arc').is_file():
    region = 'ua'
subprocess.run([sys.executable, 'arcutils_extract.py', f'jacket_thumbnails_{region}_8.arc'])



existing = ['inst', 'name', 'netp', 'scal', 'selc', 'sele', 'stae', 'staf', 'titl']
xml_parser = ET.XMLParser(remove_blank_text=True)
mdb = ET.parse(str(Path('startup', 'gamedata', 'musicdb.xml')), xml_parser).getroot()
for music in mdb:
    existing.append(music.find('basename').text)


skipped = []
mcode = 79999
for packages in Path('packages').glob('*'):
    basename = packages.name
    info = Path(packages, 'package.json')
    with open(info) as package_json:
        json_data = json.load(package_json)
    # excess example for what must be accounted for when expanding to packages other than Extreme, as the formats vary:
    if basename not in existing and json_data.get('_origin') == 'extreme' and Path(packages, f'{basename}_th.png').exists() and Path(packages, f'{basename}_bk.png').exists() and Path(packages, 'song.mp3').exists() and Path(packages, 'preview.mp3').exists() and Path(packages, 'all.csq').exists():
        thumb_input = Path(packages, f'{basename}_th.png')
        jacket_input = Path(packages, f'{basename}_bk.png')
        song_input = Path(packages, 'song.mp3')
        prev_input = Path(packages, 'preview.mp3')
        csq = Path(packages, 'all.csq')

        Path(output, basename, 'Win').mkdir(parents=True, exist_ok=True)
        Path(output, basename, 'data', 'jacket').mkdir(parents=True, exist_ok=True)

        thumb_output = Path(output, basename, f'{basename}_tn.dds')
        jacket_output = Path(output, basename, 'data', 'jacket', f'{basename}_jk.dds')
        song_output = Path(output, basename, f'{basename}.wav')
        prev_output = Path(output, basename, f'{basename}_s.wav')
        ssq = Path(output, basename, f'{basename}.ssq')
        xap = Path(output, basename, f'{basename}.xap')

        subprocess.run(f'magick.exe convert {thumb_input} -background black -gravity center -resize 192x192! -extent 192x192 -flatten {thumb_output}')
        subprocess.run(f'magick.exe convert {jacket_input} -background black -gravity center -resize 512x512! -extent 512x512 -flatten {jacket_output}')

        subprocess.run(f'ffmpeg -ss 0.0507 -i {song_input} -af "apad=pad_dur=1" {song_output} -loglevel error')
        subprocess.run(f'ffmpeg -i {prev_input} -af "volume=6dB" {prev_output} -loglevel error')

        copyfile(csq, ssq)

        # this will be required if functionality is expanded to other origins
        if json_data.get('_origin') != "extreme":
            chart = bytearray(open(ssq, "rb").read())
            chunks = []
            while len(chart) > 0:
                chunk_size = int.from_bytes(chart[:4], 'little')
                if chunk_size == 0:
                    chunks.append([])
                    chart = chart[4:]
                else:
                    chunks.append(chart[4:chunk_size])
                    chart = chart[chunk_size:]
            for idx, chunk in enumerate(chunks):
                if not chunk:
                    continue
                chunk_type = int.from_bytes(chunk[:2], 'little')
                if chunk_type != 1:
                    continue
                time = int.from_bytes(chunk[2:4], 'little')
                count = int.from_bytes(chunk[4:6], 'little')
                if time == 0x96:
                    continue
                diff = 0x96 // time
                if diff != 0x96 / time:
                    print("Is not a clean division", time, 0x96)
                    exit(1)
                idx = 0x08 + count * 4
                for x in range(0, count * 4, 4):
                    point = int.from_bytes(chunk[idx+x:idx+x+4], 'little') * diff
                    print("%08x" % point)
                    chunk[idx+x:idx+x+4] = int.to_bytes(point, 4, 'little')
                chunk[2] = 0x96
                chunk[3] = 0
            chart = bytearray(b"".join([int.to_bytes(len(x) + (4 if x else 0), 4, 'little') + bytearray(x) for x in chunks]))
            open(ssq, "wb").write(chart)

        with open('dummy.xap', 'r') as f:
            with open(xap, 'w') as o:
                o.write(re.sub(r"DUMMY", basename, f.read()))

        subprocess.run(f'{xact} {xap} {Path(output, basename)} /WIN32 /F')

        title = json_data['title']
        title_yomi = ''.join(title.split()).lower()
        title_yomi = ''.join(e for e in title_yomi if e.isalnum())
        artist = json_data.get('artist', 'OMNIMIX')
        bpm_max = json_data['bpms'][0]
        bpm_min = json_data['bpms'][1]

        SPL = math.floor(json_data.get('difficulties', {}).get('single', {}).get('light', 0) * 1.5)
        SPS = math.floor(json_data.get('difficulties', {}).get('single', {}).get('standard', 0) * 1.5)
        SPH = math.floor(json_data.get('difficulties', {}).get('single', {}).get('heavy', 0) * 1.5)
        SPO = math.floor(json_data.get('difficulties', {}).get('single', {}).get('challenge', 0) * 1.5)
        DPL = math.floor(json_data.get('difficulties', {}).get('double', {}).get('light', 0) * 1.5)
        DPS = math.floor(json_data.get('difficulties', {}).get('double', {}).get('standard', 0) * 1.5)
        DPH = math.floor(json_data.get('difficulties', {}).get('double', {}).get('heavy', 0) * 1.5)
        DPO = math.floor(json_data.get('difficulties', {}).get('double', {}).get('challenge', 0) * 1.5)

        diff_level = [0, SPL, SPS, SPH, SPO, 0, DPL, DPS, DPH, DPO]

#        mcode = int(crc16_arc(str.encode(basename)))
        mcode += 1
        bgstage = 3
        series = 8
        diff_level_str = " ".join([str(d) for d in diff_level])

        print('  <music>')
        print(f'    <mcode __type="u32">{mcode}</mcode>')
        print(f'    <basename>{basename}</basename>')
        print(f'    <title>{title}</title>')
        print(f'    <title_yomi>{title_yomi}</title_yomi>')
        print(f'    <artist>{artist}</artist>')
        if bpm_max == bpm_min:
            print(f'    <bpmmax __type="u16">{bpm_max}</bpmmax>')
        else:
            print(f'    <bpmmin __type="u16">{bpm_min}</bpmmin>')
            print(f'    <bpmmax __type="u16">{bpm_max}</bpmmax>')
        print(f'    <series __type="u8">{series}</series>')
        print(f'    <bgstage __type="u16">{bgstage}</bgstage>')
        print(f'    <diffLv __type="u8" __count="10">{diff_level}</diffLv>')
        print('  </music>')

        mdb_entry = E.music(
            E.mcode(str(mcode), __type="u32"),
            E.basename(str(basename), __type="str"),
            E.title(str(title), __type="str"),
            E.title_yomi(str(title_yomi), __type="str"),
            E.artist(str(artist), __type="str"),
            E.bpmmax(str(bpm_max), __type="u16"),
            E.series(str(series), __type="u8"),
            E.bgstage(str(bgstage), __type="u16"),
            E.diffLv(diff_level_str, __type="u8", __count=str(len(diff_level))),
        )

        if bpm_max != bpm_min:
            mdb_entry.append(E.bpmmin(str(bpm_min), __type="u16"))

        mdb.append(mdb_entry)

        print()

        copyfile(ssq, Path(contents, 'data', 'mdb_apx', 'ssq', f'{basename}.ssq'))
        copyfile(Path(output, basename, f'{basename}.xsb'), Path(contents, 'data', 'sound', 'win', 'dance', f'{basename}.xsb'))
        copyfile(Path(output, basename, f'{basename}.xwb'), Path(contents, 'data', 'sound', 'win', 'dance', f'{basename}.xwb'))
        subprocess.run([sys.executable, 'arcutils_create.py', f'{basename}_jk.arc', '--directory', f'{Path(output, basename, "data")}'])
        Path(f'{basename}_jk.arc').rename(Path(contents, 'data', 'arc', 'jacket', f'{basename}_jk.arc'))
        copyfile(thumb_output, Path('data', 'jacket', 'thumbnail', f'{basename}_tn.dds'))


    else:
        skipped.append(basename)
subprocess.run([sys.executable, 'arcutils_create.py', f'jacket_thumbnails_{region}_8.arc_omni'])
Path(f'jacket_thumbnails_{region}_8.arc_omni').rename(Path(contents, 'data', 'arc', 'thumbnail', f'jacket_thumbnails_{region}_8.arc'))
rmtree(Path('data'))
rmtree(output)

print('Already exist in the mdb:')
print(len(skipped))
print(skipped)

# sort mdb by mcode
mdb[:] = sorted(mdb, key=lambda x:int(x.find('mcode').text))

open("omni_musicdb.xml", "wb").write(ET.tostring(mdb, pretty_print=True, method='xml', encoding='utf-8', xml_declaration=True))
Path.rename(Path('startup'), Path('data'))
copyfile("omni_musicdb.xml", Path('data', 'gamedata', 'musicdb.xml'))
subprocess.run([sys.executable, 'arcutils_create.py', 'startup.arc_omni'])
Path('startup.arc_omni').rename(Path(contents, 'data', 'arc', 'startup.arc'))
rmtree(Path('data'))
