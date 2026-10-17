#!/usr/bin/env python3
"""CI-only live NetworkRuntime reservation probe in the existing 50-drive GameTest.

Runs against actual patched MinecraftAutocraftingService in both pre/post
runtime GameTests. No source code for the test is included in the release JAR.
Fail closed if the GameTest fixture layout changes.
"""
import os
from pathlib import Path

p = Path(os.environ.get("V1_PROJECT_ROOT", "work")) / "src/main/java/dev/obsidiannetwork/build103/Build103GameTests.java"
s = p.read_text(encoding="utf-8")
begin = s.index("private static final class FiftyDriveTest extends GameTestInstance {")
end = s.index("private static final class MixedCableTest extends GameTestInstance {", begin)
before, segment, after = s[:begin], s[begin:end], s[end:]
marker = "XSXLABS_REAL_AUTOCRAFT_RESERVATION_GAMETEST_V1"
assert marker not in s, "Probe already present, refusing duplicate injection"
anchor = "FiftyDriveTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data) { super(data); }"
assert segment.count(anchor) == 1, "50-drive registration changed"
assert segment.count("h.succeed();") == 1, "50-drive success gate changed"
assert "REAL_50_DRIVE_SUSTAINED_SUMMARY" in segment, "50-drive load test missing"
assert "if(p95>50_000_000L)" in segment, "Existing 50-drive budget gate missing"

