#!/usr/bin/env python3
"""v1.7.8 original owner-managed claim teams; permission-limited, persisted.

This patch runs AFTER apply-v178-claims.py and BEFORE apply-v178-ftb-batch.py.
Team members may build/interact with their leader's claimed land, but only
the actual chunk owner can claim/unclaim/force-load, preserving owner quotas.
"""
import os
from pathlib import Path
path=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/claims/V178Claims.java"
source=path.read_text(encoding="utf-8")
def rep(old,new):
 global source
 count=source.count(old)
 assert count==1,("V178_TEAM_SOURCE_DRIFT",old[:110],count)
 source=source.replace(old,new,1)

rep(''' private static final Map<UUID,Set<UUID>> TRUSTED=new HashMap<>();''',
''' private static final Map<UUID,Set<UUID>> TRUSTED=new HashMap<>();
 // Owner is the team leader. Membership is exclusive, and claims remain
 // owned by the individual player, not reassigned during membership changes.
 private static final int MAX_TEAM_SIZE=16;
 private static final Map<UUID,Set<UUID>> TEAM_MEMBERS=new HashMap<>();
 private static final Map<UUID,UUID> MEMBER_TEAM=new HashMap<>();
 private record TeamInvite(UUID owner,long expiresAt){}
 private static final Map<UUID,TeamInvite> TEAM_INVITES=new HashMap<>();''')

rep('''  CLAIMS.clear();TRUSTED.clear();OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();''',
'''  CLAIMS.clear();TRUSTED.clear();TEAM_MEMBERS.clear();MEMBER_TEAM.clear();TEAM_INVITES.clear();
  OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();''')
rep('''    TRUSTED.clear();OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();''',
'''    TRUSTED.clear();TEAM_MEMBERS.clear();MEMBER_TEAM.clear();TEAM_INVITES.clear();
    OWNED_COUNT.clear();LOADED_COUNT.clear();REQUEST_TICKS.clear();REQUEST_CENTERS.clear();''')

rep('''     }else if(s.length==6&&s[0].equals("C")){''',
'''     }else if(s.length==4&&s[0].equals("M")){
      UUID owner=UUID.fromString(s[1]),member=UUID.fromString(s[2]);
      // Fail closed on duplicate, self, multi-team or cyclic team records.
      if(!owner.equals(member)&&!MEMBER_TEAM.containsKey(member)
         &&!MEMBER_TEAM.containsKey(owner)&&!TEAM_MEMBERS.containsKey(member)
         &&TEAM_MEMBERS.getOrDefault(owner,Set.of()).size()<MAX_TEAM_SIZE){
       TEAM_MEMBERS.computeIfAbsent(owner,k->new HashSet<>()).add(member);
       MEMBER_TEAM.put(member,owner);
      }
     }else if(s.length==6&&s[0].equals("C")){''')

rep('''  Path destination=path(active),temporary=null;''',
r'''  // Members persist in the same atomic world-scoped claim save. Pending
  // invitations are deliberately not persisted (no stale privileges).
  for(var team:TEAM_MEMBERS.entrySet())for(UUID member:team.getValue())
   data.append("M\t").append(team.getKey()).append('\t').append(member)
      .append("\t-\n");
  Path destination=path(active),temporary=null;''')

rep('''  return owner==null||owner.equals(player)
      ||TRUSTED.getOrDefault(owner,Set.of()).contains(player);''',
'''  return owner==null||owner.equals(player)
      ||TRUSTED.getOrDefault(owner,Set.of()).contains(player)
      ||TEAM_MEMBERS.getOrDefault(owner,Set.of()).contains(player);''')
rep('''      TRUSTED.getOrDefault(c.owner(),Set.of()).contains(p.getUUID())?2:3;''',
'''      (TRUSTED.getOrDefault(c.owner(),Set.of()).contains(p.getUUID())
       ||TEAM_MEMBERS.getOrDefault(c.owner(),Set.of()).contains(p.getUUID()))?2:3;''')

