#!/bin/zsh
# Draft set for review: pink/white hero stills + the seven mode heads on dark.
cd "$(dirname "$0")/.."
B=/Applications/Blender.app/Contents/MacOS/Blender
for c in pink white; do
  $B -b -P tools/render_device.py -- --color $c --out render/draft/hero_$c.png --res 1200x1600 --samples 256 --yaw -20 --camy -0.44 --camz 0.32 --lookz 0.085 > /dev/null 2>&1
done
for m in booster mc derma air dual mask ai; do
  $B -b -P tools/render_device.py -- --color pink --cam head --bg dark --led $m --out render/draft/mode_$m.png --res 800x800 --samples 160 --yaw -20 > /dev/null 2>&1
done
echo DONE
