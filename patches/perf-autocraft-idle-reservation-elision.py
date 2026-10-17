#!/usr/bin/env python3
"""Avoid per-tick allocation when an autocrafting request reserves no items.

ProcessingRequest and BufferedInput are immutable records. Keep the exact
storage extraction, overflow check, and diagnostic behavior. A successful
reservation still builds a new immutable snapshot. Fail closed on source drift.
"""
import os
from pathlib import Path

p = Path(os.environ["V1_SOURCE_ROOT"]) / "dev/obsidiannetwork/platform/MinecraftAutocraftingService.java"
s = p.read_text(encoding="utf-8")
start_token = "private MinecraftAutocraftingService.ProcessingRequest reserveAvailable("
end_token = "private long bufferedCrafts("
assert s.count(start_token) == s.count(end_token) == 1, "Autocraft method layout changed"
assert "private record BufferedInput(" in s
assert "private record ProcessingRequest(" in s
assert "inputs = List.copyOf(inputs);" in s, "ProcessingRequest input immutability changed"
a = s.index(start_token)
b = s.index(end_token, a)
before, method, after = s[:a], s[a:b], s[b:]
old_allocation = "ArrayList<MinecraftAutocraftingService.BufferedInput> out = new ArrayList<>(r.inputs().size());"
old_append = "out.add(new MinecraftAutocraftingService.BufferedInput(b.descriptor(), b.perCraft(), b.target(), Math.addExact(b.buffered(), got)));"
old_return = "return new MinecraftAutocraftingService.ProcessingRequest(r.id(), r.output(), r.outputCount(), r.remainingCrafts(), out);"
for anchor in (old_allocation, old_append, old_return,
               "long missing = b.target() - b.buffered();",
               "long got = take <= 0L ? 0L : this.runtime.storage().extract(b.descriptor().key(), take);",
               "if (got > 0L) {"):
    assert method.count(anchor) == 1, "Reservation anchor changed: " + anchor
assert "XSXLABS_AUTOCRAFT_IDLE_RESERVATION_ELISION_V1" not in method

method = method.replace(
    old_allocation,
    "// XSXLABS_AUTOCRAFT_IDLE_RESERVATION_ELISION_V1\n"
    "      ArrayList<MinecraftAutocraftingService.BufferedInput> out = null;\n"
    "      int visited = 0;",
    1,
)
method = method.replace(
    old_append,
    """// If every extract returned zero, keep the existing immutable request.
         // On the first success, retain prior unchanged entries in order.
         if (got > 0L && out == null) {
            out = new ArrayList<>(r.inputs().size());
            out.addAll(r.inputs().subList(0, visited));
         }
         if (out != null) {
            out.add(got == 0L ? b :
                new MinecraftAutocraftingService.BufferedInput(
                    b.descriptor(), b.perCraft(), b.target(), Math.addExact(b.buffered(), got)));
         }
         visited++;""",
    1,
)
method = method.replace(old_return,
    "return out == null ? r : new MinecraftAutocraftingService.ProcessingRequest(r.id(), r.output(), r.outputCount(), r.remainingCrafts(), out);", 1)
assert method.count("out == null ? r :") == 1
p.write_text(before + method + after, encoding="utf-8")
print("AUTOCRAFT_IDLE_RESERVATION_ELISION_V1 PASS")
