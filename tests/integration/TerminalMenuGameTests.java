package dev.obsidiannetwork.build103;

import dev.obsidiannetwork.ObsidianNetwork;
import dev.obsidiannetwork.blockentity.StorageDriveBlockEntity;
import dev.obsidiannetwork.core.*;
import dev.obsidiannetwork.menu.StorageTerminalMenu;
import dev.obsidiannetwork.network.*;
import dev.obsidiannetwork.platform.MinecraftItemStackCodec;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.gametest.framework.*;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Rotation;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.RegisterGameTestsEvent;
import net.neoforged.neoforge.network.handling.IPayloadContext;

/** CI-only real server menu/payload stress; no client rendering claims. */
@EventBusSubscriber(modid="obsidiannetwork")
public final class TerminalMenuGameTests {
  @SubscribeEvent public static void register(RegisterGameTestsEvent event) {
    var env=event.registerEnvironment(Identifier.fromNamespaceAndPath("obsidiannetwork","terminal_menu_env"),new TestEnvironmentDefinition.AllOf(java.util.List.of()));
    event.registerTest(Identifier.fromNamespaceAndPath("obsidiannetwork","terminal_menu_stress"),new Test(new TestData<Holder<TestEnvironmentDefinition<?>>>(env,Identifier.fromNamespaceAndPath("obsidiannetwork","build103_empty"),400,0,true,Rotation.NONE)));
  }
  private static void check(boolean ok,String msg){if(!ok)throw new IllegalStateException("TERMINAL_MENU_TEST: "+msg);}
  private static long count(ServerPlayer p,net.minecraft.world.item.Item item) {
    long amount=0;
    for(int i=0;i<36;i++)if(p.getInventory().getItem(i).is(item))amount+=p.getInventory().getItem(i).getCount();
    if(p.containerMenu.getCarried().is(item))amount+=p.containerMenu.getCarried().getCount();
    return amount;
  }
  private static void clear(ServerPlayer p){for(int i=0;i<36;i++)p.getInventory().setItem(i,ItemStack.EMPTY);p.containerMenu.setCarried(ItemStack.EMPTY);}
  private static void stats(String marker,long[] values,int operations) {
    long[] sorted=values.clone();java.util.Arrays.sort(sorted);
    long total=0;for(long n:sorted)total+=n;
    System.out.println(marker+" samples="+sorted.length+" operations="+operations+" median_ns="+sorted[sorted.length/2]+" p95_ns="+sorted[(int)Math.ceil(sorted.length*.95)-1]+" max_ns="+sorted[sorted.length-1]+" total_ns="+total);
  }
  @SuppressWarnings("unchecked")
  private static void checkRecipeCache(StorageTerminalMenu menu,ServerLevel level) {
    try {
      var field=StorageTerminalMenu.class.getDeclaredField("craftSlots");field.setAccessible(true);
      var craft=(net.minecraft.world.inventory.TransientCraftingContainer)field.get(menu);
      var cached=StorageTerminalMenu.class.getDeclaredMethod("craftRecipeCandidates",ServerLevel.class,net.minecraft.world.item.crafting.CraftingInput.class);cached.setAccessible(true);
      var matching=StorageTerminalMenu.class.getDeclaredMethod("matchingCraftRecipes",ServerLevel.class,net.minecraft.world.item.crafting.CraftingInput.class);matching.setAccessible(true);
      Object first=cached.invoke(menu,level,craft.asCraftInput());
      check(first==cached.invoke(menu,level,craft.asCraftInput()),"same exact grid reuses candidates");
      for(int variant=0;variant<4;variant++) {
        ItemStack fixture=new ItemStack(variant==3?Items.BIRCH_LOG:Items.OAK_LOG,variant==1?2:1);
        if(variant==2)fixture.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME,Component.literal("exact component fixture"));
        menu.getSlot(5).set(fixture);
        var input=craft.asCraftInput();
        java.util.List<net.minecraft.world.item.crafting.RecipeHolder<net.minecraft.world.item.crafting.CraftingRecipe>> expected=new java.util.ArrayList<>();
        java.util.List<ItemStack> outputs=new java.util.ArrayList<>();
        java.util.List<?> candidates=(java.util.List<?>)cached.invoke(menu,level,input);
        for(var holder:level.recipeAccess().recipeMap().byType(net.minecraft.world.item.crafting.RecipeType.CRAFTING)) {
          var recipe=holder.value();
          boolean stable=(recipe.getClass()==net.minecraft.world.item.crafting.ShapedRecipe.class||recipe.getClass()==net.minecraft.world.item.crafting.ShapelessRecipe.class)&&recipe.placementInfo().ingredients().stream().noneMatch(net.minecraft.world.item.crafting.Ingredient::isCustom);
          check(stable||candidates.contains(holder),"custom/special recipe remains live candidate");
          if(!recipe.matches(input,level))continue;
          ItemStack output=recipe.assemble(input);
          if(output.isEmpty()||!output.isItemEnabled(level.enabledFeatures()))continue;
          boolean duplicate=false;for(ItemStack old:outputs)if(ItemStack.matches(old,output)){duplicate=true;break;}
          if(!duplicate){outputs.add(output);expected.add(holder);}
        }
        check(expected.equals(matching.invoke(menu,level,input)),"cached recipe choices equal full scan variant="+variant);
      }
      menu.getSlot(5).set(new ItemStack(Items.OAK_LOG,1));
      var mapField=StorageTerminalMenu.class.getDeclaredField("cachedCraftRecipeMap");mapField.setAccessible(true);
      var input=craft.asCraftInput();
      Object reference=matching.invoke(menu,level,input);
      for(int warmup=0;warmup<20;warmup++){mapField.set(menu,null);matching.invoke(menu,level,input);matching.invoke(menu,level,input);}
      long[] rebuildNs=new long[9],reuseNs=new long[9];
      for(int trial=0;trial<9;trial++)for(int phase=0;phase<2;phase++){
        boolean rebuild=((trial+phase)&1)==0;
        matching.invoke(menu,level,input); // prime before each timed reuse pass
        Object actual=null;long begin=System.nanoTime();
        for(int operation=0;operation<32;operation++){
          if(rebuild)mapField.set(menu,null);
          actual=matching.invoke(menu,level,input);
        }
        long ns=System.nanoTime()-begin;
        check(reference.equals(actual),"candidate cache benchmark preserves exact recipe choices");
        (rebuild?rebuildNs:reuseNs)[trial]=ns;
      }
      stats("TERMINAL_RECIPE_MATCH_REBUILD_NS",rebuildNs,288);
      stats("TERMINAL_RECIPE_MATCH_REUSE_NS",reuseNs,288);
      System.out.println("TERMINAL_RECIPE_CACHE_EQUIVALENCE PASS variants=4 exact_counts=true exact_components=true dynamic_candidates_live=true");
    } catch(ReflectiveOperationException failure){throw new IllegalStateException("Recipe cache runtime verification failed",failure);}
  }
  private static IPayloadContext context(ServerPlayer player) {
    return (IPayloadContext)java.lang.reflect.Proxy.newProxyInstance(IPayloadContext.class.getClassLoader(),new Class<?>[]{IPayloadContext.class},(proxy,method,args)->{
      if(method.getName().equals("player"))return player;
      if(method.getName().equals("enqueueWork")){
        if(args[0] instanceof Runnable runnable)runnable.run();
        else if(args[0] instanceof java.util.function.Supplier<?> supplier)supplier.get();
        return java.util.concurrent.CompletableFuture.completedFuture(null);
      }
      if(method.getName().equals("disconnect"))throw new IllegalStateException("Test payload disconnected: "+java.util.Arrays.toString(args));
      if(method.getName().equals("toString"))return "TerminalMenuTestContext";
      throw new UnsupportedOperationException("Unexpected payload context API "+method.getName());
    });
  }
  private static void send(StorageTerminalMenu menu,IPayloadContext ctx,long[] nonce,TerminalProtocol.Message msg) {
    ServerTerminalPayloadHandler.handle(TerminalWirePayload.of(new TerminalFrameCodec.Frame(menu.terminalId(),menu.sessionId(),++nonce[0],msg)),ctx);
  }
  private static final class Test extends GameTestInstance {
    Test(TestData<Holder<TestEnvironmentDefinition<?>>> data){super(data);}
    @Override public com.mojang.serialization.MapCodec<? extends GameTestInstance> codec(){throw new UnsupportedOperationException("CI-only");}
    @Override protected net.minecraft.network.chat.MutableComponent typeDescription(){return Component.literal("Authoritative terminal menu crafting and bulk operations");}
    @Override public void run(GameTestHelper h) {
      ServerLevel level=(ServerLevel)h.getLevel();
      BlockPos controller=h.absolutePos(new BlockPos(1,1,1)),drivePos=h.absolutePos(new BlockPos(2,1,1)),terminal=h.absolutePos(new BlockPos(1,1,2));
      level.setBlock(controller,ObsidianNetwork.NETWORK_CONTROLLER.get().defaultBlockState(),3);
      level.setBlock(drivePos,ObsidianNetwork.STORAGE_DRIVE.get().defaultBlockState(),3);
      level.setBlock(terminal,ObsidianNetwork.CRAFTING_TERMINAL.get().defaultBlockState(),3);
      StorageDriveBlockEntity drive=(StorageDriveBlockEntity)level.getBlockEntity(drivePos);
      net.minecraft.world.item.Item cell=null;
      for(var item:net.minecraft.core.registries.BuiltInRegistries.ITEM)if(item instanceof dev.obsidiannetwork.item.StorageCellItem){cell=item;break;}
      check(cell!=null,"registered normal storage cell");
      for(int slot=0;slot<StorageDriveRuntime.SLOTS;slot++)check(drive.insertCellAt(slot,new ItemStack(cell)),"insert cell "+slot);
      h.startSequence().thenExecuteAfter(30,()->{
        NetworkRuntime rt=WorldTopologyBridge.runtimeForController(level,controller);
        check(rt!=null,"controller runtime");rt.energy().load(200000);check(rt.tick(),"powered runtime");
        ServerPlayer player=FakePlayerFactory.get(level,new com.mojang.authlib.GameProfile(java.util.UUID.fromString("cc08cd0b-1fa2-4c8f-b1ee-fd5f009912c0"),"ONTerminalTest"));
        player.setPos(terminal.getX()+.5,terminal.getY()+.5,terminal.getZ()+.5);
        var flow=WorldTopologyBridge.openTerminal(level,terminal,player);check(flow!=null,"real terminal session");
        StorageTerminalMenu menu=new StorageTerminalMenu(72,player.getInventory(),terminal,flow.terminalId(),flow.sessionId());
        player.containerMenu=menu;clear(player);
        check(WorldTopologyBridge.openTerminalViewers(level,rt).contains(player),"fake player participates in real terminal delta fan-out");
        var codec=new MinecraftItemStackCodec(level.registryAccess());
        var logs=codec.describe(new ItemStack(Items.OAK_LOG));
        var stone=codec.describe(new ItemStack(Items.COBBLESTONE));
        var iron=codec.describe(new ItemStack(Items.IRON_INGOT));
        for(var d:java.util.List.of(logs,stone,iron))rt.descriptors().registerKnown(d.key(),d.canonicalPayload());
        check(rt.storage().insertExact(logs.key(),logs.canonicalPayload(),1600)==1600,"log fixture");
        check(rt.storage().insertExact(stone.key(),stone.canonicalPayload(),1)==1,"stone seed");
        check(rt.storage().insertExact(iron.key(),iron.canonicalPayload(),1)==1,"iron seed");
        menu.getSlot(5).set(new ItemStack(Items.OAK_LOG,1));
        check(menu.getSlot(0).getItem().is(Items.OAK_PLANKS)&&menu.getSlot(0).getItem().getCount()==4,"log recipe output");
        checkRecipeCache(menu,level);
        // Multi-result recipes may not consume an ingredient when only part of
        // their result fits. These are real result-slot quick moves.
        for(int i=0;i<36;i++)player.getInventory().setItem(i,new ItemStack(Items.COBBLESTONE,64));
        player.getInventory().setItem(35,new ItemStack(Items.OAK_PLANKS,63));
        long logBefore=rt.storage().index().amount(logs.key());
        check(menu.quickMoveStack(player,0).isEmpty(),"partial output must reject");
        check(rt.storage().index().amount(logs.key())==logBefore&&menu.getSlot(5).getItem().getCount()==1&&count(player,Items.OAK_PLANKS)==63,"partial output conservation");
        player.getInventory().setItem(35,new ItemStack(Items.COBBLESTONE,64));
        check(menu.quickMoveStack(player,0).isEmpty(),"full inventory rejects craft");
        check(rt.storage().index().amount(logs.key())==logBefore,"full inventory ingredient conservation");
        player.getInventory().setItem(35,new ItemStack(Items.OAK_PLANKS,60));
        check(!menu.quickMoveStack(player,0).isEmpty()&&count(player,Items.OAK_PLANKS)==64,"exact room accepts full output");
        clear(player);
        final long[] produced={4};
        final long[] craftSamples=new long[60],craftTicks=new long[20],bulkSamples=new long[20],bulkTicks=new long[20];
        final long[] nonce={0};var ctx=context(player);
        // Exercise full resync and key disappearance/reappearance. A new screen
        // may clear all visuals while reusing this menu/session.
        ServerTerminalPayloadHandler.flushRuntimeDeltas(level,rt);
        menu.terminalVisualKeyRemoved(logs.key());
        send(menu,ctx,nonce,new TerminalProtocol.ResyncRequest(rt.storage().index().revision()));
        check(menu.terminalVisualKeyKnown(logs.key()),"full resync resends known immutable metadata");
        check(rt.storage().extract(stone.key(),1)==1,"zero-count metadata fixture");
        ServerTerminalPayloadHandler.flushRuntimeDeltas(level,rt);
        check(!menu.terminalVisualKeyKnown(stone.key()),"zero delta invalidates visual key");
        rt.descriptors().registerKnown(stone.key(),stone.canonicalPayload());
        check(rt.storage().insertExact(stone.key(),stone.canonicalPayload(),1)==1,"metadata reappearance fixture");
        ServerTerminalPayloadHandler.flushRuntimeDeltas(level,rt);
        check(menu.terminalVisualKeyKnown(stone.key()),"reappearing key resends metadata");
        long now=level.getGameTime();
        check(menu.shouldSendFluidSnapshot(now,true),"forced fluid refresh");
        check(!menu.shouldSendFluidSnapshot(now,false),"same-tick item requests coalesce fluid refresh");
        check(menu.shouldSendFluidSnapshot(now,true),"same-tick fluid mutation forces refresh");
        System.out.println("TERMINAL_METADATA_RESYNC_V1 PASS resync=true zero_delta=true reappearance=true fluid_force=true viewer_registered=true");
        var seq=h.startSequence();
        for(int tick=-5;tick<20;tick++){
          final int sample=tick;
          seq.thenExecuteAfter(1,()->{
            ServerTickProbe.mark(sample<0?"rapid_crafting_warmup":"rapid_crafting");
            if(sample==0)System.out.println("BENCHMARK_WINDOW_START workload=crafting wall_time_ms="+System.currentTimeMillis());
            rt.energy().load(200000);check(rt.tick(),"crafting power");
            long tickStart=System.nanoTime();
            for(int op=0;op<3;op++){
              long begin=System.nanoTime();
              menu.clicked(0,0,op==0?ContainerInput.QUICK_MOVE:ContainerInput.PICKUP,player);
              menu.broadcastChanges();
              if(sample>=0)craftSamples[sample*3+op]=System.nanoTime()-begin;
            }
            long out=count(player,Items.OAK_PLANKS);
            check(out==72,"shift craft plus two manual crafts output="+out);
            produced[0]+=out;clear(player);
            check((1601-rt.storage().index().amount(logs.key())-menu.getSlot(5).getItem().getCount())*4==produced[0],"crafting exact ingredient/result totals");
            if(sample>=0)craftTicks[sample]=System.nanoTime()-tickStart;
            if(sample==19){
              stats("TERMINAL_CRAFT_MENU_NS",craftSamples,60);stats("TERMINAL_CRAFT_TICK_WORK_NS",craftTicks,360);
              System.out.println("TERMINAL_CRAFT_CONSERVATION PASS crafted_planks="+produced[0]+" full_inventory=true partial_inventory=true quick_move=true manual_click=true");
              System.out.println("BENCHMARK_WINDOW_END workload=crafting wall_time_ms="+System.currentTimeMillis());
            }
          });
        }
        for(int tick=-5;tick<20;tick++){
          final int sample=tick;
          seq.thenExecuteAfter(1,()->{
            ServerTickProbe.mark(sample<0?"rapid_bulk_warmup":"rapid_bulk");
            if(sample==0)System.out.println("BENCHMARK_WINDOW_START workload=bulk wall_time_ms="+System.currentTimeMillis());
            rt.energy().load(200000);check(rt.tick(),"bulk power");
            long start=System.nanoTime();
            for(int op=0;op<64;op++){
              var item=op<32?Items.COBBLESTONE:Items.IRON_INGOT;
              if(op<60){
                player.getInventory().setItem(9,new ItemStack(item,64));
                check(!menu.quickMoveStack(player,10).isEmpty(),"menu bulk insertion "+op);
                check(player.getInventory().getItem(9).isEmpty(),"bulk menu source consumed exactly");
                menu.broadcastChanges();
              }else{
                menu.setCarried(new ItemStack(item,64));
                send(menu,ctx,nonce,new TerminalProtocol.SlotInsertRequest(36,64));
                check(menu.getCarried().isEmpty(),"payload bulk cursor consumed exactly");
              }
            }
            check(rt.storage().index().amount(stone.key())==2049&&rt.storage().index().amount(iron.key())==2049,"bulk deposits exact counts");
            for(var d:java.util.List.of(stone,iron)){
              send(menu,ctx,nonce,new TerminalProtocol.TransferRequest(false,d.key(),2048));
              check(count(player,d==stone?Items.COBBLESTONE:Items.IRON_INGOT)==2048,"payload extract exact full inventory output");
              clear(player);
            }
            check(rt.storage().index().amount(stone.key())==1&&rt.storage().index().amount(iron.key())==1,"bulk cycle no loss or duplication");
            long ns=System.nanoTime()-start;
            if(sample>=0){bulkSamples[sample]=ns;bulkTicks[sample]=ns;}
            if(sample==19){
              stats("TERMINAL_BULK_MENU_NS",bulkSamples,1320);stats("TERMINAL_BULK_TICK_WORK_NS",bulkTicks,1320);
              System.out.println("TERMINAL_BULK_CONSERVATION PASS cycles=25 items_per_cycle=4096 types=2 menu_insertions=1500 payload_insertions=100 payload_extractions=50");
              System.out.println("BENCHMARK_WINDOW_END workload=bulk wall_time_ms="+System.currentTimeMillis());
            }
          });
        }
        seq.thenExecute(()->{
          clear(player);
          rt.storage().insertExact(stone.key(),stone.canonicalPayload(),1000000000L);
          long before=rt.storage().index().amount(stone.key());
          player.getInventory().setItem(9,new ItemStack(Items.COBBLESTONE,64));
          check(menu.quickMoveStack(player,10).isEmpty(),"full storage rejects menu deposit");
          check(player.getInventory().getItem(9).getCount()==64&&rt.storage().index().amount(stone.key())==before,"full storage conservation");
          check(rt.storage().extract(stone.key(),13)==13,"partial storage fixture");
          check(!menu.quickMoveStack(player,10).isEmpty(),"partial storage accepts fitting amount");
          check(player.getInventory().getItem(9).getCount()==51&&rt.storage().index().amount(stone.key())==before,"partial storage conservation");
          clear(player);menu.removed(player);player.containerMenu=player.inventoryMenu;
          System.out.println("TERMINAL_MENU_STRESS_V1 PASS server_menu=true rendered_client_gui=false partial_and_full_storage=true");
          h.succeed();
        });
      });
    }
  }
}
