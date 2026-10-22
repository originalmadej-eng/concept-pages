#!/bin/zsh
# AIR SHOT beat: render (Blender) -> comp -> mp4.   zsh tools/render_air.sh <version>
cd "$(dirname "$0")/.."
rm -rf render/air render/air_c
B=/Applications/Blender.app/Contents/MacOS/Blender
# the cloud title is held still in frame, so one 3D render of it is enough (with the clouds it cost ~4 min/frame)
rm -rf render/air_text; $B -b -P tools/shot_air.py -- --out render/air_text/ --pass text --still 110 > render/air_text.log 2>&1 || exit 1
$B -b -P tools/shot_air.py -- --out render/air/ --pass scene > render/air.log 2>&1 || exit 1
python3 tools/comp_air.py render/air render/air_c --text "" --text_img render/air_text/f0110.png || exit 1
ffmpeg -y -loglevel error -framerate 24 -i render/air_c/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 render/air_$1.mp4 && echo "OK render/air_$1.mp4"
