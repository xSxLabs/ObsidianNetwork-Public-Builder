#!/usr/bin/env python3
"""Generate the 126-cuboid native Hammer model, reconstructed from reference coordinates."""
import os,json,zlib,base64
from pathlib import Path
from PIL import Image,ImageDraw
data=json.loads(zlib.decompress(base64.b64decode("eNrVXO1u3DYQfBf/1hHip6i+ShEURnKODTi+4O6MtAj87uXuUhK5lIKgf8oF2mswl8o7Ws5yllr558P59fzt/Ha/Pfzx58+Hp+vlW/rDSSvjh9Os0seoZv9peLhfEo6wtsoMGX16/HxO/+fPh7fL9f6c/oYb3BDG9E/68nZ5b7Dz4+3OoB/nBnr/zoAvlx9vFfTxMZTRjinQmKJNYYUt2IRqraYh/WneC9bGOIQ4OOcGbVwRcfNFDrvBc+wNjgQaNLNg+AGVU46acTllijLIWA1krAU2diMD8KQcZMbucdFzSJk23tQLicGZB0MzC4YiB4ZlBhXK4jcBAg0eAtWVChKMaNyL38AijYPVgeWi+SJzaPDMosGRR4NmJgw/4nLKYTMyp8xRCJu0hJzyka0sgK2aTPcrK7FKgc5sYWmP4QtbWQsXtrBWMrJWFhSnUYWdmjUqYyWUrBF3C16xUvTiChYyaesVUBFXrqyypq1WTukooVg5Nba1ysGHtFIFTNpKhVTEFapJGdPWqajGKKFOTc3+l7Qdc/ESVaemdvdbqIirUzptflNbqFL34a2ESpUCtb6tVRC/uFpFXNpqhWQkrawRN7+gZgxbr40t4U5FwsfdQ4WALWa6JqPD8cyGw5kMh5ELBzOVGmZMNOwUQUUUibF+44LfODWjdzS7Qkl04coxMi7NF4tYOL7IheMkGI4ukqnxo9QsGeCpyRmTkxi6+01WlnTJSYvN+ueKGWnDORCMg6smNdZcanQ9iSvB9SyuBPNpXAmt53EbuJcLq8yBSFL8UZ5ILO0sjUhGNDL7GukqF60uMBHidDGqPVWYX4qiw2I15gOsRh9GRSNOHqPaE4f5hTZ6TUkjE8yHOJUs56NMJiGfyfW9eTgVwq42Qm5PjLhUtOIIdNbb9c6BiWgUgVkQp4io3N7GkVpeJ6wBidCN78kjcbHy9IGJafVBiRG0fUQ6JDF7OZGkFk0PCjWdlepiAiDg82nYDfWRVvDu1CdBNbolpAC3dBTgkowC2lKxgiz0CKML/Fw04mN13/0JlsPbnsuR2eIHfKRH0dqIOfUBQ44NUiyEPRPFIaO7owwORwqqXDC4GGMo0GKIoUDXEYYCKwYYVpQXpoA3fSIvHorSFHA6hpIUBNSmjUkOmBPJ/PrmYRRuCXMlbQS9Onzk/7+MJFkFclC4EftVxYg6bIi86bJ4pkZnPVwOfrvFkdhksOPzfwOB0ilzcMWZuYG5Nep7fJ9tTxF8jpHHnin1F/qMc4FOYbfp1tARNiMdmrk+3UKAVT2XKwNDB9ikgjIcLZdOVjwUkxSnxg1qXe8ZhTpjdleMNVC3bGRlkcHLDlujyw5bo7TD1tiyw5ZoFf1E9dDQzV+iR9TTaEHP/iBSnOiQw1rjTx5MWlr1MC8RDpswh767Xjs1XHj9Ai2cfoGuPr/ACpe/onXBwYkglx9Sb9Ue7L2nVdV7vUejnIpjZPIFbiNyMP5Qwv9/p2Jw1sHlXqWIXuPJqaaZGy/liTXEa8ZlxHSjM0OWjKFW3na+oDTeeLL2YygXVAAOAXzmGPp0ECNsZlbRwdBU3H/UOToIhDuUgsbnUE45muidSy14C8uKpmL7PwgCVU+4MeDjtehKKvMMVDw8Z4hOyFlQku+gA62qGIp9bgbnRCcVIfSs6hG3gZnamoLClISR0kEzdPsUOnFKM578OGooKwboQUg1B0now23gStH5RYPtLZ1kwBOME4vAbOpe3hFqbLrtM+MxgV3Kc4Cz9tK0nVcPl3ZebAKUXRHYhH1EoDtds/gXWR8moDdVZ/FyUeuD19U61fS+pNOOPgpRNHafbVcKvaqAnjTmgyTekmKrKqAjpbZzpyGlTrXvfpS6zrYdpTZVWDdKPWfbjFKTKqAXpYaz7URzi9p1J4oNZ9OHUnvadR+aX3Jo21DqT+V0odRq7jSh1J1K60HRkDYtKJpXCR0o2NG2/STzKqL/zAf1E7//5DX67z7Rjza9J5lXOb1n9qO89czuVVbnuSq67Hs2Qffdd656LoMv5dx317mqub73q5j77jlXLZcdZyFlCR3npuRdIQvqN+GXcOC6wWHtyW6PoD0ezMzLo91eTzDApqZCZKh6bpM6FhWO8NTn40Obb/EYeOyEh3gcfCfHXyO+XRixSzNK620wjfDZIbXDic1EEcoz0wL/otgOKrzYECp83RIqtNgUCnyHTsB321o6U34bTgwdjb+bYsJXEEs6wBOqQe5NpfChqFs6RFMam5SEyULYbgY6xcQ5wROSNAJmUyFecFQti0k5LYZGqlUQcKx4nGjmNmXJHhNxHrdXP/JdvfliObTh+HJuw3E6uuHocnpT47VUIOqGDZGURiblwONi8gHZFGXZo1RyQbAdz5o5NaJNmerVlbb6aRWPlNcCKGjOhRgKo1K432KAcfO+2RF3732zTWTWN5vKrp1vHflqfI9C78/3ZsfBbW82KMJcb0sGTa8gMoXnLcmUllcOm8LxlmQKwytqma1+1xRvxm1+1yhJbrflgG5XBonV65YsSq97QKNrp1tnZHW6YqiUPjfbWW5zs/vt3+VW62pzuQe56Nnjlkw2jyuGyCnQKB3NUbgiJziQg49qXMcTgp5ehTJ4kKiL8B2+34W/m0bGBmh3ExFk5CHpYScNAWZxJGQBvnq5fX99/Aei+/r+Av+5Xu6P95cLCgiGvvwAd+J+fXy7vS5f4BieoW9unx9fz1iP4Rcb47+fPoaHr9fL+9sXdsFxGHevZtmV4IcuH3Cxp5e/z+21dBwPYmOXw6GQ/EGXu97u38/X2+Xtr+vL1+f78+NOqKcZRoCa69O4HsZWswcof/Af8np+2v8ZM0Tb/ozT7/6Q+/PL9ctvMaGhPXanDL9RcVg/+OV/yeE/Xf35/Pj7SY3Hi+3j419ydSfH")))
assert len(data["elements"])==126
assets=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork"
model=assets/"models/item/hammer.json";model.parent.mkdir(parents=True,exist_ok=True)
elements=[]
for e in data["elements"]:
 faces={k:{"uv":[round(q/32,5) for q in uv],"texture":"#0"} for k,uv in e["faces"].items()}
 elements.append({"from":[round(v,4) for i,v in enumerate(e["from"])],"to":[round(v,4) for v in e["to"]],"faces":faces})
