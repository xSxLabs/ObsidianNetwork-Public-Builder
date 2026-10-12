package dev.xsxlabs.stress;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.LogisticsCableBlockEntity;
import dev.obsidiannetwork.blockentity.NetworkTankBlockEntity;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.ChestBlockEntity;
import net.minecraft.world.level.material.Fluids;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.tick.ServerTickEvent;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

@Mod("stressfixture")
public final class ActiveStressFixture {
    private static final int LANES=32, START=100, DURATION=400;
    private int ticks=0;
    private boolean started=false;
    private final List<Double> mspt=new ArrayList<>();
    private long previous=0;
    private long initialItems=0,initialFluid=0;

    public ActiveStressFixture(){ NeoForge.EVENT_BUS.register(this); }
    private static void require(boolean ok,String msg){ if(!ok)throw new IllegalStateException("BUILD106 ACTIVE STRESS: "+msg); }
    private static BlockPos pos(int lane,int x,boolean fluid){return new BlockPos(x,90,(fluid?64:0)+lane*2);}
    private static IFluidHandler tank(ServerLevel level,BlockPos p){
        return IFluidHandler.of(((NetworkTankBlockEntity)level.getBlockEntity(p)).tank());
    }
    private static int itemCount(ServerLevel l,BlockPos p){
        ChestBlockEntity chest=(ChestBlockEntity)l.getBlockEntity(p);
        int n=0;for(int i=0;i<chest.getContainerSize();i++)n+=chest.getItem(i).getCount();
        return n;
    }
    private static int fluidCount(ServerLevel l,BlockPos p){return tank(l,p).getFluidInTank(0).getAmount();}
    private void setup(ServerLevel l){
        for(int lane=0;lane<LANES;lane++){
            BlockPos source=pos(lane,0,false),in=pos(lane,1,false),mid=pos(lane,2,false),out=pos(lane,3,false),dest=pos(lane,4,false);
            l.setBlock(source,Blocks.CHEST.defaultBlockState(),3);
            l.setBlock(in,ObsidianNetwork.ITEM_CABLE.get().defaultBlockState(),3);
            l.setBlock(mid,ObsidianNetwork.ITEM_CABLE.get().defaultBlockState(),3);
            l.setBlock(out,ObsidianNetwork.ITEM_CABLE.get().defaultBlockState(),3);
            l.setBlock(dest,Blocks.CHEST.defaultBlockState(),3);
            ((LogisticsCableBlockEntity)l.getBlockEntity(in)).setMode(Direction.WEST,LogisticsCableBlockEntity.Mode.IMPORT);
            ((LogisticsCableBlockEntity)l.getBlockEntity(out)).setMode(Direction.EAST,LogisticsCableBlockEntity.Mode.EXPORT);
            ChestBlockEntity c=(ChestBlockEntity)l.getBlockEntity(source);
            for(int slot=0;slot<27;slot++)c.setItem(slot,new ItemStack(Items.DIAMOND,64));
            initialItems+=itemCount(l,source);
            BlockPos fs=pos(lane,0,true),fi=pos(lane,1,true),fm=pos(lane,2,true),fo=pos(lane,3,true),fd=pos(lane,4,true);
            l.setBlock(fs,ObsidianNetwork.NETWORK_TANK_64K.get().defaultBlockState(),3);
            l.setBlock(fi,ObsidianNetwork.FLUID_CABLE.get().defaultBlockState(),3);
            l.setBlock(fm,ObsidianNetwork.FLUID_CABLE.get().defaultBlockState(),3);
            l.setBlock(fo,ObsidianNetwork.FLUID_CABLE.get().defaultBlockState(),3);
            l.setBlock(fd,ObsidianNetwork.NETWORK_TANK_64K.get().defaultBlockState(),3);
            ((LogisticsCableBlockEntity)l.getBlockEntity(fi)).setMode(Direction.WEST,LogisticsCableBlockEntity.Mode.IMPORT);
            ((LogisticsCableBlockEntity)l.getBlockEntity(fo)).setMode(Direction.EAST,LogisticsCableBlockEntity.Mode.EXPORT);
            int filled=tank(l,fs).fill(new FluidStack(Fluids.WATER,32000),IFluidHandler.FluidAction.EXECUTE);
            require(filled==32000,"source fluid fill "+lane+" "+filled);
            initialFluid+=filled;
        }
    }
    private void finish(ServerLevel l,MinecraftServer server)throws Exception{
        long is=0,id=0,fs=0,fd=0;
        for(int lane=0;lane<LANES;lane++){
            is+=itemCount(l,pos(lane,0,false));id+=itemCount(l,pos(lane,4,false));
            fs+=fluidCount(l,pos(lane,0,true));fd+=fluidCount(l,pos(lane,4,true));
        }
        require(initialItems==is+id,"ITEM LOSS/DUPLICATION initial="+initialItems+" actual="+(is+id));
        require(initialFluid==fs+fd,"FLUID LOSS/DUPLICATION initial="+initialFluid+" actual="+(fs+fd));
        require(id>0,"No actual item delivery");
        require(fd>0,"No actual fluid delivery");
        Collections.sort(mspt);
        double avg=mspt.stream().mapToDouble(Double::doubleValue).average().orElse(0);
        double p95=mspt.get((int)Math.ceil(mspt.size()*.95)-1);
        double seconds=DURATION/20.0;
        String json=String.format(Locale.ROOT,
          "{\"fixture\":\"separate-NeoForge-mod-frozen-Build-106\",\"lanes\":%d,\"ticks\":%d,\"initial_items\":%d,\"item_source_remaining\":%d,\"item_exported\":%d,\"item_imported\":%d,\"item_cable_moved\":%d,\"initial_fluid_mb\":%d,\"fluid_source_remaining_mb\":%d,\"fluid_exported_mb\":%d,\"fluid_imported_mb\":%d,\"fluid_cable_moved_mb\":%d,\"items_per_second\":%.3f,\"mb_per_second\":%.3f,\"avg_mspt\":%.3f,\"p95_mspt\":%.3f,\"estimated_tps\":%.3f,\"item_balance_error\":%d,\"fluid_balance_error_mb\":%d}",
          LANES,DURATION,initialItems,is,id,id,id,initialFluid,fs,fd,fd,fd,id/seconds,fd/seconds,avg,p95,Math.min(20,1000/avg),initialItems-is-id,initialFluid-fs-fd);
        Files.writeString(Path.of("transport-results.json"),json);
        System.out.println("BUILD106_ACTIVE_TRANSPORT_PASS "+json);
        server.halt(false);
    }
    @SubscribeEvent
    public void tick(ServerTickEvent.Post event){
        MinecraftServer server=event.getServer();
        ServerLevel level=server.overworld();
        if(++ticks<START)return;
        try{
            if(!started){setup(level);started=true;previous=System.nanoTime();return;}
            long now=System.nanoTime();
            mspt.add((now-previous)/1_000_000.0);
            previous=now;
            if(ticks==START+DURATION)finish(level,server);
        }catch(Exception ex){ex.printStackTrace();server.halt(false);throw new RuntimeException(ex);}
    }
}
