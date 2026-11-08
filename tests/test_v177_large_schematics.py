#!/usr/bin/env python3
"""v177 schematics contract: 30m cap, server-only imports, no item NBT explosion."""
from pathlib import Path
import ast
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v177/apply-v177-large-schematics.py").read_text(encoding="utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class LargeSchematics(unittest.TestCase):
 def test_source_python_compiles(self):
  ast.parse(PATCH)
 def test_thirty_million_ceiling_for_both_selection_and_import(self):
  for key in (
   "public static final int MAX_BLOCKS=30_000_000;",
   "public static final int MAX=30_000_000;",
   "total>MAX",
   "count>V177SchematicStore.MAX",
   "2,048 per tick",
   "PER_TICK=2048",
   "Math.abs((long)second.getX()-first.getX())",
  ):self.assertIn(key,PATCH)
 def test_server_directory_and_command(self):
  for key in (
   'Commands.literal("xsxschematic")',
   'Commands.literal("load")',
   'StringArgumentType.word()',
   'resolve("xsxschematics")',
   'server.getServerDirectory()',
   'server.getWorldPath(LevelResource.ROOT)',
   'String name',
   'importedFile(server,name)',
   'player.setItemInHand(hand,finished);',
   'ObsidianNetwork.NETWORK_SCHEMATIC_QUILL.get()',
  ):self.assertIn(key,PATCH)
 def test_worldedit_v2_v3_and_no_untrusted_tiles(self):
  for key in (
   'version!=2&&version!=3',
   'schem.getCompoundOrEmpty("Blocks")',
   'version==3?"Data":"BlockData"',
   'NbtIo.readCompressed(file,NbtAccounter.create(MAX_NBT_BYTES))',
   'if(cursor!=bytes.length)',
   'sy*sz',
   'Truncated/invalid varint',
   'Untrusted block-entity inventories, entities and biomes deliberately excluded.',
  ):self.assertIn(key,PATCH)
 def test_server_auto_folder_and_creative_access(self):
  for key in (
   "ServerStartedEvent event",
   "V177SchematicStore.imports(event.getServer());",
   'output.accept((ItemLike)NETWORK_PRINTER_ITEM.get());',
   'output.accept((ItemLike)NETWORK_SCHEMATIC_QUILL.get());',
   'output.accept((ItemLike)NETWORK_BLUEPRINT.get());',
   'V177_SCHEM_QUILL_PRINTER_REEXPOSED_IN_CREATIVE_JEI_AND_RECIPES',
   'network_schematic_quill.json',
   'network_printer.json',
   'WORLD',
   'Files.isSymbolicLink(file)',
   'loadedChunks>=1',
  ):
   if key=='WORLD':continue
   self.assertIn(key,PATCH)
 def test_capture_loads_at_most_one_chunk_each_tick(self):
  for key in (
   'int loadedChunks=0;',
   'if(loadedChunks>=1){t.next--;break;}',
   'world.getChunk(pos.getX()>>4,pos.getZ()>>4)',
   'world.getWorldBorder().isWithinBounds(pos)',
  ):self.assertIn(key,PATCH)
 def test_async_and_no_raw_30m_network_packets(self):
  for key in (
   'CompletableFuture.supplyAsync',
   'CompletableFuture.runAsync',
   'server.execute(()->',
   'NETWORK_BLUEPRINT.get()',
   '"xsxlabs_schem_id"',
   'new AbstractList<>()',
   'public String get(int i){return p.block(i);}',
   'V177SchematicStore.state(',
   'if(player.getItemInHand(hand)!=original)',
   'if(player.getItemInHand(t.hand)!=t.source)',
   'if(!world.hasChunkAt(pos))',
  ):self.assertIn(key,PATCH)
  self.assertNotIn('String.join(",",out)',PATCH)
 def test_build_runs_after_173_and_in_v177_scope(self):
  base=FLOW.index('python3 features/v173/apply-blueprint-limits-378.py')
  end=FLOW.index('python3 features/v173/apply-blueprint-visible-392.py',base)
  task=FLOW.index('python3 features/v177/apply-v177-large-schematics.py')
  self.assertLess(end,task)
  self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',FLOW)
  self.assertIn("python3 tests/test_v177_large_schematics.py",FLOW)

if __name__=="__main__":
 unittest.main()
