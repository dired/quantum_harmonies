# This was intended for the frequencies to be mapped upon the notes on the musical scales,
# but it turned out more feasible to iterate through the array of the musical scale itself,
# to build harmonic thirds or fifths

from pytuning.scales import create_edo_scale,create_pythagorean_scale
from pytuning.tuning_tables import create_timidity_tuning,create_csound_tuning,create_scala_tuning,create_fluidsynth_tuning
import numpy as np

scale = np.array(create_edo_scale(12,2),dtype=float)
scales = []
for j in scale:
    scales.append(j)
for i in range(10):
    start = scale[-1]
    scale = scale*2
    for n, j in enumerate(scale):
        if n>0:
            scales.append(j)
print(scales)
notes = []
for i, o in enumerate(scales):
    notes.append(o*55)
print(notes)
