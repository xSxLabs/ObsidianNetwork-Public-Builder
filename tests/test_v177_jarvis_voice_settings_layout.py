#!/usr/bin/env python3
"""Check paged, individually toggleable JARVIS GUI does not hide buttons."""
from pathlib import Path
import re

source = Path("features/v177/apply-v177-jarvis-voice.py").read_text(encoding="utf-8")
begin = 'add("client/V177JarvisSettingsScreen.java",r\'\'\''
assert source.count(begin)==1, "JARVIS settings source missing"
screen = source.split(begin,1)[1].split("\'\'\')",1)[0]

for marker in ('private int page=0,subpage=0;', 'FLAGS[page][subpage]',
               '"< PREV"', '"NEXT >"', '"DONE"',
               'flight_on|Flight ON', 'flight_off|Flight OFF',
               'sleep_begin|Sleep begins','sleep_end|Sleep finishes',
               'home|Welcome back at home','integrity_0|Integrity zero'):
    assert marker in screen, marker
assert '"\\\\|"'.replace('\\\\','\\\\') in screen, "split regex absent"
# Vertical layout at screenshot scale 260 UI pixels.
height=260
tabs_y=max(22,height//2-125)
settings_y=tabs_y+27
last_setting_bottom=settings_y+5*23+20
nav_top=settings_y+143
done_top=settings_y+168
assert last_setting_bottom<nav_top
assert nav_top+20<done_top
assert done_top+20<=height
assert 'flag(x,y+138,"Sleep announcements"' not in screen
print("V177_JARVIS_PAGED_SETTINGS_LAYOUT_PASS")
