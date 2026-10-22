#!/bin/zsh
# MC and DERMA SHOT jelly beats: render (Blender) -> composite -> mp4.   zsh tools/render_pudding.sh mc|derma <version>
cd "$(dirname "$0")/.."
B=/Applications/Blender.app/Contents/MacOS/Blender
case $1 in
  mc)    A=(--mode mc --frames 72 --text "Bounce Boosting");             C=(--word MC --f_text 22) ;;
  derma) A=(--mode derma --frames 96);  C=(--pinprick "DERMA SHOT" --f_text 12) ;;   # mode name as a needle dot grid (comp)
esac
rm -rf render/pud_$1 render/pud_$1_c
$B -b -P tools/shot_pudding.py -- --out render/pud_$1/ $A > render/pud_$1.log 2>&1 || exit 1
python3 tools/comp_pudding.py render/pud_$1 render/pud_$1_c --phrase "" $C || exit 1
ffmpeg -y -loglevel error -framerate 24 -i render/pud_$1_c/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 render/pudding_$1_$2.mp4 && echo "OK render/pudding_$1_$2.mp4"
