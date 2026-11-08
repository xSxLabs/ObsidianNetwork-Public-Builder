#!/usr/bin/env python3
"""Regression contract: all mod text-input GUIs handle E without closing."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v177/apply-v177-gui-e-text-focus.py").read_text(encoding="utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class TextFieldInventoryKeyTests(unittest.TestCase):
    def test_one_global_listener_covers_all_xsxlabs_screens_only(self):
        for needle in (
            'ScreenEvent.KeyPressed.Pre event',
            'screen.getClass().getName().startsWith("dev.obsidiannetwork.")',
            'mc.screen!=screen',
            '@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)',
            'mc.options.keyInventory.matches(event.getKeyEvent())',
        ):
            self.assertIn(needle,PATCH)

    def test_focused_fields_consume_e_and_leave_character_input_intact(self):
        for needle in (
            'child instanceof EditBox box',
            'child instanceof MultiLineEditBox box',
            'box.isFocused()&&box.isActive()',
            'if(state.isEditing){',
            'event.setCanceled(true);',
            'CharacterTyped event',
        ):
            self.assertIn(needle,PATCH)
        self.assertNotIn("charTyped(",PATCH)
        self.assertNotIn("setScreen(null)",PATCH)

    def test_nonfocused_field_closes_and_nontextfield_screen_untouched(self):
        for needle in (
            'if(!state.hasField)return;',
            '}else{',
            'screen.onClose();',
            'java.util.IdentityHashMap<GuiEventListener,Boolean>',
            'depth>8||seen.size()>256',
        ):
            self.assertIn(needle,PATCH)

    def test_hook_applies_only_after_existing_v177_source_reconstruction(self):
        self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ]; then',FLOW)
        self.assertIn('python3 features/v177/apply-v177-gui-e-text-focus.py',FLOW)

if __name__=="__main__":
    unittest.main()
