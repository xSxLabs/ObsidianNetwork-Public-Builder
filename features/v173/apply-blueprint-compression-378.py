#!/usr/bin/env python3
"""B378: backward-compatible compressed strings for large Blueprint cards."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/item/NetworkBlueprintItem.java"
s=p.read_text(encoding="utf-8")
def replace(old,new):
 global s
 assert s.count(old)==1,("B378_BLUEPRINT_CODEC_DRIFT",old[:90],s.count(old))
 s=s.replace(old,new,1)
replace('return data==null?"":data.copyTag().getStringOr(key,"");',
'''if(data==null)return "";
   String raw=data.copyTag().getStringOr(key,"");
   if(!raw.startsWith("@xsxz1:"))return raw;
   try{
    byte[] zipped=java.util.Base64.getDecoder().decode(raw.substring(7));
    try(var input=new java.util.zip.GZIPInputStream(new java.io.ByteArrayInputStream(zipped));
        var output=new java.io.ByteArrayOutputStream()){
     byte[] chunk=new byte[8192];int n,total=0;
     while((n=input.read(chunk))!=-1){
      total+=n;if(total>128*1024*1024)return "";
      output.write(chunk,0,n);
     }
     return output.toString(java.nio.charset.StandardCharsets.UTF_8);
    }
   }catch(java.io.IOException|IllegalArgumentException ex){return "";}''')
replace('tag.putString(key,value);',
'''// B378_COMPRESSED_BLUEPRINT: older noncompressed items still work.
   String stored=value;
   if(("xsxlabs_blocks".equals(key)||"xsxlabs_states".equals(key))&&value.length()>4096){
    try{
     var bytes=new java.io.ByteArrayOutputStream();
     try(var gzip=new java.util.zip.GZIPOutputStream(bytes)){
      gzip.write(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
     }
     stored="@xsxz1:"+java.util.Base64.getEncoder().encodeToString(bytes.toByteArray());
    }catch(java.io.IOException ex){throw new IllegalStateException(ex);}
   }
   tag.putString(key,stored);''')
p.write_text(s,encoding="utf-8")
print("B378_BLUEPRINT_COMPRESSED_BACKWARD_COMPAT_PASS")
