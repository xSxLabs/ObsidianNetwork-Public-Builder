#!/usr/bin/env python3
"""Test-only MinecraftServer tick-ring and JVM GC observations during storage load.

The last 100 server ticks include other GameTest activity. Do not report
these results as a controlled A/B performance or client GUI measurement.
"""
import os
from pathlib import Path
p=Path(os.environ.get("V1_PROJECT_ROOT","work"))/"src/main/java/dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text(encoding="utf-8")
start="private static final class FiftyDriveTest extends GameTestInstance {"
end="private static final class MixedCableTest extends GameTestInstance {"
assert s.count(start)==s.count(end)==1, "GameTest fixture layout changed"
a=s.index(start); b=s.index(end,a)
segment=s[a:b]
marker="XSXLABS_SERVER_TICK_GC_PROBE_V1"
assert marker not in s, "Probe already injected"
ctor="FiftyDriveTest(TestData<net.minecraft.core.Holder<TestEnvironmentDefinition<?>>> data) { super(data); }"
anchor="final long[] storageTickWorkNs=new long[20];"
for x in (ctor, anchor, "h.succeed();", "REAL_50_DRIVE_SUSTAINED_SUMMARY", "if(p95>50_000_000L)"):
    assert segment.count(x)==1, "Fail-closed GameTest source anchor drift: "+x
helper="""// XSXLABS_SERVER_TICK_GC_PROBE_V1 — only in temporary GameTest source.
              private static long[] gcTotals() {
                long beans=0L, count=0L, millis=0L;
                for(var b:java.lang.management.ManagementFactory.getGarbageCollectorMXBeans()) {
                  long c=b.getCollectionCount(), ms=b.getCollectionTime();
                  if(c>=0L && ms>=0L) {
                    beans++;
                    count=Math.addExact(count,c);
                    millis=Math.addExact(millis,ms);
                  }
                }
                return new long[]{beans,count,millis};
              }"""
segment=segment.replace(ctor, ctor+"\n              "+helper, 1)
segment=segment.replace(anchor, anchor+"\n                        final long[] gcBefore=gcTotals();", 1)
observe="""// Read MinecraftServer's OWN completed-tick timing ring, not
                          // the wall-clock time between test callbacks.
                          long[] raw=level.getServer().getTickTimesNanos().clone();
                          long[] serverTicks=java.util.Arrays.stream(raw).filter(n->n>0L).sorted().toArray();
                          if(serverTicks.length<20 || serverTicks.length>100)
                            throw new IllegalStateException("Insufficient actual server tick samples");
                          long realP95=serverTicks[(serverTicks.length*95+99)/100-1];
                          long realP99=serverTicks[(serverTicks.length*99+99)/100-1];
                          long realWorst=serverTicks[serverTicks.length-1];
                          System.out.println("REAL_SERVER_TICK_RING_V1 samples="+serverTicks.length+
                              " p95_ns="+realP95+" p99_ns="+realP99+" worst_ns="+realWorst+
                              " ring_scope=true uncontrolled=true");
                          long[] gcAfter=gcTotals();
                          if(gcBefore[0]<1L || gcBefore[0]!=gcAfter[0] ||
                              gcAfter[1]<gcBefore[1] || gcAfter[2]<gcBefore[2])
                            throw new IllegalStateException("Unusable JVM GC counters");
                          System.out.println("REAL_SERVER_GC_WINDOW_V1 beans="+gcAfter[0]+
                              " collections_delta="+(gcAfter[1]-gcBefore[1])+
                              " time_ms_delta="+(gcAfter[2]-gcBefore[2])+
                              " approximate_gc_accounting=true uncontrolled=true");
                          """
segment=segment.replace("h.succeed();",observe+"h.succeed();",1)
assert segment.count(marker)==1
assert segment.count("REAL_SERVER_TICK_RING_V1 samples=")==1
assert segment.count("REAL_SERVER_GC_WINDOW_V1 beans=")==1
p.write_text(s[:a]+segment+s[b:], encoding="utf-8")
print("SERVER_TICK_GC_GAMETEST_PROBE_V1 PASS")
