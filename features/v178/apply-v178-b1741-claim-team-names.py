#!/usr/bin/env python3
"""B1741: owner-managed named claim teams, persisted in the same atomic
world-scoped team/claims file. Rename is server-authorized, bounded, and visible
through the existing on-demand team GUI snapshot (no polling).
Apply after B1740 and B1730.
"""
import os
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
def patch(rel,old,new,n=1):
    p=J/rel
    s=p.read_text("utf8")
    assert s.count(old)==n,("B1741_ANCHOR",rel,old[:100],s.count(old))
    p.write_text(s.replace(old,new,n),"utf8")

claim="claims/V178Claims.java"
patch(claim,''' private static final Map<UUID,TeamInvite> TEAM_INVITES=new HashMap<>();''',
''' private static final Map<UUID,TeamInvite> TEAM_INVITES=new HashMap<>();
 private static final Map<UUID,String> TEAM_NAMES=new HashMap<>();
 private static String teamName(UUID leader){
  return TEAM_NAMES.getOrDefault(leader,"Unnamed Team");
 }''')
patch(claim,'''TEAM_MEMBERS.clear();MEMBER_TEAM.clear();TEAM_INVITES.clear();''',
'''TEAM_MEMBERS.clear();MEMBER_TEAM.clear();TEAM_INVITES.clear();TEAM_NAMES.clear();''',n=2)
patch(claim,'''     }else if(s.length==4&&s[0].equals("M")){''',
'''     }else if(s.length==4&&s[0].equals("N")){
      UUID leader=UUID.fromString(s[1]);
      String name=s[2].trim();
      if(name.matches("[A-Za-z0-9 _-]{3,24}"))TEAM_NAMES.put(leader,name);
     }else if(s.length==4&&s[0].equals("M")){''')
patch(claim,'''  for(var team:TEAM_MEMBERS.entrySet())for(UUID member:team.getValue())''',
r'''  for(var entry:TEAM_NAMES.entrySet())
   data.append("N\t").append(entry.getKey()).append('\t')
       .append(entry.getValue()).append("\t-\n");
  for(var team:TEAM_MEMBERS.entrySet())for(UUID member:team.getValue())''')
patch(claim,'''  tell(target,"Claim team invite from "+p.getGameProfile().name()+
       ". Use /xsxchunks team accept within 60 seconds.");''',
'''  tell(target,"Claim team invitation: "+teamName(owner)+" (leader "+
       p.getGameProfile().name()+"). Use /xsxchunks team accept within 60 seconds.");''')
patch(claim,'''  tell(p,"Joined claim team owned by "+invite.owner());''',
'''  tell(p,"Joined claim team: "+teamName(invite.owner())+
       " (owner "+invite.owner()+").");''')
patch(claim,'''   Set<UUID> members=TEAM_MEMBERS.remove(owner);''',
'''   Set<UUID> members=TEAM_MEMBERS.remove(owner);
   boolean hadName=TEAM_NAMES.remove(owner)!=null;''')
patch(claim,'''   if((members==null||members.isEmpty())&&!revokedInvites){''',
'''   if((members==null||members.isEmpty())&&!revokedInvites&&!hadName){''')
patch(claim,'''   if(members!=null&&!members.isEmpty())dirty=true;''',
'''   if((members!=null&&!members.isEmpty())||hadName)dirty=true;''')
patch(claim,'''  tell(p,"Claim team owner: "+leader+" | members "+members.size()+"/"+MAX_TEAM_SIZE);''',
'''  tell(p,"Claim team: "+teamName(leader)+" | owner "+leader+
      " | members "+members.size()+"/"+MAX_TEAM_SIZE);''')
patch(claim,'''  PacketDistributor.sendToPlayer(p,new V178TeamSnapshot(
      leader.toString(),summary.toString()));''',
'''  PacketDistributor.sendToPlayer(p,new V178TeamSnapshot(
      leader.toString(),summary.toString(),teamName(leader)));''')
patch(claim,''' private static int teamList(ServerPlayer p){''',
''' private static int teamRename(ServerPlayer p,String name){
  ensure((ServerLevel)p.level());
  UUID leader=p.getUUID();
  if(MEMBER_TEAM.containsKey(leader)){
   tell(p,"Only your claim team leader may rename the team.");
   return 0;
  }
  String clean=name.trim();
  if(!clean.matches("[A-Za-z0-9 _-]{3,24}")){
   tell(p,"Team name must be 3-24 letters, numbers, spaces, _ or -.");
   return 0;
  }
  if(clean.equals(TEAM_NAMES.put(leader,clean))){
   tell(p,"Team name is unchanged.");return 1;
  }
  dirty=true;
  tell(p,"Claim team renamed to "+clean);
  for(UUID member:TEAM_MEMBERS.getOrDefault(leader,Set.of())){
   ServerPlayer online=p.level().getServer().getPlayerList().getPlayer(member);
   if(online!=null)tell(online,"Your claim team is now named "+clean);
  }
  return 1;
 }
 private static int teamList(ServerPlayer p){''')