rep(''' @SubscribeEvent public static void commands(RegisterCommandsEvent event){''',
''' // Team invitations are explicit, online-only, and expire after 60 seconds.
 // No implicit access is granted merely by receiving an invite.
 private static int teamInvite(ServerPlayer p,String name){
  ensure((ServerLevel)p.level());
  UUID owner=p.getUUID();
  if(MEMBER_TEAM.containsKey(owner)){
   tell(p,"Leave your current team before inviting players.");return 0;
  }
  ServerPlayer target=p.level().getServer().getPlayerList().getPlayerByName(name);
  if(target==null||target.getUUID().equals(owner)){
   tell(p,"Invitee must be another online player.");return 0;
  }
  UUID member=target.getUUID();
  if(MEMBER_TEAM.containsKey(member)||TEAM_MEMBERS.containsKey(member)){
   tell(p,"Player already belongs to or leads a team.");return 0;
  }
  if(TEAM_MEMBERS.getOrDefault(owner,Set.of()).size()>=MAX_TEAM_SIZE){
   tell(p,"Team limit is "+MAX_TEAM_SIZE+" members.");return 0;
  }
  long expiry=(long)p.level().getServer().getTickCount()+1200L;
  TEAM_INVITES.put(member,new TeamInvite(owner,expiry));
  tell(p,"Invitation sent to "+name);
  tell(target,"Claim team invite from "+p.getGameProfile().name()+
       ". Use /xsxchunks team accept within 60 seconds.");
  return 1;
 }
 private static int teamAccept(ServerPlayer p){
  ensure((ServerLevel)p.level());
  UUID member=p.getUUID();
  TeamInvite invite=TEAM_INVITES.remove(member);
  if(invite==null||(long)p.level().getServer().getTickCount()>invite.expiresAt()
     ||MEMBER_TEAM.containsKey(member)||TEAM_MEMBERS.containsKey(member)
     ||MEMBER_TEAM.containsKey(invite.owner())
     ||TEAM_MEMBERS.getOrDefault(invite.owner(),Set.of()).size()>=MAX_TEAM_SIZE){
   tell(p,"No valid claim team invitation.");return 0;
  }
  if(!TEAM_MEMBERS.computeIfAbsent(invite.owner(),k->new HashSet<>()).add(member))
   return 0;
  MEMBER_TEAM.put(member,invite.owner());dirty=true;
  tell(p,"Joined claim team owned by "+invite.owner());
  ServerPlayer leader=p.level().getServer().getPlayerList().getPlayer(invite.owner());
  if(leader!=null)tell(leader,p.getGameProfile().name()+" joined your claim team.");
  return 1;
 }
 private static boolean teamUnlink(UUID owner,UUID member){
  if(!owner.equals(MEMBER_TEAM.get(member)))return false;
  MEMBER_TEAM.remove(member);
  var members=TEAM_MEMBERS.get(owner);
  if(members!=null){
   members.remove(member);
   if(members.isEmpty())TEAM_MEMBERS.remove(owner);
  }
  dirty=true;return true;
 }
 private static int teamLeave(ServerPlayer p){
  ensure((ServerLevel)p.level());
  UUID leader=MEMBER_TEAM.get(p.getUUID());
  if(leader==null){tell(p,"Not a claim team member.");return 0;}
  teamUnlink(leader,p.getUUID());
  tell(p,"Left claim team; shared permissions revoked.");
  ServerPlayer owner=p.level().getServer().getPlayerList().getPlayer(leader);
  if(owner!=null)tell(owner,p.getGameProfile().name()+" left your team.");
  return 1;
 }
 private static int teamKick(ServerPlayer p,String nameOrId){
  ensure((ServerLevel)p.level());
  UUID owner=p.getUUID();
  ServerPlayer target=p.level().getServer().getPlayerList().getPlayerByName(nameOrId);
  UUID member=target==null?null:target.getUUID();
  if(member==null){
   try{member=UUID.fromString(nameOrId);}catch(IllegalArgumentException ignored){}
  }
  if(member==null||!teamUnlink(owner,member)){
   tell(p,"Not your team member (offline members require UUID).");return 0;
  }
  tell(p,"Team member removed.");
  if(target!=null)tell(target,"You were removed from the claim team.");
  return 1;
 }
 private static int teamList(ServerPlayer p){
  ensure((ServerLevel)p.level());
  UUID leader=MEMBER_TEAM.getOrDefault(p.getUUID(),p.getUUID());
  var members=TEAM_MEMBERS.getOrDefault(leader,Set.of());
  tell(p,"Claim team owner: "+leader+" | members "+members.size()+"/"+MAX_TEAM_SIZE);
  for(UUID member:members)tell(p,"Member: "+member);
  return 1;
 }
 @SubscribeEvent public static void commands(RegisterCommandsEvent event){''')

rep('''  event.getDispatcher().register(root);''',
'''  root.then(Commands.literal("team")
    .then(Commands.literal("invite")
      .then(Commands.argument("player",StringArgumentType.word())
        .executes(c->teamInvite(c.getSource().getPlayerOrException(),
           StringArgumentType.getString(c,"player")))))
    .then(Commands.literal("accept")
        .executes(c->teamAccept(c.getSource().getPlayerOrException())))
    .then(Commands.literal("leave")
        .executes(c->teamLeave(c.getSource().getPlayerOrException())))
    .then(Commands.literal("kick")
      .then(Commands.argument("player",StringArgumentType.word())
        .executes(c->teamKick(c.getSource().getPlayerOrException(),
           StringArgumentType.getString(c,"player")))))
    .then(Commands.literal("list")
        .executes(c->teamList(c.getSource().getPlayerOrException()))));
  event.getDispatcher().register(root);''')

for token in ("TEAM_MEMBERS", "MEMBER_TEAM", "TEAM_INVITES", 'data.append("M\\t")',
              "teamInvite(ServerPlayer", "teamAccept(ServerPlayer", "teamLeave(ServerPlayer",
              "teamKick(ServerPlayer", 'Commands.literal("team")'):
 assert token in source,("V178_TEAM_GENERATION_GATE_MISSING",token)
path.write_text(source,encoding="utf-8")
print("V178_CLAIM_TEAMS_INVITE_ACCEPT_LEAVE_KICK_PERSISTED_PASS")
