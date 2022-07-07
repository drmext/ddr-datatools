import argparse
import glob
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image


def check_files(converter = None):
    required = [
        'ffmpeg.exe',
        'unxwb.exe',
        Path(data_path, 'arc', 'startup.arc')
    ]
    if converter:
        required.append(Path('sox', 'sox.exe'))
        required.append(converter)
    missing = []
    for file in required:
        if not Path(file).exists():
            missing.append(file)
    if missing:
        raise SystemExit("MISSING REQUIRED FILES:\n" + '\n'.join(map(str, missing)))


def get_mdb():
    subprocess.run([sys.executable, 'arcutils_extract.py', Path(data_path, 'arc', 'startup.arc')])
    with open(Path('data', 'gamedata', 'musicdb.xml'), 'r', encoding='utf-8') as f:
        mdb = ET.fromstring(f.read())
    return mdb


def get_version_basenames(mdb, games):
    version_basenames = []
    for music in mdb:
        if int(music.find('series').text) in games:
            version_basenames.append(music.find('basename').text)
    return version_basenames


def get_song_info(mdb, basename):
    for music in mdb:
        if music.find('basename').text == basename:
            track = music.find('mcode').text
            base = music.find('basename').text
            title = music.find('title').text
            try:
                yomi = music.find('title_yomi').text
            except AttributeError:
                yomi = title
            artist = music.find('artist').text
            bpm = music.find('bpmmax').text
            game = music.find('series').text
            diffLv = music.find('diffLv').text
            levels = [int(s) for s in diffLv.split(' ')]
    return track, base, title, yomi, artist, bpm, game, diffLv, levels


def get_sanitized_filename(filename):
    homoglyphs = {
            '\\' : '＼',
            '/' : '⁄',
            ':' : '։',
            '*' : '⁎',
            '?' : '？',
            '"' : '',
            '<' : '‹',
            '>' : '›',
            '|' : 'ǀ',
        }
    for bad, good in homoglyphs.items():
        filename = filename.replace(bad, good)
    return filename


def to_fancy_quotes(s):
    quote_chars_counts = {'"': 0}
    output = []
    for c in s:
        if c in quote_chars_counts.keys():
            replacement = (quote_chars_counts[c] % 2 == 0) and '“' or '”'
            quote_chars_counts[c] = quote_chars_counts[c] + 1
            new_ch = replacement
        else:
            new_ch = c
        output.append(new_ch)
    return ''.join(output)


def extract_xwb(basename):
    subprocess.run(f'unxwb.exe {Path(data_path, "sound", "win", "dance", basename+".xwb")}')
    full_song = sorted((Path(s).stat().st_size, s) for s in glob.glob('0000000?.wav'))[-1][1] # preview index changes sometimes
    Path(full_song).rename(f'{basename}.wav')
    for wav in glob.glob('0000000?.wav'):
        Path(wav).unlink()


def extract_jk(basename):
    subprocess.run([sys.executable, 'arcutils_extract.py', Path(data_path, "arc", "jacket", basename+"_jk.arc")])
    if Path("data", "jacket", basename+"_jk.dds").exists():
        subprocess.run(f'rhythmcodex\RhythmCodex.Cli.exe gfx decode-dds {Path("data", "jacket", basename+"_jk.dds")}')


def wav_to_mp3(basename, jacket, title, artist, track, bpm, game, outfile):
    Path(out_path, "mp3").mkdir(parents=True, exist_ok=True)
    artist = artist.replace("\"", "\\\"")
    title = title.replace("\"", "\\\"")
    subprocess.run(f'ffmpeg -i {basename}.wav -i "{jacket}" -map_metadata 0 -map 0 -map 1 -b:a 320k -ar 44100 -metadata title="{title}" -metadata artist="{artist}" -metadata album_artist="Konami" -metadata album="DanceDanceRevolution A3 GST" -metadata date=2022 -metadata track={track} -metadata TBPM={bpm} -metadata disc={game} -metadata comment="{basename}" "{Path(out_path, "mp3", outfile+".mp3")}" -loglevel error')