# Preserve all source geometry positions and native hand transforms.
model.write_text(json.dumps({"texture_size":[512,512],"textures":{"0":"obsidiannetwork:item/hammer"},"elements":elements,"display":data["display"]},separators=(",",":"))+"\n")
definition=assets/"items/hammer.json";definition.parent.mkdir(parents=True,exist_ok=True)
definition.write_text(json.dumps({"model":{"type":"minecraft:model","model":"obsidiannetwork:item/hammer"}},indent=2)+"\n")
tex=assets/"textures/item/hammer.png";tex.parent.mkdir(parents=True,exist_ok=True)
# Native texture is generated during build, as with the Multitool.
# Eight 64x64 reference material swatches in each of two atlas rows.
import random,math
im=Image.new("RGBA",(512,512),(0,0,0,0))
pix=im.load()
colors=[(23,20,30),(33,29,43),(45,40,56),(57,48,67),(68,57,76),(81,64,85),(16,13,23),(59,21,76),
        (140,36,216),(202,77,241),(239,166,250),(93,27,141),(104,89,116),(91,36,121),(30,25,41),(166,49,234)]
for tile in range(16):
 x0=(tile%8)*64;y0=(tile//8)*64
 base=colors[tile]
 rng=random.Random(176000+tile)
 for y in range(64):
  for x in range(64):
   grain=rng.randrange(-7,8)
   sheen=0
   if tile>=8:
    sheen=int(24*math.exp(-((x-y-5)/22)**2))
    if tile in (8,9,10,15):sheen+=int(22*math.exp(-((x-y-8)/13)**2))
   edge=18 if (x in (2,3) or y in (2,3)) and tile>=8 else 0
   pix[x0+x,y0+y]=tuple(max(0,min(255,v+grain+sheen+edge)) for v in base)+(255,)
 # Engraved borders and inset bevels from the reference atlas.
 from PIL import ImageDraw
 d=ImageDraw.Draw(im)
 outline=tuple(min(255,v+38) for v in base)+(255,)
 shade=tuple(max(0,v-15) for v in base)+(255,)
 d.line([(x0+3,y0+59),(x0+3,y0+3),(x0+59,y0+3)],fill=shade,width=2)
 d.line([(x0+7,y0+55),(x0+7,y0+7),(x0+55,y0+7)],fill=outline,width=1)
im.save(tex)
print("HAMMER_NATIVE_MODEL_126_CUBES_GENERATED")