probe = """
              // XSXLABS_REAL_AUTOCRAFT_RESERVATION_GAMETEST_V1
              // Uses private immutable records only in this temporary CI GameTest.
              private static final boolean XSXLABS_REQUIRE_IDLE_REUSE = false;
              private static void assertLiveAutocraftReservations(
                  net.minecraft.server.level.ServerLevel level,
                  dev.obsidiannetwork.core.NetworkRuntime runtime) {
                try {
                  var service=dev.obsidiannetwork.network.WorldTopologyBridge.autocraftingService(level,runtime);
                  Class<?> bufferType=Class.forName(
                      "dev.obsidiannetwork.platform.MinecraftAutocraftingService$BufferedInput");
                  Class<?> requestType=Class.forName(
                      "dev.obsidiannetwork.platform.MinecraftAutocraftingService$ProcessingRequest");
                  var bufferCtor=bufferType.getDeclaredConstructor(
                      dev.obsidiannetwork.core.ExactStackDescriptor.class,
                      long.class,long.class,long.class);
                  bufferCtor.setAccessible(true);
                  var requestCtor=requestType.getDeclaredConstructor(
                      long.class,dev.obsidiannetwork.core.ExactStackDescriptor.class,
                      long.class,long.class,java.util.List.class);
                  requestCtor.setAccessible(true);
                  var reserve=service.getClass().getDeclaredMethod("reserveAvailable",requestType);
                  reserve.setAccessible(true);
                  var inputsMethod=requestType.getDeclaredMethod("inputs");
                  inputsMethod.setAccessible(true);
                  var bufferedMethod=bufferType.getDeclaredMethod("buffered");
                  bufferedMethod.setAccessible(true);

                  // Real network with no corresponding item: attempts to reserve
                  // must preserve the exact immutable request instance and stock.
                  var absent=new dev.obsidiannetwork.core.ExactStackDescriptor(
                      "minecraft:prismarine",new byte[0]);
                  var absentKey=absent.key();
                  long initial=runtime.storage().index().amount(absentKey);
                  if(initial!=0L)throw new IllegalStateException("Missing-item fixture is not empty");
                  java.util.ArrayList<Object> emptyInputs=new java.util.ArrayList<>();
                  for(int i=0;i<12;i++)emptyInputs.add(bufferCtor.newInstance(absent,1L,1L,0L));
                  Object idle=requestCtor.newInstance(9000001L,absent,1L,1L,emptyInputs);
                  for(int iteration=0;iteration<100;iteration++){
                    Object next=reserve.invoke(service,idle);
                    if(XSXLABS_REQUIRE_IDLE_REUSE && next!=idle)throw new IllegalStateException(
                        "Idle autocraft rebuilt an unchanged reservation");
                  }
                  long[] measurements=new long[9];
                  for(int sample=0;sample<measurements.length;sample++){
                    long start=System.nanoTime();
                    for(int iteration=0;iteration<500;iteration++)
                      if(XSXLABS_REQUIRE_IDLE_REUSE && reserve.invoke(service,idle)!=idle)
                        throw new IllegalStateException("Idle reservation identity drift");
                    measurements[sample]=System.nanoTime()-start;
                  }
                  java.util.Arrays.sort(measurements);
                  if(runtime.storage().index().amount(absentKey)!=initial)
                    throw new IllegalStateException("Idle reservation changed storage");
                  System.out.println("REAL_AUTOCRAFT_IDLE_RESERVATION_V1 samples=9 calls_per_sample=500 inputs=12"+
                      " median_ns="+measurements[4]+" p90_ns="+measurements[8]+
                      " no_TPS_claim=true");

                  // A real successful reservation must allocate a new request,
                  // debit the authoritative network index, preserve order and be
                  // fully reversible with exact descriptor and quantity.
                  var available=new dev.obsidiannetwork.core.ExactStackDescriptor(
                      "minecraft:copper_ingot",new byte[0]);
                  var key=available.key();
                  long original=runtime.storage().index().amount(key);
                  if(original!=0L)throw new IllegalStateException("Reservation fixture already populated");
                  if(runtime.storage().insertExact(key,available.canonicalPayload(),17L)!=17L)
                    throw new IllegalStateException("Cannot seed exact reservation stock");
                  try {
                    Object buffer=bufferCtor.newInstance(available,1L,10L,0L);
                    Object pending=requestCtor.newInstance(9000002L,available,1L,10L,java.util.List.of(buffer));
                    Object reserved=reserve.invoke(service,pending);
                    if(reserved==pending)
                      throw new IllegalStateException("Successful reservation reused an old request");
                    var inputs=(java.util.List<?>)inputsMethod.invoke(reserved);
                    if(inputs.size()!=1 || ((Long)bufferedMethod.invoke(inputs.get(0)))!=10L)
                      throw new IllegalStateException("Incorrect buffered reservation");
                    if(runtime.storage().index().amount(key)!=7L)
                      throw new IllegalStateException("Autocraft reservation did not debit exactly 10");
                    if(runtime.storage().insertExact(key,available.canonicalPayload(),10L)!=10L)
                      throw new IllegalStateException("Autocraft reservation exact restore incomplete");
                    if(runtime.storage().index().amount(key)!=17L)
                      throw new IllegalStateException("Autocraft reservation restore count wrong");
                  } finally {
                    long left=runtime.storage().index().amount(key);
                    if(left>0L && runtime.storage().extract(key,left)!=left)
                      throw new IllegalStateException("Autocraft fixture cleanup failed");
                  }
                  if(runtime.storage().index().amount(key)!=0L)
                    throw new IllegalStateException("Autocraft test left stored items");
                  System.out.println("REAL_AUTOCRAFT_RESERVATION_CONSERVATION_V1 PASS "+
                      "drives=50 cells=800 extracted=10 restored=10");
                } catch (ReflectiveOperationException ex) {
                  throw new IllegalStateException("Live autocraft reflection fixture incompatible",ex);
                }
              }
"""

segment=segment.replace(anchor,anchor+"\n"+probe,1)
segment=segment.replace("h.succeed();", "assertLiveAutocraftReservations(level,rt);\n                          h.succeed();",1)
assert segment.count(marker)==1
assert segment.count("assertLiveAutocraftReservations(level,rt);")==1
assert segment.count("h.succeed();")==1
p.write_text(before+segment+after,encoding="utf-8")
print("REAL_AUTOCRAFT_RESERVATION_GAMETEST_INJECTION_V1 PASS")
