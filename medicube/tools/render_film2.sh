#!/bin/zsh
# Film v2: screen frames -> Blender -> composite -> mp4. Args: resolution samples tag
cd "$(dirname "$0")/.."
RES=${1:-960x540}; SMP=${2:-24}; TAG=${3:-preview}
python3 tools/make_screen_seq.py --shot film2 > /dev/null
rm -rf render/film2 render/film2_comp
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -P tools/shot_film2.py -- --res $RES --samples $SMP --out render/film2/ > render/film2.log 2>&1
echo "rendered $(ls render/film2 | wc -l)"
python3 tools/comp_film2.py render/film2 render/film2_comp
ffmpeg -y -loglevel error -framerate 24 -i render/film2_comp/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart render/film2_$TAG.mp4
ls -la render/film2_$TAG.mp4
