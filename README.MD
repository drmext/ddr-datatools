# Import DDR EXTREME (system573) songs to A20+


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

7. Run `python3 ddromni.py`

8. Copy the resulting contents\ over your original



## Note:
- this is quickly thrown together and not done in an ideal way; please expand on it or get use out of it as is (I just add a few songs such as sode and cart, but 95 out of 454 will be used from packages if you leave all 454 in the folder. this shouldn't hit any buffer limits on A20+)
- artist name is set to OMNIMIX for all added songs because artists are not in the Extreme package.json
- background stage is set to 3 for all added songs
- the diff levels may not be accurate (old_diff \* 1.5 rounded down)
- jacket aspect ratios are messed up
- most preview volume is deep fried (tried to match original preview levels)


## Thanks:
- WF for extracted packages
- DM for original arc tool and lz77 (extract)