patch(claim,'''  root.then(Commands.literal("team")
     .then(Commands.literal("invite")''',
'''  root.then(Commands.literal("team")
     .then(Commands.literal("name")
       .then(Commands.argument("name",StringArgumentType.greedyString())
         .executes(c->teamRename(c.getSource().getPlayerOrException(),
            StringArgumentType.getString(c,"name")))))
     .then(Commands.literal("invite")''')

snap="claims/V178TeamSnapshot.java"
patch(snap,'''public record V178TeamSnapshot(String leader,String members) implements CustomPacketPayload {''',
'''public record V178TeamSnapshot(String leader,String members,String name) implements CustomPacketPayload {''')
patch(snap,'''      buf.writeUtf(p.leader(),40);buf.writeUtf(p.members(),768);''',
'''      buf.writeUtf(p.leader(),40);buf.writeUtf(p.members(),768);
      buf.writeUtf(p.name(),40);''')
patch(snap,'''buf->new V178TeamSnapshot(buf.readUtf(40),buf.readUtf(768))''',
'''buf->new V178TeamSnapshot(buf.readUtf(40),buf.readUtf(768),buf.readUtf(40))''')

screen="client/V178ClaimTeamScreen.java"
patch(screen,''' private EditBox playerInput;''',
''' private EditBox playerInput,teamInput;
 public static String visibleTeamName(){
  V178TeamSnapshot current=snapshot;
  return current==null?"":current.name();
 }''')
patch(screen,'''  private void namedAction(String action){''',
'''  private void renameTeam(){
   if(teamInput==null)return;
   String name=teamInput.getValue().trim();
   if(!name.matches("[A-Za-z0-9 _-]{3,24}")){
    status="Name: 3-24 letters, digits, spaces, _ or -.";
    return;
   }
   send("name "+name);
  }
  private void namedAction(String action){''')
patch(screen,'''int x=width/2-120,y=Math.max(38,(height-265)/2);''',
'''int x=width/2-120,y=Math.max(20,(height-316)/2);''',n=2)
patch(screen,'''   addRenderableWidget(Button.builder(Component.literal("Disband team"),
      btn->send("disband")).bounds(x,y+107,112,20).build());''',
'''   teamInput=new EditBox(font,x,y+106,158,20,Component.literal("Team Name"));
   teamInput.setMaxLength(24);
   teamInput.setHint(Component.literal("Custom team name"));
   addRenderableWidget(teamInput);
   addRenderableWidget(Button.builder(Component.literal("Rename"),
      btn->renameTeam()).bounds(x+164,y+106,76,20).build());
   addRenderableWidget(Button.builder(Component.literal("Disband team"),
      btn->send("disband")).bounds(x,y+133,112,20).build());''')
patch(screen,'''g.fill(x-6,y-22,x+247,y+258,0xe70c2230);''',
'''g.fill(x-6,y-22,x+247,y+291,0xe70c2230);''')
patch(screen,'''    g.text(font,"Player / UUID",x,y+12,0xffe3f4fc);''',
'''    g.text(font,"Player / UUID",x,y+12,0xffe3f4fc);
    g.text(font,"Team name (leader only)",x,y+95,0xffe3f4fc);''')
patch(screen,'''    g.text(font,status,x,y+132,0xffc5e9dd);''',
'''    g.text(font,status,x,y+159,0xffc5e9dd);''')
patch(screen,'''g.text(font,"Requesting team membership...",x,y+153,0xffefcf8e);''',
'''g.text(font,"Requesting team membership...",x,y+180,0xffefcf8e);''')
patch(screen,'''    g.text(font,"Owner: "+data.leader(),x,y+151,0xff93e8a8);''',
'''    g.text(font,"Team: "+data.name(),x,y+179,0xff93e8a8);
    g.text(font,"Owner: "+data.leader(),x,y+192,0xff93e8a8);''')
patch(screen,'''g.text(font,"No members in this team.",x,y+166,0xffd6e2ef);''',
'''g.text(font,"No members in this team.",x,y+209,0xffd6e2ef);''')
patch(screen,'''for(int i=0;i<Math.min(16,members.length);i++)
        g.text(font,(i+1)+". "+members[i],x,y+166+i*8,0xffd6e2ef);''',
'''for(int i=0;i<Math.min(8,members.length);i++)
        g.text(font,(i+1)+". "+members[i],x,y+209+i*9,0xffd6e2ef);
      if(members.length>8)
       g.text(font,"... and "+(members.length-8)+" more",x,y+280,0xffd6e2ef);''')
# Name updates are immediately visible after explicit refresh, not per-frame
# server traffic. Existing ownership / whitelist checks stay server-authoritative.
assert 'Commands.literal("name")' in (J/claim).read_text()
assert 'data.name()' in (J/screen).read_text()
assert "TEAM_NAMES.clear()" in (J/claim).read_text()
print("B1741_PERSISTENT_OWNER_TEAM_NAMES_GUI_INVITES_PACKET_PASS")
