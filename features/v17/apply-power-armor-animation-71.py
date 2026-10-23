#!/usr/bin/env python3
"""Build 71 candidate: staged, eased GeckoLib suit panel motion.
Run after apply-power-armor-geckolib.py. No inventory/entity transaction changes.
"""
import json, os
from pathlib import Path
root=Path(os.environ["V1_RESOURCE_ROOT"])/"assets/obsidiannetwork/geckolib/animations/entity"
def keys(values):
    return {f"{i/20:.2f}": {"vector":v,"easing":"easeInOutSine"} for i,v in values}
def track(*values):
    return keys(values)
# 20 ticks / 1 second. Stage: unlatch -> split -> raise -> hold.
moves={
 "chest_left":{"rotation":track([0,0,0],[0,-8,0],[0,-35,-3],[0,-67,-7],[0,-74,-8]),
               "position":track([0,0,0],[-.3,0,0],[-2,0,-.6],[-4,0,-1.6],[-5,0,-2])},
 "chest_right":{"rotation":track([0,0,0],[0,8,0],[0,35,3],[0,67,7],[0,74,8]),
               "position":track([0,0,0],[.3,0,0],[2,0,-.6],[4,0,-1.6],[5,0,-2])},
 "helmet":{"rotation":track([0,0,0],[0,0,0],[-8,0,0],[-34,0,0],[-50,0,0]),
           "position":track([0,0,0],[0,0,0],[0,1,0],[0,5,0],[0,7,0])},
 "left_arm":{"rotation":track([0,0,0],[0,0,0],[0,0,-12],[0,0,-31],[0,0,-38])},
 "right_arm":{"rotation":track([0,0,0],[0,0,0],[0,0,12],[0,0,31],[0,0,38])},
 "left_leg":{"rotation":track([0,0,0],[0,0,0],[0,0,-4],[0,0,-13],[0,0,-17])},
 "right_leg":{"rotation":track([0,0,0],[0,0,0],[0,0,4],[0,0,13],[0,0,17])}
}
# Spread keyframes across 0, 0.15, 0.4, 0.75, 1 seconds.
times=["0.0","0.15","0.4","0.75","1.0"]
def normalized(data):
    return {t:{"vector":v,"easing":"easeInOutSine"} for t,v in zip(times,data)}
stages={
 "chest_left":{"rotation":[[0,0,0],[0,-8,0],[0,-35,-3],[0,-67,-7],[0,-74,-8]],"position":[[0,0,0],[-.3,0,0],[-2,0,-.6],[-4,0,-1.6],[-5,0,-2]]},
 "chest_right":{"rotation":[[0,0,0],[0,8,0],[0,35,3],[0,67,7],[0,74,8]],"position":[[0,0,0],[.3,0,0],[2,0,-.6],[4,0,-1.6],[5,0,-2]]},
 "helmet":{"rotation":[[0,0,0],[0,0,0],[-8,0,0],[-34,0,0],[-50,0,0]],"position":[[0,0,0],[0,0,0],[0,1,0],[0,5,0],[0,7,0]]},
 "left_arm":{"rotation":[[0,0,0],[0,0,0],[0,0,-12],[0,0,-31],[0,0,-38]]},
 "right_arm":{"rotation":[[0,0,0],[0,0,0],[0,0,12],[0,0,31],[0,0,38]]},
 "left_leg":{"rotation":[[0,0,0],[0,0,0],[0,0,-4],[0,0,-13],[0,0,-17]]},
 "right_leg":{"rotation":[[0,0,0],[0,0,0],[0,0,4],[0,0,13],[0,0,17]]}
}
for tier in ("mk1","mk2"):
    p=root/f"power_armor_visual_{tier}.animation.json"
    doc=json.loads(p.read_text())
    assert set(doc["animations"])=={"animation.power_armor.open","animation.power_armor.close"}
    opening={bone:{channel:normalized(values) for channel,values in channels.items()} for bone,channels in stages.items()}
    closing={bone:{channel:{t:{"vector":values[4-i],"easing":"easeInOutSine"} for i,t in enumerate(times)} for channel,values in channels.items()} for bone,channels in stages.items()}
    for name,bones in (("open",opening),("close",closing)):
        doc["animations"][f"animation.power_armor.{name}"]={"animation_length":1.0,"loop":"hold_on_last_frame","bones":bones}
    p.write_text(json.dumps(doc,indent=2)+"\n")
print("BUILD71_ANIMATION_CANDIDATE_PASS: 2 tiers, eased staged open/close; inventory logic unchanged")
