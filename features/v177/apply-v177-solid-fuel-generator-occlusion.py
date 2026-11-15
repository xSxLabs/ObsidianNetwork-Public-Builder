#!/usr/bin/env python3
"""1.7.7: Solid Fuel Generator must not occlude neighboring blocks.

Same narrow property-only correction already used for Nutrinator and
Electric Water Pump in B609. Preserve collision, block shapes, materials,
tile entities, energy generation, fuel consumption, GUI and block models.
"""
import os
from pathlib import Path
import re

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
registrations=[]
# This is a build-time source edit only. Never search blocks during game ticks.
for path in root.rglob("*.java"):
    source=path.read_text(encoding="utf-8")
    for found in re.finditer(
        r'\bBLOCKS\s*\.\s*registerBlock\s*\(\s*"(?:solid_fuel_generator|solid_fuel_gen)"',
        source,
    ):
        registrations.append((path,source,found.start()))
assert len(registrations)==1,(
    "V177_SOLID_FUEL_GENERATOR_REGISTRY_MISSING_OR_DUPLICATE",
    len(registrations),
    [str(x[0]) for x in registrations],
)
path,source,start=registrations[0]
end=source.find(";",start)
assert start<end<start+1600,("V177_SOLID_FUEL_GENERATOR_DECLARATION_DRIFT",str(path))
section=source[start:end+1]
assert ".noOcclusion()" not in section,("V177_SOLID_FUEL_ALREADY_NONOCCLUDING",str(path))
# RegisterBlock's third argument is the exact BlockBehaviour.Properties
# lambda, p -> p.<properties>. Do not touch the constructor or other blocks.
props=list(re.finditer(r'\b([A-Za-z_]\w*)\s*->\s*\1(?=\s*[.])',section))
assert len(props)==1,("V177_SOLID_FUEL_PROPERTIES_SHAPE_DRIFT",str(path),section[:1100])
m=props[0]
patched=section[:m.end()]+".noOcclusion() /* V177_SOLID_FUEL_NO_OCCLUSION */"+section[m.end():]
assert patched.count(".noOcclusion()")==1
assert patched.count("V177_SOLID_FUEL_NO_OCCLUSION")==1
assert patched.replace(".noOcclusion() /* V177_SOLID_FUEL_NO_OCCLUSION */","")==section
path.write_text(source[:start]+patched+source[end+1:],encoding="utf-8")
print("V177_SOLID_FUEL_GENERATOR_NO_OCCLUSION_NEIGHBOR_FACES_PASS",path)
