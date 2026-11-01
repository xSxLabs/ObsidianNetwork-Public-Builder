package dev.obsidiannetwork.backpack;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Set;
public final class V176BackpackCodecTest {
    private static void yes(boolean b){if(!b)throw new AssertionError();}
    public static void main(String[] args){
        var magnet=new V176BackpackRules.Magnet(true,true,
          V176BackpackRules.FilterMode.BLACKLIST,Set.of("minecraft:dirt","minecraft:stone"));
        var state=new V176BackpackRules.State(Arrays.asList(
          new V176BackpackRules.Cell(256000,Map.of("minecraft:iron_ingot|{}",5000L)),
          null,
          new V176BackpackRules.Cell(64000,Map.of("minecraft:diamond|components={}",20L))),
          magnet,24);
        var encoded=V176BackpackCodec.encode(state);
        var restored=V176BackpackCodec.decode(encoded);
        yes(restored.equals(state));
        yes(restored.capacity()==320000&&restored.used()==5020);
        boolean failed=false;
        try {var broken=Arrays.copyOf(encoded,encoded.length+1);
          V176BackpackCodec.decode(broken);}catch(IllegalArgumentException expected){failed=true;}
        yes(failed);
        yes(Arrays.equals(encoded,V176BackpackCodec.encode(restored)));
        System.out.println("V176_BACKPACK_SERIALIZATION_ROUNDTRIP_AND_INTEGRITY_PASS");
    }
}
