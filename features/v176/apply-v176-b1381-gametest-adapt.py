#!/usr/bin/env python3
"""B1381: preserve existing unlimited-transfer GameTests and test real rate budget."""
import os
from pathlib import Path
root=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork/build103"

def one(path,old,new):
    p=root/path
    s=p.read_text(encoding="utf-8")
    assert s.count(old)==1,("B1381_GAME_TEST_DRIFT",path,old[:100],s.count(old))
    p.write_text(s.replace(old,new,1),encoding="utf-8")

one("B1355EnergyGameTests.java",
    '   source.cycleSide(Direction.EAST.get3DDataValue());',
    '''    if(bank.b1381OutputLimit()!=2_000_000L)
     throw new IllegalStateException("B1381 expected default 2M FE/t");
    bank.b1381SetOutputLimit(13); // Existing B1355 5M delivery test uses original unlimited rate.
    source.cycleSide(Direction.EAST.get3DDataValue());''')

one("B1376ReactorBankGameTests.java",
    '   var formed=reactor.revalidate(w);',
    '''    if(bank.b1381OutputLimit()!=2_000_000L)
     throw new IllegalStateException("B1381 default bank rate was not 2M");
    bank.b1381SetOutputLimit(13); // Keep preexisting 5M transfer assertions.
    var formed=reactor.revalidate(w);''')

one("B1355EnergyGameTests.java",
    '    System.out.println("B1355_TWO_BILLION_FE_POWERBANK_SOURCE_OFF_FULL_SINK_PASS");',
    '''     System.out.println("B1355_TWO_BILLION_FE_POWERBANK_SOURCE_OFF_FULL_SINK_PASS");
     // B1381 real storage, real OUTPUT port, two pulls in ONE transaction.
     // The second pull must see ZERO budget and aborted transaction must
     // restore BOTH the FE balance and the rate quota.
     var b1381Port=(PowerbankBlockEntity)w.getBlockEntity(op);
     if(b1381Port==null)throw new IllegalStateException("B1381 missing output port");
     long b1381Before=bank.xsxNetworkStoredFe();
     bank.b1381SetOutputLimit(4);
     try(var capProbe=Transaction.openRoot()){
       int first=b1381Port.energyPort().extract(5_000_000,capProbe);
       int second=b1381Port.energyPort().extract(5_000_000,capProbe);
       if(first!=2_000_000||second!=0)
        throw new IllegalStateException("B1381 rate budget overflow first="+first+" second="+second);
       // Deliberately NO commit.
     }
     if(bank.xsxNetworkStoredFe()!=b1381Before)
       throw new IllegalStateException("B1381 rollback lost stored FE");
     try(var secondRoot=Transaction.openRoot()){
       int again=b1381Port.energyPort().extract(2_000_000,secondRoot);
       if(again!=2_000_000)
        throw new IllegalStateException("B1381 aborted root did not refund quota "+again);
       // Deliberately NO commit.
     }
     if(bank.xsxNetworkStoredFe()!=b1381Before)
       throw new IllegalStateException("B1381 second rollback lost stored FE");
     bank.b1381SetOutputLimit(13);
     System.out.println("B1381_POWERBANK_TWO_MILLION_RATE_AND_ROLLBACK_PASS");''')
print("B1381_REAL_SERVER_GAME_TEST_ADAPTED")
