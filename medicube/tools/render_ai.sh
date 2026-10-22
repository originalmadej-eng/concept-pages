#!/bin/zsh
# AI beat v4 (user 2026-10-21): (1) bake the drain — narrow slots over the whole floor (render/ai_fluid4)
# (2) the white-lit pass f1-32 (MASK's water, fading out while it drains) (+ render/ai_path.json)
# (3) the studio pass f1-240 (real sweep and lights, pearl body, slow spin)  (4) comp + mp4.
# v3 (white -> black crossfade, painted beam) is tools/render_ai_v3.sh
#   zsh tools/render_ai.sh <ver> [bake|white|studio|comp]   (no step = all)
cd "$(dirname "$0")/.."
V=${1:-v4}; S=${2:-all}; FEND=70
B=(/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -P tools/shot_ai.py --)
[[ $S == all || $S == bake ]] && { rm -rf render/ai_fluid4; $B --water 1 --bake 1 --norender 1 --fend $FEND --slots 4 > render/ai_bake4.log 2>&1; }
[[ $S == all || $S == white ]] && { rm -rf render/ai_white; $B --water 1 --from_cache 1 --fend $FEND --bg white --f0 1 --f1 32 --path 1 --out render/ai_white/ > render/ai_white.log 2>&1; }
[[ $S == all || $S == studio ]] && { rm -rf render/ai_studio; $B --water 1 --from_cache 1 --fend $FEND --bg studio --out render/ai_studio/ > render/ai_studio.log 2>&1; }
rm -rf render/ai_c4; python3 tools/comp_ai.py render/ai_c4
ffmpeg -y -loglevel error -framerate 24 -i render/ai_c4/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 render/ai_$V.mp4
echo render/ai_$V.mp4
