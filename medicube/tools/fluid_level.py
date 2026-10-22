"""Water level over time from a Mantaflow mesh cache (domain-normalised z, 90th percentile of the mesh verts).
A steady fall after the splash settles = the sim is losing water.   python3 tools/fluid_level.py render/mask_fluid"""
import glob, gzip, os, struct, sys
import numpy as np
fs = sorted(glob.glob(os.path.join(sys.argv[1], "mesh", "*.bobj.gz")))
for fn in fs[::10] + fs[-1:]:
    b = gzip.open(fn).read(); n = struct.unpack("i", b[:4])[0]
    v = np.frombuffer(b[4:4 + n * 12], np.float32).reshape(-1, 3)
    print(os.path.basename(fn)[11:15], "z90 %.3f  zmax %.3f" % (np.percentile(v[:, 2], 90), v[:, 2].max()))
