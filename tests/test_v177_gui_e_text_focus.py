#!/usr/bin/env python3
"""Regression contract: xSxLabs and optional JEI search focus protect E text input."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATCH=(ROOT/"features/v177/apply-v177-gui-e-text-focus.py").read_text(encoding="utf-8")
FLOW=(ROOT/".github/workflows/networkstorage-v1.7-clean.yml").read_text(encoding="utf-8")

class TextFieldInventoryKeyTests(unittest.TestCase):
    def test_listener_covers_all_xsxlabs_screens_only(self):
        for needle in (
            'ScreenEvent.KeyPressed.Pre event',
            'screen.getClass().getName().startsWith("dev.obsidiannetwork.")',
            'mc.screen!=screen',
            '@EventBusSubscriber(modid="obsidiannetwork",value=Dist.CLIENT)',
            'mc.options.keyInventory.matches(event.getKeyEvent())',
        ):
            self.assertIn(needle,PATCH)

    def test_focused_xsxlabs_fields_consume_e_without_blocking_text(self):
        for needle in (
            'child instanceof EditBox box',
            'child instanceof MultiLineEditBox box',
            'box.isFocused()&&box.isActive()',
            'if(state.isEditing||jeiEditing){',
            'event.setCanceled(true);',
            'CharacterTyped',
        ):
            self.assertIn(needle,PATCH)
        self.assertNotIn("charTyped(",PATCH)
        self.assertNotIn("setScreen(null)",PATCH)

    def test_jei_overlay_focus_uses_optional_public_api(self):
        for needle in (
            'net.neoforged.fml.ModList.get().isLoaded("jei")',
            'V177JeiSearchFocusBridge.searchFocused()',
            'import mezz.jei.api.IModPlugin;',
            'import mezz.jei.api.JeiPlugin;',
            '@JeiPlugin',
            'onRuntimeAvailable(IJeiRuntime available)',
            'onRuntimeUnavailable()',
            'active.getIngredientListOverlay().hasKeyboardFocus()',
            'Identifier.fromNamespaceAndPath("obsidiannetwork","v177_jei_search_focus")',
        ):
            self.assertIn(needle,PATCH)
        self.assertNotIn("getDeclaredField(",PATCH)
        self.assertNotIn("Class.forName(",PATCH)
        self.assertNotIn("mezz.jei.gui.",PATCH)

    def test_e_closes_nonediting_guis_even_without_local_text_box(self):
        self.assertNotIn('if(!state.hasField)return;',PATCH)
        self.assertIn('screen.onClose();',PATCH)
        self.assertIn('java.util.IdentityHashMap<GuiEventListener,Boolean>',PATCH)
        self.assertIn('depth>8||seen.size()>256',PATCH)
        self.assertIn('event.setCanceled(true); // one close;',PATCH)

    def test_hook_applies_after_existing_v177_source_reconstruction(self):
        self.assertIn('if [ "$GITHUB_REF_NAME" = "1.7.7" ] || [ "$GITHUB_REF_NAME" = "1.7.7.1-ultra-performance" ]; then',FLOW)
        self.assertIn('python3 features/v177/apply-v177-gui-e-text-focus.py',FLOW)
        self.assertIn("test_v177_gui_e_text_focus.py",FLOW)

if __name__=="__main__":
    unittest.main()
