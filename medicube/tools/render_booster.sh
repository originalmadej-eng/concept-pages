#!/bin/zsh
# BOOSTER beat (strawberry shortcake, user 2026-10-21/22): render (Blender, transparent) -> comp -> mp4
#   zsh tools/render_booster.sh <ver> [render|comp]   (no step = both)
cd "$(dirname "$0")/.."
V=${1:-v1}; S=${2:-all}
[[ $S == all || $S == render ]] && { rm -rf render/booster; /Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -P tools/shot_booster.py -- --out render/booster/ > render/booster.log 2>&1 || exit 1; }
rm -rf render/booster_c; python3 tools/comp_booster.py render/booster render/booster_c || exit 1
ffmpeg -y -loglevel error -framerate 24 -i render/booster_c/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 render/booster_$V.mp4 && echo render/booster_$V.mp4
