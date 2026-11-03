#!/usr/bin/env python3
"""B964 startup hotfix: prevent duplicate NeoForge key category registration.

Crash in Build 963:
ClientModEvents.xsxRegisterPowerArmorKeys called registerCategory for
obsidiannetwork:network_storage even though the Network Storage keymap
listener had already registered that exact category.

Keep the single shared category ID and every registered key binding; remove
only the second category registration from the Power Armor listener.
"""
import os,re
from pathlib import Path

root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
client=root/"client/ClientModEvents.java"
power=root/"powerarmor/PowerArmorExitKeyClient.java"
flight=root/"client/V176CreativeFlightParticles.java"
assert all(x.is_file() for x in (client,power,flight)), "B964_MISSING_GENERATED_CLIENT_SOURCE"
src=client.read_text(encoding="utf-8")
m=list(re.finditer(
 r'\bxsxRegisterPowerArmorKeys\s*\(\s*(?:[\w.]+\.)?RegisterKeyMappingsEvent\s+([A-Za-z_$][\w$]*)\s*\)\s*\{',
 src))
assert len(m)==1, ("B964_POWER_ARMOR_KEY_LISTENER_DRIFT",len(m))
name=m[0].group(1)
start=m[0].end()
level=1
end=None
for i in range(start,len(src)):
 if src[i]=="{":level+=1
 elif src[i]=="}":
  level-=1
  if level==0:
   end=i
   break
assert end is not None, "B964_METHOD_UNTERMINATED"
body=src[start:end]
# Do not remove or relocate any key registrations. Only the category is
# redundant, because the existing Network Storage listener owns its ID.
pattern=(r'(?m)^[ \t]*'+re.escape(name)+
 r'\.registerCategory\(\s*(?:dev\.obsidiannetwork\.powerarmor\.)?'
 r'PowerArmorExitKeyClient\.CATEGORY\s*\);[ \t]*\r?\n')
new_body,count=re.subn(pattern,'',body)
assert count==1,("B964_DOUBLE_CATEGORY_CALL_DRIFT",count,body[:500])
assert "registerCategory(" not in new_body, "B964_MULTIPLE_POWER_ARMOR_CATEGORY_CALLS"
assert new_body.count(".register(")==body.count(".register(")>=2, "B964_KEY_MAPPING_REGISTRATION_CHANGED"
src=src[:start]+new_body+src[end:]
client.write_text(src,encoding="utf-8")
pc=power.read_text(encoding="utf-8")
fc=flight.read_text(encoding="utf-8")
# All existing bindings use the same category object/ID; no new category.
assert 'Identifier.fromNamespaceAndPath("obsidiannetwork","network_storage")' in pc, "B964_CATEGORY_ID_CHANGED"
assert "PowerArmorExitKeyClient.CATEGORY" in fc, "B964_FLIGHT_CATEGORY_CHANGED"
assert "registerCategory(" not in src[start:start+len(new_body)], "B964_DOUBLE_REGISTRATION_REMAINING"
# Make the root cause verifiable even without starting the graphics client.
print("B964_STARTUP_CATEGORY_DEDUPLICATED_ONE_SHARED_XSXLABS_NETWORK_STORAGE_CATEGORY_KEYS_PRESERVED PASS")
