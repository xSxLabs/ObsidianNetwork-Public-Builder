#!/usr/bin/env python3
"""Keep J.A.R.V.I.S. voice settings reachable at Minecraft GUI scale."""
from pathlib import Path
import re

source = Path("features/v177/apply-v177-jarvis-voice.py").read_text(encoding="utf-8")
begin = 'add("client/V177JarvisSettingsScreen.java",r\'\'\''
assert source.count(begin) == 1, "JARVIS settings screen source missing"
screen = source.split(begin, 1)[1].split("\'\'\')", 1)[0]
assert 'flag(x,y+138,"Sleep announcements","sleep");' in screen
assert 'int doneOffset = page == 0 ? 164 : 147;' in screen
assert 'button(x,y+doneOffset,238,"DONE",()->this.onClose());' in screen
assert 'int x=this.width/2-120,y=Math.max(32,this.height/2-125);' in screen

# MC widgets are 20 GUI pixels high. DONE may not cover the seventh row.
sleep_bottom = 138 + 20
done_top = int(re.search(r'page == 0 \? (\d+) :', screen).group(1))
assert done_top - sleep_bottom >= 4, "DONE overlaps Sleep announcements"

# Screenshot-sized GUI (approx. 260 scaled pixels tall) must show both.
height = 260
top = max(32, height // 2 - 125)
first_setting_y = top + 27
assert first_setting_y + done_top + 20 <= height, "DONE falls off screen"
print("V177_JARVIS_VOICE_SETTINGS_LAYOUT_PASS")
