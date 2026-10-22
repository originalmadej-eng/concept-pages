#!/bin/zsh
# Continuous ad film: screen frames -> Blender -> composite -> mp4. Args: resolution samples (preview 960x540 24)
cd "$(dirname "$0")/.."
RES=${1:-960x540}; SMP=${2:-24}; TAG=${3:-preview}
python3 tools/make_screen_seq.py --shot film > /dev/null
rm -rf render/film render/film_comp
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -P tools/shot_film.py -- --res $RES --samples $SMP --out render/film/ > render/film.log 2>&1
echo "rendered $(ls render/film | wc -l)"
python3 tools/comp_film.py render/film render/film_comp
ffmpeg -y -loglevel error -framerate 24 -i render/film_comp/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart render/film_$TAG.mp4
ls -la render/film_$TAG.mp4
