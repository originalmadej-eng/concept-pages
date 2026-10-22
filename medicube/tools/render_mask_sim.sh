#!/bin/zsh
# MASK with real water (user 2026-10-16: "옆으로 하자" — side-slap entry). Bake and render must be one run:
# a fresh Blender run does not pick up the baked cache. ~2 h bake + ~1 h render.
# --band 5: the default narrow band (3) lost water steadily after the plop (tools/fluid_level.py); 7 and 10 crash at res 282.
#   zsh tools/render_mask_sim.sh <ver>
cd "$(dirname "$0")/.."
V=${1:-v5}
rm -rf render/mask_fluid render/mask_sim; mkdir -p render/mask_sim
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -P tools/shot_mask.py -- --water 1 --bake 1 --fres 282 \
  --mrad 1.2 --fractions 1 --band 5 --snd 0 --crest 1.0 --energy 2.0 --tilt_in 55 --frames 120 --fend 120 \
  --out render/mask_sim/ --res 960x540 --samples 32 > render/mask_sim.log 2>&1
ls render/mask_sim | wc -l
