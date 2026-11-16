#!/usr/bin/env python3
"""B1651: world-scoped claim/force-load limits in serverconfig.

Atomic claim persistence stays unchanged. Read config once per server startup,
not on ticks, render, claim edits, or map requests. Preserve legacy JVM defaults.
"""
import os
from pathlib import Path
P=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/claims/V178Claims.java"
s=P.read_text(encoding="utf-8")
def rep(old,new):
 global s
 count=s.count(old)
 assert count==1,("V178_SERVER_CONFIG_SOURCE_DRIFT",old[:90],count)
 s=s.replace(old,new,1)
rep(''' private static final String FILE_NAME="xsxlabs-v178-claims.tsv";''',
''' private static final String FILE_NAME="xsxlabs-v178-claims.tsv";
 private static final String CONFIG_NAME="xsxlabs-chunks.properties";
 private static int activeMaxClaims=MAX_CLAIMS,activeMaxLoaded=MAX_LOADED;
 private static int activeMaxTeamMembers=MAX_TEAM_SIZE;''')
rep('''  active=level.getServer();dirty=false;''',
'''  active=level.getServer();dirty=false;
  readLimits(active);''')
rep(''' private static void save(){''',
''' /** Server config is read only when a new world/server is attached. */
 private static void readLimits(MinecraftServer server){
  activeMaxClaims=MAX_CLAIMS;
  activeMaxLoaded=MAX_LOADED;
  activeMaxTeamMembers=MAX_TEAM_SIZE;
  Path path=server.getWorldPath(LevelResource.ROOT)
       .resolve("serverconfig").resolve(CONFIG_NAME);
  Properties settings=new Properties();
  try{
   if(Files.isRegularFile(path)){
    try(InputStream input=Files.newInputStream(path)){settings.load(input);}
   }else{
    Files.createDirectories(path.getParent());
    settings.setProperty("max_claimed_chunks",Integer.toString(MAX_CLAIMS));
    settings.setProperty("max_force_loaded_chunks",Integer.toString(MAX_LOADED));
    settings.setProperty("max_team_members",Integer.toString(MAX_TEAM_SIZE));
    try(OutputStream output=Files.newOutputStream(path)){
     settings.store(output,"xSxLabs Network Storage chunk limits (restart server after editing)");
    }
   }
   try{
    activeMaxClaims=Math.min(2048,Math.max(1,
       Integer.parseInt(settings.getProperty("max_claimed_chunks",
          Integer.toString(MAX_CLAIMS)).trim())));
   }catch(NumberFormatException ignored){activeMaxClaims=MAX_CLAIMS;}
   try{
    activeMaxLoaded=Math.min(256,Math.max(0,
       Integer.parseInt(settings.getProperty("max_force_loaded_chunks",
          Integer.toString(MAX_LOADED)).trim())));
   }catch(NumberFormatException ignored){activeMaxLoaded=MAX_LOADED;}
   activeMaxLoaded=Math.min(activeMaxLoaded,activeMaxClaims);
   try{
    activeMaxTeamMembers=Math.min(MAX_TEAM_SIZE,Math.max(1,
      Integer.parseInt(settings.getProperty("max_team_members",
        Integer.toString(MAX_TEAM_SIZE)).trim())));
   }catch(NumberFormatException ignored){activeMaxTeamMembers=MAX_TEAM_SIZE;}
  }catch(IOException ex){
   System.err.println("[xSxLabs] chunk config read failed: "+ex);
  }
 }
 private static void save(){''')
# Preserve the absolute safety caps, replace only runtime quota comparisons.
n1=s.count(">=MAX_CLAIMS")
n2=s.count(">=MAX_LOADED")
assert n1>=2 and n2>=2,("V178_QUOTA_COMPARISON_DRIFT",n1,n2)
s=s.replace(">=MAX_CLAIMS",">=activeMaxClaims").replace(">=MAX_LOADED",">=activeMaxLoaded")
nt1=s.count(">=MAX_TEAM_SIZE")
nt2=s.count("<MAX_TEAM_SIZE")
nd=s.count('"+MAX_TEAM_SIZE+"')
assert nt1==2 and nt2==1 and nd==2,("V178_TEAM_LIMIT_DRIFT",nt1,nt2,nd)
s=s.replace(">=MAX_TEAM_SIZE",">=activeMaxTeamMembers")
s=s.replace("<MAX_TEAM_SIZE","<activeMaxTeamMembers")
s=s.replace('"+MAX_TEAM_SIZE+"','"+activeMaxTeamMembers+"')
n3=s.count('"+MAX_CLAIMS+"')
n4=s.count('"+MAX_LOADED+"')
assert n3>=2 and n4>=2,("V178_QUOTA_DISPLAY_DRIFT",n3,n4)
s=s.replace('"+MAX_CLAIMS+"','"+activeMaxClaims+"').replace('"+MAX_LOADED+"','"+activeMaxLoaded+"')
assert s.count("readLimits(active);")==1
assert "MAX_CLAIMS=Math.min(2048" in s and "MAX_LOADED=Math.min(256" in s
assert "activeMaxLoaded=Math.min(activeMaxLoaded,activeMaxClaims);" in s
assert "Files.createDirectories(path.getParent());" in s
P.write_text(s,encoding="utf-8")
print("V178_B1651_WORLD_SCOPED_SERVER_CLAIM_LIMITS_PASS")