def ddrcharttool(base, title, artist, levels):
    Path(out_path, "sm", base).mkdir(parents=True, exist_ok=True)
    subprocess.run(f'{sys.executable} ddrcharttool.py -i {str(Path(data_path, "mdb_apx", "ssq", base+".ssq"))} -if ssq -o {str(Path(out_path, "sm", base, base+".sm"))} -of sm')
    subprocess.run(f'sox\sox.exe -V1 -R {base}.wav -C7 {Path(out_path, "sm", base, base+".ogg")} -D -G rate 48000')
    shutil.copy(Path('data', 'jacket', f'{base}_jk.png'), Path(out_path, "sm", base, base+".png"))

    artist = artist.replace("\"", "\\\"")
    title = title.replace("\"", "\\\"")
    with in_place.InPlace(f'{str(Path(out_path, "sm", base, base+".sm"))}', encoding='utf-8') as file:

        # levels.insert(4, levels.pop(0))
        sp_dp = {'Beginner:\n': 0, 'Easy:\n': 0, 'Medium:\n': 0, 'Hard:\n': 0, 'Challenge:\n': 0,}
        sp = 0
        dp = 6

        for line in file:
            if line in sp_dp.keys():
                if sp_dp[line] == 0:
                    line = line.replace(line, line+str(levels[sp])+':\n')
                    sp += 1
                    sp_dp[line] = 1
                else:
                    line = line.replace(line, line+str(levels[dp])+':\n')
                    dp += 1
            line = line.replace(f'#TITLE:Untitled;', f'#TITLE:{title};\n#ARTIST:{artist};\n#BANNER:{base}.png;\n#BACKGROUND:{base}.png;')
            line = line.replace('#MUSIC:song.mp3;', f'#MUSIC:{base}.ogg;')
            if line.strip("\n") != "1:":
                file.write(line)


def rhythmcodex(base, title, artist, levels):
    subprocess.run(f'rhythmcodex\RhythmCodex.Cli.exe ssq decode {Path(data_path, "mdb_apx", "ssq", base+".ssq")} -o {Path(out_path, "sm", base)}')
    subprocess.call(f'sox\sox.exe -V1 -R {base}.wav -C7 {Path(out_path, "sm", base, base+".ogg")} -D -G rate 48000')
    shutil.copy(Path('data', 'jacket', f'{base}_jk.png'), Path(out_path, "sm", base, base+".png"))

    artist = artist.replace("\"", "\\\"")
    title = title.replace("\"", "\\\"")
    with in_place.InPlace(f'{Path(out_path, "sm", base, base+".sm")}', encoding='utf-8') as file:
        for line in file:
            # if line.find("#OFFSET:") > -1:
            #     offset = line[8:-2]
            #     fixed_offset = float(offset) - 0.05
            #     line = line.replace(f'#OFFSET:{offset}', '#OFFSET:%6f'.format(fixed_offset))
            if line.find("// RhythmCodex") > -1:
                date = (line[15:])
                line = line.replace(f'// RhythmCodex {date}', '')
            line = line.replace(f'#TITLE:{base};', f'#TITLE:{title};')
            line = line.replace('#ARTIST:;', f'#ARTIST:{artist};')
            # if not title.isascii():
            #     line = line.replace('#SUBTITLE:;', f'#SUBTITLE:{romkan.to_roma(yomi).upper()};')
            line = line.replace('#BANNER:;', f'#BANNER:{base+".png"};')
            line = line.replace('#BACKGROUND:;', f'#BACKGROUND:{base+".png"};')
            line = line.replace(f'#PREVIEW:{base}-preview.ogg;', '#PREVIEW:;')
            line = line.replace('#NOTES:dance-single::Beginner:1', f'#NOTES:dance-single::Beginner:{levels[0]}')
            line = line.replace('#NOTES:dance-single::Easy:1', f'#NOTES:dance-single::Easy:{levels[1]}')
            line = line.replace('#NOTES:dance-single::Medium:1', f'#NOTES:dance-single::Medium:{levels[2]}')
            line = line.replace('#NOTES:dance-single::Hard:1', f'#NOTES:dance-single::Hard:{levels[3]}')
            line = line.replace('#NOTES:dance-single::Challenge:1', f'#NOTES:dance-single::Challenge:{levels[4]}')
            line = line.replace('#NOTES:dance-double::Beginner:1', f'#NOTES:dance-double::Beginner:{levels[5]}')
            line = line.replace('#NOTES:dance-double::Easy:1', f'#NOTES:dance-double::Easy:{levels[6]}')
            line = line.replace('#NOTES:dance-double::Medium:1', f'#NOTES:dance-double::Medium:{levels[7]}')
            line = line.replace('#NOTES:dance-double::Hard:1', f'#NOTES:dance-double::Hard:{levels[8]}')
            line = line.replace('#NOTES:dance-double::Challenge:1', f'#NOTES:dance-double::Challenge:{levels[9]}')
            file.write(line)


