#!/usr/bin/env python3
"""B605: fix Energy Cable facades and input collars competing for one BER slot.

Root cause proven in packaged B604 bytecode:
  ClientModEvents.registerTesseractRenderer() installs CableFacadeRenderer for
  ModBlockEntities.ENERGY_CABLE, but
  NetworkPlanterClientRenderRegistration.register() installs
  EnergyCableInputRenderer for the SAME BlockEntityType.
Only the last BlockEntityRenderer provider survives the entity-renderer map.
B602 BE sync and B603 visibility fallback cannot repair this renderer collision.

Register one composite facade+collar provider from ClientModEvents, and remove
only the redundant ENERGY registration in NetworkPlanterClientRenderRegistration.
Do NOT touch the planter renderer, cable side modes, FE flow or native armor.
"""
import os,re
from pathlib import Path
J=Path(os.environ["V1_SOURCE_ROOT"])/"dev/obsidiannetwork"
facade=J/"client/render/CableFacadeRenderer.java"
collar=J/"client/EnergyCableInputRenderer.java"
be=J/"blockentity/EnergyCableBlockEntity.java"
assert all(p.exists() for p in (facade,collar,be)), "B605_SOURCE_MISSING"
face_src=facade.read_text(encoding="utf-8")
col_src=collar.read_text(encoding="utf-8")
assert "implements BlockEntityRenderer" in face_src and "facadeModel.submit" in face_src
assert "implements BlockEntityRenderer" in col_src and "public void submit(" in col_src
assert "public static final class InputState" in col_src, "B605_COLLAR_STATE_VISIBILITY_CHANGED"
# The new combined renderer delegates to BOTH existing tested renderers.
# No new geometry, blocking, ticking, server packets or resource changes.
target=J/"client/EnergyCableCompositeRenderer.java"
assert not target.exists(), "B605_COMPOSITE_EXISTS"
target.write_text(r'''package dev.obsidiannetwork.client;

import com.mojang.blaze3d.vertex.PoseStack;
import dev.obsidiannetwork.blockentity.EnergyCableBlockEntity;
import dev.obsidiannetwork.client.render.CableFacadeRenderer;
import dev.obsidiannetwork.client.render.CableFacadeRenderState;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.blockentity.state.BlockEntityRenderState;
import net.minecraft.client.renderer.feature.ModelFeatureRenderer;
import net.minecraft.client.renderer.state.level.CameraRenderState;
import net.minecraft.world.phys.Vec3;

/**
 * B605_ENERGY_FACADE_AND_COLLAR:
 * Exactly ONE renderer provider per Energy Cable BE type.
 * Render both original facade textured model and the subtle INPUT collars.
 * No client state/sync modifications or world scans.
 */
public final class EnergyCableCompositeRenderer implements
        BlockEntityRenderer<EnergyCableBlockEntity, EnergyCableCompositeRenderer.State> {

  public static final class State extends BlockEntityRenderState {
    public final CableFacadeRenderState facade = new CableFacadeRenderState();
    public final EnergyCableInputRenderer.InputState collar = new EnergyCableInputRenderer.InputState();
  }

  private final CableFacadeRenderer<EnergyCableBlockEntity> facade;
  private final EnergyCableInputRenderer collar;

  public EnergyCableCompositeRenderer(BlockEntityRendererProvider.Context context) {
    this.facade = new CableFacadeRenderer<>(context);
    this.collar = new EnergyCableInputRenderer(context);
  }

  @Override public State createRenderState() { return new State(); }

  @Override public void extractRenderState(
      EnergyCableBlockEntity be, State state, float partialTick, Vec3 cameraPos,
      ModelFeatureRenderer.CrumblingOverlay crumblingOverlay) {
    BlockEntityRenderer.super.extractRenderState(
        be, state, partialTick, cameraPos, crumblingOverlay);
    facade.extractRenderState(be, state.facade, partialTick, cameraPos, crumblingOverlay);
    collar.extractRenderState(be, state.collar, partialTick, cameraPos, crumblingOverlay);
  }

  @Override public void submit(State state, PoseStack pose, SubmitNodeCollector collector,
                               CameraRenderState camera) {
    // Opaque facade is submitted first; the INPUT renderer itself suppresses
    // collars when this cable has an installed FACADED=true blockstate.
    facade.submit(state.facade, pose, collector, camera);
    collar.submit(state.collar, pose, collector, camera);
  }

  @Override public int getViewDistance() {
    return Math.max(facade.getViewDistance(), collar.getViewDistance());
  }
}
''', encoding="utf-8")
client=J/"client/ClientModEvents.java"
s=client.read_text(encoding="utf-8")
pat=r'(?P<prefix>event\.registerBlockEntityRenderer\s*\(\s*[\w.]*ModBlockEntities\.ENERGY_CABLE\.get\(\)\s*,\s*)(?P<old>[\w.]*CableFacadeRenderer::new)(?P<suffix>\s*\)\s*;)'
m=list(re.finditer(pat,s,re.S))
assert len(m)==1,("B605_ORIGINAL_FACADE_REGISTRATION_DRIFT",len(m))
s=s[:m[0].start("old")]+"dev.obsidiannetwork.client.EnergyCableCompositeRenderer::new"+s[m[0].end("old"):]
client.write_text(s,encoding="utf-8")
# This class was originally the Network Planter's registration class; retain
# its Planter renderer exactly as-is and remove ONLY the conflicting ENERGY one.
planter=J/"client/NetworkPlanterClientRenderRegistration.java"
s=planter.read_text(encoding="utf-8")
pattern=r'\s*event\.registerBlockEntityRenderer\s*\(\s*[\w.]*ModBlockEntities\.ENERGY_CABLE\.get\(\)\s*,\s*[\w.]*EnergyCableInputRenderer::new\s*\)\s*;'
matches=list(re.finditer(pattern,s,re.S))
assert len(matches)==1,("B605_ENERGY_SECOND_PROVIDER_CHANGED",len(matches),s[:1300])
s=s[:matches[0].start()]+s[matches[0].end():]
assert "NETWORK_PLANTER.get()" in s and "NetworkPlanterRenderer::new" in s, "B605_PLANTER_REGRESSION"
planter.write_text(s,encoding="utf-8")
assert "EnergyCableCompositeRenderer::new" in client.read_text(encoding="utf-8")
assert "EnergyCableInputRenderer::new" not in planter.read_text(encoding="utf-8")
assert "ModBlockEntities.ENERGY_CABLE.get()" not in planter.read_text(encoding="utf-8")
assert "B602_ENERGY_FACADE_FINAL_SYNC" in (J/"item/CableFacadeItem.java").read_text(encoding="utf-8")
assert "B603_FACADE_NONINVISIBLE" in (J/"block/EnergyCableBlock.java").read_text(encoding="utf-8")
print("B605_ENERGY_FACADE_COLLAR_COMPOSITE_RENDERER_SINGLE_PROVIDER_PASS")
