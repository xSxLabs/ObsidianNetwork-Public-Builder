# BUILD-LOCK — v1.1.0 Build 490

Status: USER-TESTED OK / BUILD-LOCK / CURRENT v1.1.0 STABLE

User runtime verification:
- Facades are visible again.
- This fixes the facade regression present after B677 / in prior v1.1.0 builds.
- Tesseract recipe fix remains part of v1.1.0.

Facade root cause/fix:
- Later client renderer registration changes dropped the B677 CableFacadeRenderer registrations.
- Restored CableFacadeRenderer registration for NETWORK_CABLE, ENERGY_CABLE, ITEM_CABLE and FLUID_CABLE while retaining Tesseract renderer registration.

Pinned source commit: 8764ebbba0537038e58c6e71061d663729caf9f6
Pinned builder commit: 22828bea1202964644d2e59c762b6f844d9ebe77
GitHub Actions run: 37189479119
Build: 490
Artifact ID: 11298358806
Artifact digest: sha256:a4b8001e067e6889b8278275244bf78a06e6507215da7ab3c3ff5fbd530debdd

Supersedes v1.1.0 Build 484 and Build 488 stable candidates.
Future development must branch from this freeze. Do not modify this freeze without explicit unlock.
