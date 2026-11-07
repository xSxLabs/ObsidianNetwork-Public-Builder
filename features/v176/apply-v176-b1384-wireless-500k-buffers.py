#!/usr/bin/env python3
"""B1384 real 500,000 FE buffers for Wireless TX and RX, accurate Jade values.

Apply AFTER legacy unlimited-transmitter patch: retain fast upstream charging,
64k/t receiver dispatch, rollback-safe FE and crossdimension runtime.
A receiver only refills on real demand; idle RX never empties a TX.
"""
import os
from pathlib import Path

java=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/blockentity/WirelessNetworkBlockEntity.java"
s=java.read_text("utf8")

def once(old,new,label):
 global s
 n=s.count(old)
 assert n==1,("B1384_WIRELESS_SOURCE_DRIFT",label,n,old[:130])
 s=s.replace(old,new,1)

assert "WIRELESS_HIGH_THROUGHPUT_V2" in s
assert "int remainingBudget=Math.min(MAX_TRANSFER,64000);" in s
assert "CAPACITY=64000000L;" in s
assert "B1384_REAL_500K_TX_RX" not in s

once("public static final long CAPACITY=64000000L;",
    "public static final long CAPACITY=500000L; // B1384_REAL_500K_TX_RX",
    "shared_tx_rx_capacity")
once('stored=transmitter?Math.max(0L,Math.min(CAPACITY,in.getLongOr("wireless_fe",0L))):0L;',
     'stored=Math.max(0L,Math.min(CAPACITY,in.getLongOr("wireless_fe",0L)));',
     "receiver_persistence")
once('''  public long getAmountAsLong(){
   if(transmitter)return stored;
   return level instanceof ServerLevel server?WirelessEnergyRuntime.available(server.getServer(),networkId):0L;
  }''',
     '''  public long getAmountAsLong(){return stored;}''',
     "jade_actual_local_fe")
once('public long getCapacityAsLong(){return transmitter?CAPACITY:Integer.MAX_VALUE;}',
     'public long getCapacityAsLong(){return CAPACITY;}',
     "jade_500k_both")

# True receiver FE storage is transaction-backed. It only pulls when downstream
# actually requests energy, so idle, already charged systems do not incur drain.
once(" private final class Handler implements EnergyHandler {",
     ''' // B1384 receiver buffer, funded only by committed network FE.
  public int b1384ReceiveFromNetwork(int requested,TransactionContext tx){
   if(transmitter||requested<=0||!(level instanceof ServerLevel server))return 0;
   int ask=(int)Math.min((long)requested,CAPACITY-stored);
   if(ask<=0)return 0;
   int received=WirelessEnergyRuntime.pull(server.getServer(),networkId,ask,tx);
   if(received>0){
    handler.journal.updateSnapshots(tx);
    stored+=received;
   }
   return received;
  }
  private int b1384ExtractLocal(int requested,TransactionContext tx){
   if(transmitter||requested<=0)return 0;
   int delivered=(int)Math.min((long)requested,stored);
   if(delivered>0){handler.journal.updateSnapshots(tx);stored-=delivered;}
   return delivered;
  }
  private final class Handler implements EnergyHandler {''',"receiver_storage_methods")

# Both auto-push and other mods pulling FE use this finite local storage.
once('''    return WirelessEnergyRuntime.pull(world.getServer(),networkId,Math.min(amount,64000),tx);''',
     '''    int request=Math.min(amount,64000);
    int needed=(int)Math.max(0L,request-stored);
    b1384ReceiveFromNetwork(needed,tx);
    return b1384ExtractLocal(request,tx);''',
     "receiver_capability_extract")

# Cached sender index must allow residual RX buffer discharge after the TX
# goes offline, and tally only NEW withdrawals against sender availability.
once('if(remainingBudget<=0||remainingSupply==0)break;',
     'if(remainingBudget<=0||(remainingSupply==0&&be.stored<=0L))break;',
     "tick_local_discharge")
once('if(remainingSupply<=0)break;',
     'if(remainingSupply<=0&&be.stored<=0L)break;',
     "can_discharge_without_tx")
once('int offer=Math.min(remainingBudget,remainingSupply);',
     'int offer=(int)Math.min((long)remainingBudget,(long)remainingSupply+be.stored);',
     "receiver_real_offer")
once('''    int withdrawn=WirelessEnergyRuntime.pull(server.getServer(),be.networkId,capacity,tx);
    if(withdrawn>0){
     int accepted=target.insert(withdrawn,tx);
     if(accepted==withdrawn){tx.commit();remainingBudget-=accepted;remainingSupply-=accepted;}
    }''',
     '''     int fromRemote=be.b1384ReceiveFromNetwork(
       (int)Math.max(0L,capacity-be.stored),tx);
     int fromBuffer=be.b1384ExtractLocal(capacity,tx);
     if(fromBuffer>0){
      int accepted=target.insert(fromBuffer,tx);
      if(accepted==fromBuffer){
       tx.commit();
       remainingBudget-=accepted;
       remainingSupply-=fromRemote;
      }
     }''',
     "autopush_receiver_buffer_transaction")

# No fake 64-million FE capacity, all storage is tracked via the same
# per-block journal. No receiver buffer is eagerly charged at idle.
assert "CAPACITY=64000000L" not in s
assert "return transmitter?CAPACITY:Integer.MAX_VALUE;" not in s
assert "return level instanceof ServerLevel server?WirelessEnergyRuntime.available" not in s
assert 'return WirelessEnergyRuntime.pull(world.getServer(),networkId,Math.min(amount,64000),tx);' not in s
assert 'if(accepted==fromBuffer)' in s
java.write_text(s,"utf8")
print("B1384_TX_RX_TRUE_500000_FE_BUFFER_AND_JADE_CAPACITY_PASS")
