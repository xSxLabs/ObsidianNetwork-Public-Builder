# Version Branch Policy — xSxLabs Network Storage

**Mandatory user-approved rule (2026-10-31): every new mod version has its own GitHub development branch.**

| Version | Development branch | Starting point |
| --- | --- | --- |
| v1.7.4 | `freeze/v1.7.4-build601` (immutable) | Released Build 601, SHA `8de5b9f483b8f8f33a039bf19e2d654ddbb6d284` |
| v1.7.5 | `v1.7.5` | v1.7.4 frozen Build 601 |
| v1.7.6 | `v1.7.6` (create **when starting** v1.7.6) | Frozen, accepted v1.7.5 |
| v1.7.7 | `v1.7.7` (create **when starting** v1.7.7) | Frozen, accepted v1.7.6 |

Each later version follows the same procedure: new branch `vMAJOR.MINOR.PATCH` from the previous accepted frozen version; never develop a new version on an older version's branch. When a version receives in-game acceptance, pin its exact successful commit in a separate immutable freeze branch. Never rewrite freeze branches or silently backport changes.

**v1.7.5:** Animation-only changes, all Power Armor tiers. Integrate the uploaded animation patch completely; keep source item ownership, equip/unequip/recall and all existing functionality. Full CI build is prohibited until integration, rig mappings, texture continuity, tests, and animation states are reviewed.
