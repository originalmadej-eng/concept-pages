#!/bin/zsh
# Re-render MASK from the existing bake (render/mask_fluid) without re-simulating: shot_mask.py --from_cache loads
# the cached meshes frame by frame. 2026-10-17 (user): no bubble coat on the device (--shell), brighter water (--wdens 1.2).
#   zsh tools/render_mask_cache.sh
cd "$(dirname "$0")/.."
rm -rf render/mask_sim2; mkdir -p render/mask_sim2
/Applications/Blender.app/Contents/MacOS/Blender --factory-startup -b -P tools/shot_mask.py -- --water 1 --from_cache 1 \
  --wdens 1.2 --tilt_in 55 --frames 120 --out render/mask_sim2/ --res 960x540 --samples 32 > render/mask_sim2.log 2>&1
ls render/mask_sim2 | wc -l
