#!/usr/bin/env python3
"""Autocrafting reservation allocation gates, with randomized conservation.

The model verifies value/ordering and unchanged-object fast path. The actual
Java runtime is additionally compiled and exercised by the regular CI suite.
"""
from dataclasses import dataclass
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

PATCH = Path(__file__).resolve().parents[1] / "patches/perf-autocraft-idle-reservation-elision.py"
REL = "dev/obsidiannetwork/platform/MinecraftAutocraftingService.java"
SOURCE = """class MinecraftAutocraftingService {
 private MinecraftAutocraftingService.ProcessingRequest reserveAvailable(MinecraftAutocraftingService.ProcessingRequest r) {
      ArrayList<MinecraftAutocraftingService.BufferedInput> out = new ArrayList<>(r.inputs().size());

      for (MinecraftAutocraftingService.BufferedInput b : r.inputs()) {
         long missing = b.target() - b.buffered();
         long take = missing <= 0L ? 0L : Math.min(missing, this.runtime.storage().index().amount(b.descriptor().key()));
         long got = take <= 0L ? 0L : this.runtime.storage().extract(b.descriptor().key(), take);
         if (got > 0L) {
            diag("RESERVE");
         }

         out.add(new MinecraftAutocraftingService.BufferedInput(b.descriptor(), b.perCraft(), b.target(), Math.addExact(b.buffered(), got)));
      }

      return new MinecraftAutocraftingService.ProcessingRequest(r.id(), r.output(), r.outputCount(), r.remainingCrafts(), out);
   }

   private long bufferedCrafts(MinecraftAutocraftingService.ProcessingRequest r) {
      return 0;
   }
   private record BufferedInput(ExactStackDescriptor descriptor, long perCraft, long target, long buffered) {}
   private record ProcessingRequest(long id, ExactStackDescriptor output, long outputCount, long remainingCrafts, List<MinecraftAutocraftingService.BufferedInput> inputs) {
      ProcessingRequest { inputs = List.copyOf(inputs); }
   }
}
"""


def apply(source=SOURCE):
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / REL
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(source)
        result = subprocess.run([sys.executable, str(PATCH)],
                                env=dict(os.environ, V1_SOURCE_ROOT=tmp),
                                capture_output=True, text=True)
        return result, p.read_text()


@dataclass(frozen=True)
class Buffer:
    key: int
    per_craft: int
    target: int
    buffered: int


def reserve(rows, stock, optimized=False):
    remaining_stock = dict(stock)
    updated = None if optimized else []
    got_total = 0
    for index, item in enumerate(rows):
        missing = item.target - item.buffered
        take = 0 if missing <= 0 else min(missing, remaining_stock.get(item.key, 0))
        got = take
        remaining_stock[item.key] = remaining_stock.get(item.key, 0) - got
        got_total += got
        if optimized and got > 0 and updated is None:
            updated = list(rows[:index])
        if updated is not None:
            updated.append(Buffer(item.key, item.per_craft, item.target, item.buffered + got)
                           if got else item)
    return (rows if updated is None else tuple(updated)), remaining_stock, got_total


class IdleAutocraftReservationTests(unittest.TestCase):
    def test_patch_preserves_exact_extract_and_immutable_request(self):
        result, source = apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("XSXLABS_AUTOCRAFT_IDLE_RESERVATION_ELISION_V1", source)
        self.assertIn("out == null ? r :", source)
        self.assertIn("out.addAll(r.inputs().subList(0, visited));", source)
        self.assertEqual(source.count("this.runtime.storage().extract("), 1)
        self.assertIn("Math.addExact(b.buffered(), got)", source)
        self.assertIn("return out == null ? r : new MinecraftAutocraftingService.ProcessingRequest", source)

    def test_changed_record_immutability_refuses_patch(self):
        changed = SOURCE.replace("inputs = List.copyOf(inputs);", "inputs = new ArrayList<>(inputs);")
        result, source = apply(changed)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(source, changed)

    def test_changed_extract_refuses_patch(self):
        changed = SOURCE.replace("this.runtime.storage().extract(", "this.runtime.storage().steal(")
        result, source = apply(changed)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(source, changed)

    def test_randomized_values_order_and_conservation(self):
        rng = random.Random(20902)
        no_op = changed = 0
        for _ in range(12000):
            rows = tuple(
                Buffer(rng.randrange(40), rng.randrange(1, 9), target, rng.randrange(target + 1))
                for target in (rng.randrange(1, 200) for __ in range(rng.randrange(0, 18)))
            )
            stock = {key: rng.randrange(0, 150) if rng.randrange(4) else 0 for key in range(40)}
            before_total = sum(stock.values()) + sum(r.buffered for r in rows)
            original, stock0, got0 = reserve(rows, stock)
            candidate, stock1, got1 = reserve(rows, stock, optimized=True)
            self.assertEqual(candidate, original)
            self.assertEqual(stock1, stock0)
            self.assertEqual(got1, got0)
            self.assertEqual(sum(stock1.values()) + sum(r.buffered for r in candidate), before_total)
            if got1:
                changed += 1
                self.assertIsNot(candidate, rows)
            else:
                no_op += 1
                self.assertIs(candidate, rows, "Unchanged request should be reused")
        self.assertGreater(no_op, 0)
        self.assertGreater(changed, 0)


if __name__ == "__main__":
    unittest.main()
