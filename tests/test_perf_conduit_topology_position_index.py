#!/usr/bin/env python3
"""Fail-closed topology index tests and randomized position lifecycle models."""
import os,random,subprocess,sys,tempfile,unittest
from pathlib import Path
PATCH=Path(__file__).resolve().parents[1]/"patches/spark-conduit-topology-position-index.py"
NETWORK="""class ConduitNetwork {
private final Set<ConduitNode> nodes=new HashSet<>();
public ConduitNetwork(ConduitType type,ConduitNode first){this.type=type;nodes.add(first);}
public void add(ConduitNode n){if(n.type()!=type)throw new IllegalArgumentException("type mismatch");nodes.add(n);n.network(this);dirty=true;}
public void remove(ConduitNode n){nodes.remove(n);dirty=true;}
public void replaceNodes(java.util.Collection<ConduitNode> next){var copy=new java.util.LinkedHashSet<>(next);for(var old:new java.util.ArrayList<>(nodes))if(!copy.contains(old)&&old.network()==this)old.network(new ConduitNetwork(type,old));nodes.clear();for(var n:copy){if(n.type()!=type)throw new IllegalArgumentException("type mismatch");nodes.add(n);n.network(this);}dirty=true;}
public void nodeChanged(ConduitNode n){dirty=true;}
}
"""
TOPOLOGY="""class ConduitTopology {
boolean cachedConnected=network.nodes().stream().anyMatch(n->n.pos().equals(bundle.getBlockPos().relative(d)));
if(physicallyConnected!=cachedConnected){network.nodeChanged(node);}
}
"""
def invoke(n=NETWORK,t=TOPOLOGY):
    with tempfile.TemporaryDirectory() as root:
        folder=Path(root)/"dev/obsidiannetwork/conduit"
        folder.mkdir(parents=True)
        a,b=folder/"ConduitNetwork.java",folder/"ConduitTopology.java"
        a.write_text(n);b.write_text(t)
        response=subprocess.run([sys.executable,str(PATCH)],env=dict(os.environ,V1_SOURCE_ROOT=root),capture_output=True,text=True)
        return response,a.read_text(),b.read_text()
class ConduitMembershipTests(unittest.TestCase):
    def test_all_lifecycle_methods_indexed(self):
        result,n,t=invoke()
        self.assertEqual(result.returncode,0,result.stderr)
        for token in ("indexedPositions.add(first.pos().immutable())","indexedPositions.add(n.pos().immutable())",
                      "indexedPositions.clear();for(var current:nodes)","nodes.clear();indexedPositions.clear();for(var n:copy)",
                      "return indexedPositions.contains(pos)"):
            self.assertIn(token,n)
        self.assertIn("network.containsPosition(",t)
        self.assertIn("physicallyConnected!=cachedConnected",t)
    def test_malformed_network_refuses_both_writes(self):
        altered=NETWORK.replace("nodes.remove(n);dirty=true;","nodes.remove(n);dirty=false;")
        result,a,b=invoke(altered,TOPOLOGY)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((a,b),(altered,TOPOLOGY))
    def test_malformed_topology_refuses_both_writes(self):
        altered=TOPOLOGY.replace("network.nodes().stream().anyMatch","network.nodes().parallelStream().anyMatch")
        result,a,b=invoke(NETWORK,altered)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((a,b),(NETWORK,altered))
    def test_duplicate_coordinates_and_split_merge_model_equivalence(self):
        rnd=random.Random(20261017)
        for trial in range(3000):
            nodes={}
            for _ in range(36):
                identity=rnd.randrange(0,55)
                pos=(rnd.randrange(0,8),rnd.randrange(0,4),rnd.randrange(0,8))
                action=rnd.randrange(3)
                if action==0:
                    nodes[identity]=pos
                elif action==1:
                    nodes.pop(identity,None)
                else:
                    nodes={k:(rnd.randrange(0,5),0,rnd.randrange(0,5))
                           for k in rnd.sample(range(55),rnd.randrange(0,20))}
                positions=set(nodes.values())
                query=pos if rnd.random()<.5 else (rnd.randrange(0,8),rnd.randrange(0,4),rnd.randrange(0,8))
                self.assertEqual(any(v==query for v in nodes.values()), query in positions)
    def test_idempotence_fails_closed(self):
        first,a,b=invoke()
        self.assertEqual(first.returncode,0,first.stderr)
        repeat,again_a,again_b=invoke(a,b)
        self.assertNotEqual(repeat.returncode,0)
        self.assertEqual((again_a,again_b),(a,b))
if __name__=="__main__":unittest.main()