def scharfrichter(base, title, yomi, artist, levels):
    Path(out_path, "sm", base).mkdir(parents=True, exist_ok=True)
    shutil.copy(Path(data_path, "mdb_apx", "ssq", base+".ssq"), Path(out_path, "sm", base, base+".ssq"))
    subprocess.run(f'scharfrichter\BemaniToSM.exe {Path(out_path, "sm", base, base+".ssq")}')
    Path(out_path, "sm", base, base+".ssq").unlink()
    subprocess.run(f'sox\sox.exe -V1 -R {base}.wav -C7 {Path(out_path, "sm", base, base+".ogg")} -D -G rate 48000')
    shutil.copy(Path('data', 'jacket', f'{base}_jk.png'), Path(out_path, "sm", base, base+"-bg.png"))

    Image.open(Path(out_path, "sm", base, base+"-bg.png")).resize((418,164)).save(Path(out_path, "sm", base, base+"-banner.png"))

    artist = artist.replace("\"", "\\\"")
    title = title.replace("\"", "\\\"")

    with in_place.InPlace(f'{Path(out_path, "sm", base, base+".sm")}', encoding='utf-8') as file:
        for line in file:
            if line.strip("\n") not in (":", "Beginner:", "Easy:", "Medium:", "Hard:", "Challenge:"):
                file.write(line)

    with in_place.InPlace(f'{str(Path(out_path, "sm", base, base+".sm"))}', encoding='utf-8') as file:

        diffs = [
            f'dance-single:\n:\nBeginner:\n{levels[0]}:\n',
            f'dance-single:\n:\nEasy:\n{levels[1]}:\n',
            f'dance-single:\n:\nMedium:\n{levels[2]}:\n',
            f'dance-single:\n:\nHard:\n{levels[3]}:\n',
            f'dance-single:\n:\nChallenge:\n{levels[4]}:\n',
            f'dance-double:\n:\nBeginner:\n{levels[5]}:\n',
            f'dance-double:\n:\nEasy:\n{levels[6]}:\n',
            f'dance-double:\n:\nMedium:\n{levels[7]}:\n',
            f'dance-double:\n:\nHard:\n{levels[8]}:\n',
            f'dance-double:\n:\nChallenge:\n{levels[9]}:\n'
        ]
        sp = 0
        dp = 6

        for line in file:
            if line.endswith('single:\n'):
                line = line.replace(line, diffs[sp])
                sp += 1
            elif line.endswith('double:\n'):
                line = line.replace(line, diffs[dp])
                dp += 1
            if not title.isascii():
                rom = romkan.to_roma(yomi).upper()
                rom = rom.replace("'", "")
                line = line.replace(f'#TITLE:{base};', f'#TITLE:{title};\n#SUBTITLE:{rom};')
                line = line.replace(f'#TITLETRANSLIT:;', f'#TITLETRANSLIT:{rom};')
            else:
                line = line.replace(f'#TITLE:{base};', f'#TITLE:{title};')
            line = line.replace('#ARTIST:;', f'#ARTIST:{artist};\n#MUSIC:{base}.ogg;')
            line = line.replace(f'#BANNER:{base}.png;', f'#BACKGROUND:{base}-banner.png;')
            if line.strip("\n") != "0:":
                file.write(line)


def clean_up():
    if Path('data').is_dir():
        shutil.rmtree(Path('data'))
    for wav in glob.glob('*.wav'):
        Path(wav).unlink()


def convert_and_tag(song):
    track, base, title, yomi, artist, bpm, game, diffLv, levels = get_song_info(mdb, song)
    outfile = get_sanitized_filename(to_fancy_quotes(f'{track} - {artist} - {title}'))
    if not Path(out_path, "mp3", outfile+".mp3").exists():
        extract_jk(base)
        wav_to_mp3(base, Path('data', 'jacket', f'{base}_jk.png'), title, artist, track, bpm, game, outfile)
        if args.sm_converter is not None:
            if args.sm_converter.lower() == "scharfrichter":
                scharfrichter(base, title, yomi, artist, levels)
            elif args.sm_converter.lower() == "rhythmcodex":
                rhythmcodex(base, title, artist, levels)
            elif args.sm_converter.lower() == "ddrcharttool":
                ddrcharttool(base, title, artist, levels)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Input folder', default="contents/data")
    parser.add_argument('-o', '--output', help='Output folder', default="output")
    parser.add_argument('-c', '--sm-converter', help='StepMania tool', default=None, choices=["scharfrichter", "rhythmcodex", "ddrcharttool"])
    parser.add_argument('-s', '--series', help='Series to process (multiple ex: 19,20)', default='20')
    parser.add_argument('-t', '--threads', help='Maximum workers for thread pool', default=10)
    args = parser.parse_args()

    data_path = Path(args.input)
    out_path = Path(args.output)

    if args.sm_converter is not None:
        import in_place
        import romkan
        if args.sm_converter.lower() == "scharfrichter":
            check_files(Path('scharfrichter', 'BemaniToSM.exe'))
        elif args.sm_converter.lower() == "rhythmcodex":
            check_files(Path('rhythmcodex', 'RhythmCodex.Cli.exe'))
        elif args.sm_converter.lower() == "ddrcharttool":
            check_files('ddrcharttool')
    else:
        check_files()

    mdb = get_mdb()

    songs = get_version_basenames(mdb, [int(s) for s in args.series.split(",") if s]) # older series might break


    for song in songs:
        if Path(data_path, "sound", "win", "dance", song+".xwb").stat().st_size < 250000:
            songs.remove(song) # don't process dummied removals
        else:
            extract_xwb(song) # extract xwbs with a single worker due to renaming 0000000?.wav (fix this)

    with ThreadPoolExecutor(max_workers=int(args.threads)) as executor:
        executor.map(convert_and_tag, songs)

    clean_up()
