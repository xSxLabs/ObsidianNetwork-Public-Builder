#!/usr/bin/env python3
"""B1384 real FE GameTest: correct new 500k TX cap and RX true buffer rollback."""
import os
from pathlib import Path
p=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103/Build103GameTests.java"
s=p.read_text("utf8")
assert 'WIRELESS_ONE_TX_EIGHT_RX_V1 ARMED' in s
assert 'WIRELESS_REAL_FE_TRANSFER_GAMETEST_V1 PASS' in s

def once(old,new,label):
 global s
 count=s.count(old)
 assert count==1,("B1384_WIRELESS_GT_DRIFT",label,count,old[:115])
 s=s.replace(old,new,1)

# The old diagnostic funded 512k in ONE TX; new physical capacity is 500k.
# 480k keeps all eight real receivers active while respecting the new cap.
once("singleTx.energyHandler().insert(512000,funding)==512000",
     "singleTx.energyHandler().insert(480000,funding)==480000","fanout_insert")
once("singleTx.stored()==512000","singleTx.stored()==480000","fanout_stored")
once("conservation==512000L","conservation==480000L","fanout_conservation")

once('''                      check(rx!=null&&!rx.isTransmitter()&&fanoutSink!=null,
                        "WIRELESS fanout real receiver and sink placed");''',
'''                      check(rx!=null&&!rx.isTransmitter()&&fanoutSink!=null,
                        "WIRELESS fanout real receiver and sink placed");
                      check(rx.energyHandler().getCapacityAsLong()==500000L&&rx.stored()==0L,
                        "B1384_REAL_RX_500K_JADE_CAPACITY");''',
"rx_cap")

once('''                      check(singleTx.stored()==480000,
                       "WIRELESS one TX holds committed 512000 FE");''',
'''                      check(singleTx.stored()==480000,
                       "WIRELESS one TX holds committed 480000 FE");
                      check(singleTx.energyHandler().getCapacityAsLong()==500000L,
                       "B1384_REAL_TX_500K_JADE_CAPACITY");
                      var rxAtFirst=(dev.obsidiannetwork.blockentity.WirelessNetworkBlockEntity)
                        world.getBlockEntity(new BlockPos(4162,80,4161));
                      check(rxAtFirst!=null,"B1384 real receiver exists");
                      // A real RX can temporarily hold 480k. When the root aborts,
                      // BOTH its buffer and the physical TX must revert exactly.
                      try(var b1384Probe=net.neoforged.neoforge.transfer.transaction.Transaction.openRoot()){
                       int filled=rxAtFirst.b1384ReceiveFromNetwork(480000,b1384Probe);
                       check(filled==480000&&rxAtFirst.stored()==480000L
                         &&singleTx.stored()==0L,"B1384_REAL_RX_BUFFER_RECEIVES_480K");
                      }
                      check(rxAtFirst.stored()==0L&&singleTx.stored()==480000L,
                       "B1384_ROLLBACK_RESTORES_BOTH_BUFFERS");
                      System.out.println("B1384_REAL_WIRELESS_500K_TX_RX_AND_ROLLBACK_PASS");''',
"tx_capacity_real_receiver")

assert 'B1384_REAL_WIRELESS_500K_TX_RX_AND_ROLLBACK_PASS' in s
p.write_text(s,"utf8")
print("B1384_WIRELESS_500K_GAMETEST_PATCH_PASS")
