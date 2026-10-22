#!/bin/zsh
# Render all five ad shots, composite, join, encode. Args: resolution samples (default preview 960x540 24)
cd "$(dirname "$0")/.."
RES=${1:-960x540}; SMP=${2:-24}
B=/Applications/Blender.app/Contents/MacOS/Blender
for s in s2 s3 s4 s5; do python3 tools/make_screen_seq.py --shot $s > /dev/null; done
rm -rf render/ad render/ad_comp
for s in s1 s2 s3 s4 s5; do
  $B -b -P tools/shot_ad.py -- --shot $s --res $RES --samples $SMP --out render/ad/$s/ > render/ad_$s.log 2>&1
  echo "rendered $s $(ls render/ad/$s | wc -l)"
done
python3 tools/comp_ad.py render/ad render/ad_comp
ffmpeg -y -loglevel error -framerate 24 -i render/ad_comp/all/f%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart render/ad_film_preview.mp4
ls -la render/ad_film_preview.mp4
