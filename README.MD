# GST and StepMania conversions

`ddr-render.py` mass converts xwb and ssq files to mp3 and ogg/.sm

Choose between scharfrichter (default), rhythmcodex, ddrcharttool, or none (GST only)

## USAGE:
```
Arguments:
'-i', '--input', help='Input folder', default="contents/data"
'-o', '--output', help='Output folder', default="output"
'-c', '--sm-converter', help='StepMania tool', default=None, choices=["scharfrichter", "rhythmcodex", "ddrcharttool"]
'-s', '--series', help='Series to process (multiple ex: 19,20)', default='20'
'-t', '--threads', help='Maximum workers for thread pool', default=10
```

External dependencies for processing GST:
- [ffmpeg.exe](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n5.0-latest-win64-gpl-5.0.zip)
- [unxwb](https://aluigi.altervista.org/papers/unxwb.zip)

External dependencies for also processing SM:
- [sox](https://sourceforge.net/projects/sox/files/sox/14.4.2/sox-14.4.2-win32.zip/download)
- [in_place.py](https://pypi.org/project/in-place/#files)
- [romkan](https://pypi.org/project/romkan/#files)
- [scharfrichter/BemaniToSM.exe](https://github.com/SaxxonPike/scharfrichter/releases/download/v0.0/Scharfrichter-0.0.zip) or  [rhythmcodex/RhythmCodex.Cli.exe](https://github.com/SaxxonPike/RhythmCodex) or [ddrcharttool.py](https://github.com/987123879113/gobbletools/blob/master/other/ddrcharttool.py)

A mixture of tools are used:
- three sm converter options because each have their quirks
- unxwb because all other tools extract to normal uncompressed wav instead of the game's raw lossy ADPCM
- sox for converting to ogg because all other tools seem to add padding which introduces an offset requirement
- ffmpeg for mp3 tags
- series prior to A20 are untested, but imagemagick may be required for converting old .dds jackets where RhythmCodex and Pillow break

# Merge music databases
`merge-mdb.py` merges two mdbs and makes a diff (with omni songs only for example)


## USAGE:
1. Run `arcutils_extract.py` to get `musicdb_omni.xml` and `musicdb_new.xml`
2. Run `merge-mdb.py`
- Uncomment lines 82-85 to add " (OmniMIX)" to artist names in the merged output
3. Run `arcutils_create.py` to repack the output `musicdb_merged.xml` or `musicdb_diff.xml` (copy to `data\gamedata\musicdb.xml` first)



# Import system573 songs to A20+ (old)


## USAGE:

1. Extract `packages` folder from ddrextreme_omnimix.rar to here

2. Enable `dotnet3`
- (offline) mount windows iso ADMIN CMD: `dism.exe /online /enable-feature /featurename:NetFX3 /Source:D:\sources\sxs /LimitAccess`

3. Extract dxsdk_aug2007.exe\Utilities\bin\\`x86` folder with 7-zip(Open Inside) to here
- https://archive.org/details/dxsdk_aug2007

4. Extract `magick.exe` and `ffmpeg.exe` to here
- https://download.imagemagick.org/ImageMagick/download/binaries/ImageMagick-7.1.0-portable-Q16-x64.zip
- https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n5.0-latest-win64-gpl-5.0.zip

5. `pip install lxml typing-extensions`

6. Copy contents\data\arc\\`startup.arc` and contents\data\arc\thumbnail\\`jacket_thumbnails_ja_8.arc` to here

7. Run `python3 573-to-a20.py`

8. Copy the resulting contents\ over your original



## Note:
- this is useless now
- artist name is set to OMNIMIX for all added songs because artists are not in the Extreme package.json
- background stage is set to 3 for all added songs
- the diff levels may not be accurate (old_diff \* 1.5 rounded down)
- jacket aspect ratios are messed up
- most preview volume is deep fried (tried to match original preview levels)


## Thanks:
- WF for extracted packages
- DM for original arc tool and lz77 (extract)