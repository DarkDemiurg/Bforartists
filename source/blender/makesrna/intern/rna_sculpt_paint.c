/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

/** \file
 * \ingroup RNA
 */

#include <stdlib.h>

#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "rna_internal.h"

#include "DNA_ID.h"
#include "DNA_gpencil_types.h"
#include "DNA_scene_types.h"
#include "DNA_brush_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "BKE_material.h"
#include "BKE_paint.h"
#include "BKE_brush.h"

#include "ED_image.h"

#include "WM_api.h"
#include "WM_types.h"

#include "bmesh.h"

const EnumPropertyItem rna_enum_particle_edit_hair_brush_items[] = {
    {PE_BRUSH_COMB, "COMB", 0, "Comb", "Comb hairs"},
    {PE_BRUSH_SMOOTH, "SMOOTH", 0, "Smooth", "Smooth hairs"},
    {PE_BRUSH_ADD, "ADD", 0, "Add", "Add hairs"},
    {PE_BRUSH_LENGTH, "LENGTH", 0, "Length", "Make hairs longer or shorter"},
    {PE_BRUSH_PUFF, "PUFF", 0, "Puff", "Make hairs stand up"},
    {PE_BRUSH_CUT, "CUT", 0, "Cut", "Cut hairs"},
    {PE_BRUSH_WEIGHT, "WEIGHT", 0, "Weight", "Weight hair particles"},
    {0, NULL, 0, NULL, NULL},
};

const EnumPropertyItem rna_enum_gpencil_sculpt_brush_items[] = {
    {GP_SCULPT_TYPE_SMOOTH, "SMOOTH", ICON_GPBRUSH_SMOOTH, "Smooth", "Smooth stroke points"},
    {GP_SCULPT_TYPE_THICKNESS,
     "THICKNESS",
     ICON_GPBRUSH_THICKNESS,
     "Thickness",
     "Adjust thickness of strokes"},
    {GP_SCULPT_TYPE_STRENGTH,
     "STRENGTH",
     ICON_GPBRUSH_STRENGTH,
     "Strength",
     "Adjust color strength of strokes"},
    {GP_SCULPT_TYPE_RANDOMIZE,
     "RANDOMIZE",
     ICON_GPBRUSH_RANDOMIZE,
     "Randomize",
     "Introduce jitter/randomness into strokes"},
    {GP_SCULPT_TYPE_GRAB,
     "GRAB",
     ICON_GPBRUSH_GRAB,
     "Grab",
     "Translate the set of points initially within the brush circle"},
    {GP_SCULPT_TYPE_PUSH,
     "PUSH",
     ICON_GPBRUSH_PUSH,
     "Push",
     "Move points out of the way, as if combing them"},
    {GP_SCULPT_TYPE_TWIST,
     "TWIST",
     ICON_GPBRUSH_TWIST,
     "Twist",
     "Rotate points around the midpoint of the brush"},
    {GP_SCULPT_TYPE_PINCH,
     "PINCH",
     ICON_GPBRUSH_PINCH,
     "Pinch",
     "Pull points towards the midpoint of the brush"},
    {GP_SCULPT_TYPE_CLONE,
     "CLONE",
     ICON_GPBRUSH_CLONE,
     "Clone",
     "Paste copies of the strokes stored on the clipboard"},
    {0, NULL, 0, NULL, NULL}};

const EnumPropertyItem rna_enum_gpencil_weight_brush_items[] = {
    {GP_SCULPT_TYPE_WEIGHT,
     "WEIGHT",
     ICON_GPBRUSH_WEIGHT,
     "Weight",
     "Weight Paint for Vertex Groups"},
    {0, NULL, 0, NULL, NULL},
};

#ifndef RNA_RUNTIME
static const EnumPropertyItem rna_enum_gpencil_lock_axis_items[] = {
    {GP_LOCKAXIS_VIEW,
     "VIEW",
     ICON_VIEW,
     "View",
     "Align strokes to current view plane"},
    {GP_LOCKAXIS_Y,
     "AXIS_Y",
     ICON_AXIS_FRONT,
     "Front (X-Z)",
     "Project strokes to plane locked to Y"},
    {GP_LOCKAXIS_X,
     "AXIS_X",
     ICON_AXIS_SIDE,
     "Side (Y-Z)",
     "Project strokes to plane locked to X"},
    {GP_LOCKAXIS_Z, "AXIS_Z", ICON_AXIS_TOP, "Top (X-Y)", "Project strokes to plane locked to Z"},
    {GP_LOCKAXIS_CURSOR,
     "CURSOR",
     ICON_PIVOT_CURSOR,
     "Cursor",
     "Align strokes to current 3D cursor orientation"},
    {0, NULL, 0, NULL, NULL},
};
#endif

const EnumPropertyItem rna_enum_symmetrize_direction_items[] = {
    {BMO_SYMMETRIZE_NEGATIVE_X, "NEGATIVE_X", 0, "-X to +X", ""},
    {BMO_SYMMETRIZE_POSITIVE_X, "POSITIVE_X", 0, "+X to -X", ""},

    {BMO_SYMMETRIZE_NEGATIVE_Y, "NEGATIVE_Y", 0, "-Y to +Y", ""},
    {BMO_SYMMETRIZE_POSITIVE_Y, "POSITIVE_Y", 0, "+Y to -Y", ""},

    {BMO_SYMMETRIZE_NEGATIVE_Z, "NEGATIVE_Z", 0, "-Z to +Z", ""},
    {BMO_SYMMETRIZE_POSITIVE_Z, "POSITIVE_Z", 0, "+Z to -Z", ""},
    {0, NULL, 0, NULL, NULL},
};

#ifdef RNA_RUNTIME
#  include "MEM_guardedalloc.h"

#  include "BKE_collection.h"
#  include "BKE_context.h"
#  include "BKE_particle.h"
#  include "BKE_pbvh.h"
#  include "BKE_pointcache.h"
#  include "BKE_object.h"
#  include "BKE_gpencil.h"

#  include "DEG_depsgraph.h"

#  include "ED_particle.h"

static void rna_GPencil_update(Main *UNUSED(bmain), Scene *scene, PointerRNA *UNUSED(ptr))
{
  /* mark all grease pencil datablocks of the scene */
  FOREACH_SCENE_COLLECTION_BEGIN (scene, collection) {
    FOREACH_COLLECTION_OBJECT_RECURSIVE_BEGIN (collection, ob) {
      if (ob->type == OB_GPENCIL) {
        bGPdata *gpd = (bGPdata *)ob->data;
        gpd->flag |= GP_DATA_CACHE_IS_DIRTY;
        DEG_id_tag_update(&gpd->id, ID_RECALC_TRANSFORM | ID_RECALC_GEOMETRY);
      }
    }
    FOREACH_COLLECTION_OBJECT_RECURSIVE_END;
  }
  FOREACH_SCENE_COLLECTION_END;

  WM_main_add_notifier(NC_GPENCIL | NA_EDITED, NULL);
}

const EnumPropertyItem rna_enum_particle_edit_disconnected_hair_brush_items[] = {
    {PE_BRUSH_COMB, "COMB", ICON_PARTICLEBRUSH_COMB, "Comb", "Comb hairs"},
    {PE_BRUSH_SMOOTH, "SMOOTH", ICON_PARTICLEBRUSH_SMOOTH, "Smooth", "Smooth hairs"},
    {PE_BRUSH_LENGTH, "LENGTH", ICON_PARTICLEBRUSH_ADD, "Length", "Make hairs longer or shorter"},
    {PE_BRUSH_CUT, "CUT", ICON_CUT, "Cut", "Cut hairs"},
    {PE_BRUSH_WEIGHT, "WEIGHT", ICON_PARTICLEBRUSH_WEIGHT, "Weight", "Weight hair particles"},
    {0, NULL, 0, NULL, NULL},
};

static const EnumPropertyItem particle_edit_cache_brush_items[] = {
    {PE_BRUSH_COMB, "COMB", 0, "Comb", "Comb paths"},
    {PE_BRUSH_SMOOTH, "SMOOTH", 0, "Smooth", "Smooth paths"},
    {PE_BRUSH_LENGTH, "LENGTH", 0, "Length", "Make paths longer or shorter"},
    {0, NULL, 0, NULL, NULL},
};

static PointerRNA rna_ParticleEdit_brush_get(PointerRNA *ptr)
{
  ParticleEditSettings *pset = (ParticleEditSettings *)ptr->data;
  ParticleBrushData *brush = NULL;

  brush = &pset->brush[pset->brushtype];

  return rna_pointer_inherit_refine(ptr, &RNA_ParticleBrush, brush);
}

static PointerRNA rna_ParticleBrush_curve_get(PointerRNA *ptr)
{
  return rna_pointer_inherit_refine(ptr, &RNA_CurveMapping, NULL);
}

static void rna_ParticleEdit_redo(bContext *C, PointerRNA *UNUSED(ptr))
{
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob = OBACT(view_layer);
  PTCacheEdit *edit = PE_get_current(scene, ob);

  if (!edit)
    return;

  if (ob)
    DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);

  BKE_particle_batch_cache_dirty_tag(edit->psys, BKE_PARTICLE_BATCH_DIRTY_ALL);
  psys_free_path_cache(edit->psys, edit);
  DEG_id_tag_update(&CTX_data_scene(C)->id, ID_RECALC_COPY_ON_WRITE);
}

static void rna_ParticleEdit_update(bContext *C, PointerRNA *UNUSED(ptr))
{
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob = OBACT(view_layer);

  if (ob)
    DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);

  /* Sync tool setting changes from original to evaluated scenes. */
  DEG_id_tag_update(&CTX_data_scene(C)->id, ID_RECALC_COPY_ON_WRITE);
}

static void rna_ParticleEdit_tool_set(PointerRNA *ptr, int value)
{
  ParticleEditSettings *pset = (ParticleEditSettings *)ptr->data;

  /* redraw hair completely if weight brush is/was used */
  if ((pset->brushtype == PE_BRUSH_WEIGHT || value == PE_BRUSH_WEIGHT) && pset->object) {
    Object *ob = pset->object;
    if (ob) {
      DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);
      WM_main_add_notifier(NC_OBJECT | ND_PARTICLE | NA_EDITED, NULL);
    }
  }

  pset->brushtype = value;
}
static const EnumPropertyItem *rna_ParticleEdit_tool_itemf(bContext *C,
                                                           PointerRNA *UNUSED(ptr),
                                                           PropertyRNA *UNUSED(prop),
                                                           bool *UNUSED(r_free))
{
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob = OBACT(view_layer);
#  if 0
  Scene *scene = CTX_data_scene(C);
  PTCacheEdit *edit = PE_get_current(scene, ob);
  ParticleSystem *psys = edit ? edit->psys : NULL;
#  else
  /* use this rather than PE_get_current() - because the editing cache is
   * dependent on the cache being updated which can happen after this UI
   * draws causing a glitch [#28883] */
  ParticleSystem *psys = psys_get_current(ob);
#  endif

  if (psys) {
    if (psys->flag & PSYS_GLOBAL_HAIR) {
      return rna_enum_particle_edit_disconnected_hair_brush_items;
    }
    else {
      return rna_enum_particle_edit_hair_brush_items;
    }
  }

  return particle_edit_cache_brush_items;
}

static bool rna_ParticleEdit_editable_get(PointerRNA *ptr)
{
  ParticleEditSettings *pset = (ParticleEditSettings *)ptr->data;

  return (pset->object && pset->scene && PE_get_current(pset->scene, pset->object));
}
static bool rna_ParticleEdit_hair_get(PointerRNA *ptr)
{
  ParticleEditSettings *pset = (ParticleEditSettings *)ptr->data;

  if (pset->scene) {
    PTCacheEdit *edit = PE_get_current(pset->scene, pset->object);

    return (edit && edit->psys);
  }

  return 0;
}

static char *rna_ParticleEdit_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.particle_edit");
}

static bool rna_Brush_mode_poll(PointerRNA *ptr, PointerRNA value)
{
  const Paint *paint = ptr->data;
  Brush *brush = value.id.data;
  const uint tool_offset = paint->runtime.tool_offset;
  const eObjectMode ob_mode = paint->runtime.ob_mode;
  UNUSED_VARS_NDEBUG(tool_offset);
  BLI_assert(tool_offset && ob_mode);

  if (brush->ob_mode & ob_mode) {
    if (paint->brush) {
      if (BKE_brush_tool_get(paint->brush, paint) == BKE_brush_tool_get(brush, paint)) {
        return true;
      }
    }
    else {
      return true;
    }
  }

  return false;
}

static bool paint_contains_brush_slot(const Paint *paint, const PaintToolSlot *tslot, int *r_index)
{
  if ((tslot >= paint->tool_slots) && (tslot < (paint->tool_slots + paint->tool_slots_len))) {
    *r_index = (int)(tslot - paint->tool_slots);
    return true;
  }
  return false;
}

static bool rna_Brush_mode_with_tool_poll(PointerRNA *ptr, PointerRNA value)
{
  Scene *scene = (Scene *)ptr->id.data;
  const PaintToolSlot *tslot = ptr->data;
  ToolSettings *ts = scene->toolsettings;
  Brush *brush = value.id.data;
  int mode = 0;
  int slot_index = 0;

  if (paint_contains_brush_slot(&ts->imapaint.paint, tslot, &slot_index)) {
    if (slot_index != brush->imagepaint_tool) {
      return false;
    }
    mode = OB_MODE_TEXTURE_PAINT;
  }
  else if (paint_contains_brush_slot(&ts->sculpt->paint, tslot, &slot_index)) {
    if (slot_index != brush->sculpt_tool) {
      return false;
    }
    mode = OB_MODE_SCULPT;
  }
  else if (paint_contains_brush_slot(&ts->uvsculpt->paint, tslot, &slot_index)) {
    if (slot_index != brush->uv_sculpt_tool) {
      return false;
    }
    mode = OB_MODE_EDIT;
  }
  else if (paint_contains_brush_slot(&ts->vpaint->paint, tslot, &slot_index)) {
    if (slot_index != brush->vertexpaint_tool) {
      return false;
    }
    mode = OB_MODE_VERTEX_PAINT;
  }
  else if (paint_contains_brush_slot(&ts->wpaint->paint, tslot, &slot_index)) {
    if (slot_index != brush->weightpaint_tool) {
      return false;
    }
    mode = OB_MODE_WEIGHT_PAINT;
  }
  else if (paint_contains_brush_slot(&ts->gp_paint->paint, tslot, &slot_index)) {
    if (slot_index != brush->gpencil_tool) {
      return false;
    }
    mode = OB_MODE_PAINT_GPENCIL;
  }

  return brush->ob_mode & mode;
}

static void rna_Sculpt_update(bContext *C, PointerRNA *UNUSED(ptr))
{
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob = OBACT(view_layer);

  if (ob) {
    DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);
    WM_main_add_notifier(NC_OBJECT | ND_MODIFIER, ob);

    if (ob->sculpt) {
      ob->sculpt->bm_smooth_shading = ((scene->toolsettings->sculpt->flags &
                                        SCULPT_DYNTOPO_SMOOTH_SHADING) != 0);
    }
  }
}

static void rna_Sculpt_ShowDiffuseColor_update(bContext *C, PointerRNA *UNUSED(ptr))
{
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob = OBACT(view_layer);

  if (ob && ob->sculpt) {
    Scene *scene = CTX_data_scene(C);
    Sculpt *sd = scene->toolsettings->sculpt;
    ob->sculpt->show_diffuse_color = ((sd->flags & SCULPT_SHOW_DIFFUSE) != 0);

    if (ob->sculpt->pbvh)
      pbvh_show_diffuse_color_set(ob->sculpt->pbvh, ob->sculpt->show_diffuse_color);

    DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);
    WM_main_add_notifier(NC_OBJECT | ND_MODIFIER, ob);
  }
}

static void rna_Sculpt_ShowMask_update(bContext *C, PointerRNA *UNUSED(ptr))
{
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *object = OBACT(view_layer);
  if (object == NULL || object->sculpt == NULL) {
    return;
  }
  Scene *scene = CTX_data_scene(C);
  Sculpt *sd = scene->toolsettings->sculpt;
  object->sculpt->show_mask = ((sd->flags & SCULPT_HIDE_MASK) == 0);
  if (object->sculpt->pbvh != NULL) {
    pbvh_show_mask_set(object->sculpt->pbvh, object->sculpt->show_mask);
  }
  DEG_id_tag_update(&object->id, ID_RECALC_GEOMETRY);
  WM_main_add_notifier(NC_OBJECT | ND_MODIFIER, object);
}

static char *rna_Sculpt_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.sculpt");
}

static char *rna_VertexPaint_path(PointerRNA *ptr)
{
  Scene *scene = (Scene *)ptr->id.data;
  ToolSettings *ts = scene->toolsettings;
  if (ptr->data == ts->vpaint) {
    return BLI_strdup("tool_settings.vertex_paint");
  }
  else {
    return BLI_strdup("tool_settings.weight_paint");
  }
}

static char *rna_ImagePaintSettings_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.image_paint");
}

static char *rna_UvSculpt_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.uv_sculpt");
}

static char *rna_GpPaint_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.gpencil_paint");
}

static char *rna_ParticleBrush_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.particle_edit.brush");
}

static void rna_Paint_brush_update(Main *UNUSED(bmain), Scene *UNUSED(scene), PointerRNA *ptr)
{
  Paint *paint = ptr->data;
  Brush *br = paint->brush;
  BKE_paint_invalidate_overlay_all();
  /* Needed because we're not calling 'BKE_paint_brush_set' which handles this. */
  BKE_paint_toolslots_brush_update(paint);
  WM_main_add_notifier(NC_BRUSH | NA_SELECTED, br);
}

static void rna_ImaPaint_viewport_update(Main *UNUSED(bmain),
                                         Scene *UNUSED(scene),
                                         PointerRNA *UNUSED(ptr))
{
  /* not the best solution maybe, but will refresh the 3D viewport */
  WM_main_add_notifier(NC_OBJECT | ND_DRAW, NULL);
}

static void rna_ImaPaint_mode_update(bContext *C, PointerRNA *UNUSED(ptr))
{
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob = OBACT(view_layer);

  if (ob && ob->type == OB_MESH) {
    /* of course we need to invalidate here */
    BKE_texpaint_slots_refresh_object(scene, ob);

    /* We assume that changing the current mode will invalidate the uv layers
     * so we need to refresh display. */
    BKE_paint_proj_mesh_data_check(scene, ob, NULL, NULL, NULL, NULL);
    WM_main_add_notifier(NC_OBJECT | ND_DRAW, NULL);
  }
}

static void rna_ImaPaint_stencil_update(bContext *C, PointerRNA *UNUSED(ptr))
{
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob = OBACT(view_layer);

  if (ob && ob->type == OB_MESH) {
    BKE_paint_proj_mesh_data_check(scene, ob, NULL, NULL, NULL, NULL);
    WM_main_add_notifier(NC_OBJECT | ND_DRAW, NULL);
  }
}

static void rna_ImaPaint_canvas_update(bContext *C, PointerRNA *UNUSED(ptr))
{
  Main *bmain = CTX_data_main(C);
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  Object *ob = OBACT(view_layer);
  Object *obedit = OBEDIT_FROM_OBACT(ob);
  bScreen *sc;
  Image *ima = scene->toolsettings->imapaint.canvas;

  for (sc = bmain->screens.first; sc; sc = sc->id.next) {
    ScrArea *sa;
    for (sa = sc->areabase.first; sa; sa = sa->next) {
      SpaceLink *slink;
      for (slink = sa->spacedata.first; slink; slink = slink->next) {
        if (slink->spacetype == SPACE_IMAGE) {
          SpaceImage *sima = (SpaceImage *)slink;

          if (!sima->pin)
            ED_space_image_set(bmain, sima, obedit, ima, true);
        }
      }
    }
  }

  if (ob && ob->type == OB_MESH) {
    BKE_paint_proj_mesh_data_check(scene, ob, NULL, NULL, NULL, NULL);
    WM_main_add_notifier(NC_OBJECT | ND_DRAW, NULL);
  }
}

static bool rna_ImaPaint_detect_data(ImagePaintSettings *imapaint)
{
  return imapaint->missing_data == 0;
}

static PointerRNA rna_GPencilSculptSettings_brush_get(PointerRNA *ptr)
{
  GP_Sculpt_Settings *gset = (GP_Sculpt_Settings *)ptr->data;
  GP_Sculpt_Data *brush = NULL;

  if ((gset) && (gset->flag & GP_SCULPT_SETT_FLAG_WEIGHT_MODE)) {
    if ((gset->weighttype >= GP_SCULPT_TYPE_WEIGHT) && (gset->weighttype < GP_SCULPT_TYPE_MAX))
      brush = &gset->brush[gset->weighttype];
  }
  else {
    if ((gset->brushtype >= 0) && (gset->brushtype < GP_SCULPT_TYPE_WEIGHT))
      brush = &gset->brush[gset->brushtype];
  }
  return rna_pointer_inherit_refine(ptr, &RNA_GPencilSculptBrush, brush);
}

static char *rna_GPencilSculptSettings_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.gpencil_sculpt");
}

static char *rna_GPencilSculptBrush_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.gpencil_sculpt.brush");
}

static char *rna_GPencilSculptGuide_path(PointerRNA *UNUSED(ptr))
{
  return BLI_strdup("tool_settings.gpencil_sculpt.guide");
}

#else

static void rna_def_paint_curve(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "PaintCurve", "ID");
  RNA_def_struct_ui_text(srna, "Paint Curve", "");
  RNA_def_struct_ui_icon(srna, ICON_CURVE_BEZCURVE);
}

static void rna_def_paint_tool_slot(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "PaintToolSlot", NULL);
  RNA_def_struct_ui_text(srna, "Paint Tool Slot", "");

  prop = RNA_def_property(srna, "brush", PROP_POINTER, PROP_NONE);
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_pointer_funcs(prop, NULL, NULL, NULL, "rna_Brush_mode_with_tool_poll");
  RNA_def_property_ui_text(prop, "Brush", "");
}

static void rna_def_paint(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "Paint", NULL);
  RNA_def_struct_ui_text(srna, "Paint", "");

  /* Global Settings */
  prop = RNA_def_property(srna, "brush", PROP_POINTER, PROP_NONE);
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_pointer_funcs(prop, NULL, NULL, NULL, "rna_Brush_mode_poll");
  RNA_def_property_ui_text(prop, "Brush", "Brush\nActive Brush");
  RNA_def_property_update(prop, 0, "rna_Paint_brush_update");

  /* paint_tool_slots */
  prop = RNA_def_property(srna, "tool_slots", PROP_COLLECTION, PROP_NONE);
  RNA_def_property_collection_sdna(prop, NULL, "tool_slots", "tool_slots_len");
  RNA_def_property_struct_type(prop, "PaintToolSlot");
  /* don't dereference pointer! */
  RNA_def_property_collection_funcs(
      prop, NULL, NULL, NULL, "rna_iterator_array_get", NULL, NULL, NULL, NULL);
  RNA_def_property_ui_text(prop, "Paint Tool Slots", "");

  prop = RNA_def_property(srna, "palette", PROP_POINTER, PROP_NONE);
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_pointer_funcs(prop, NULL, NULL, NULL, NULL);
  RNA_def_property_ui_text(prop, "Palette", "Palette\nActive Palette");

  prop = RNA_def_property(srna, "show_brush", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", PAINT_SHOW_BRUSH);
  RNA_def_property_ui_text(prop, "Show Brush", "");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "show_brush_on_surface", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", PAINT_SHOW_BRUSH_ON_SURFACE);
  RNA_def_property_ui_text(prop, "Show Brush On Surface", "");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "show_low_resolution", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", PAINT_FAST_NAVIGATE);
  RNA_def_property_ui_text(
      prop, "Fast Navigate", "Fast Navigate\nFor multires, show low resolution while navigating the view");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "input_samples", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_int_sdna(prop, NULL, "num_input_samples");
  RNA_def_property_ui_range(prop, 1, PAINT_MAX_INPUT_SAMPLES, 0, -1);
  RNA_def_property_ui_text(
      prop, "Input Samples", "Input Samples\nAverage multiple input samples together to smooth the brush stroke");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_symmetry_x", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry_flags", PAINT_SYMM_X);
  RNA_def_property_ui_text(prop, "Symmetry X", "Symmetry X\nMirror brush across the X axis");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_symmetry_y", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry_flags", PAINT_SYMM_Y);
  RNA_def_property_ui_text(prop, "Symmetry Y", "Symmetry Y\nMirror brush across the Y axis");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_symmetry_z", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry_flags", PAINT_SYMM_Z);
  RNA_def_property_ui_text(prop, "Symmetry Z", "Symmetry Z\nMirror brush across the Z axis");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_symmetry_feather", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry_flags", PAINT_SYMMETRY_FEATHER);
  RNA_def_property_ui_text(prop,
                           "Symmetry Feathering",
                           "Symmetry Feathering\nReduce the strength of the brush where it overlaps symmetrical daubs");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "cavity_curve", PROP_POINTER, PROP_NONE);
  RNA_def_property_flag(prop, PROP_NEVER_NULL);
  RNA_def_property_ui_text(prop, "Curve", "Curve\nEditable cavity curve");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_cavity", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", PAINT_USE_CAVITY_MASK);
  RNA_def_property_ui_text(prop, "Cavity Mask", "Cavity Mask\nMask painting according to mesh geometry cavity");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "tile_offset", PROP_FLOAT, PROP_XYZ);
  RNA_def_property_float_sdna(prop, NULL, "tile_offset");
  RNA_def_property_array(prop, 3);
  RNA_def_property_range(prop, 0.01, FLT_MAX);
  RNA_def_property_ui_range(prop, 0.01, 100, 1 * 100, 2);
  RNA_def_property_ui_text(
      prop, "Tiling offset for the X Axis", "X Axis Tiling Offset\nStride at which tiled strokes are copied");

  prop = RNA_def_property(srna, "tile_x", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry_flags", PAINT_TILE_X);
  RNA_def_property_ui_text(prop, "Tile X", "Tile X\nTile along X axis");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "tile_y", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry_flags", PAINT_TILE_Y);
  RNA_def_property_ui_text(prop, "Tile Y", "Tile Y\nTile along Y axis");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "tile_z", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "symmetry_flags", PAINT_TILE_Z);
  RNA_def_property_ui_text(prop, "Tile Z", "Tile Z\nTile along Z axis");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);
}

static void rna_def_sculpt(BlenderRNA *brna)
{
  static const EnumPropertyItem detail_refine_items[] = {
      {SCULPT_DYNTOPO_SUBDIVIDE,
       "SUBDIVIDE",
       0,
       "Subdivide Edges",
       "Subdivide long edges to add mesh detail where needed"},
      {SCULPT_DYNTOPO_COLLAPSE,
       "COLLAPSE",
       0,
       "Collapse Edges",
       "Collapse short edges to remove mesh detail where possible"},
      {SCULPT_DYNTOPO_SUBDIVIDE | SCULPT_DYNTOPO_COLLAPSE,
       "SUBDIVIDE_COLLAPSE",
       0,
       "Subdivide Collapse",
       "Both subdivide long edges and collapse short edges to refine mesh detail"},
      {0, NULL, 0, NULL, NULL},
  };

  static const EnumPropertyItem detail_type_items[] = {
      {0,
       "RELATIVE",
       0,
       "Relative Detail",
       "Mesh detail is relative to the brush size and detail size"},
      {SCULPT_DYNTOPO_DETAIL_CONSTANT,
       "CONSTANT",
       0,
       "Constant Detail",
       "Mesh detail is constant in world space according to detail size"},
      {SCULPT_DYNTOPO_DETAIL_BRUSH,
       "BRUSH",
       0,
       "Brush Detail",
       "Mesh detail is relative to brush radius"},
      {SCULPT_DYNTOPO_DETAIL_MANUAL,
       "MANUAL",
       0,
       "Manual Detail",
       "Mesh detail does not change on each stroke, only when using Flood Fill"},
      {0, NULL, 0, NULL, NULL},
  };

  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "Sculpt", "Paint");
  RNA_def_struct_path_func(srna, "rna_Sculpt_path");
  RNA_def_struct_ui_text(srna, "Sculpt", "");

  prop = RNA_def_property(srna, "radial_symmetry", PROP_INT, PROP_XYZ);
  RNA_def_property_int_sdna(prop, NULL, "radial_symm");
  RNA_def_property_int_default(prop, 1);
  RNA_def_property_range(prop, 1, 64);
  RNA_def_property_ui_range(prop, 0, 32, 1, 1);
  RNA_def_property_ui_text(
      prop, "Radial Symmetry Count X Axis", "Radial Symmetry Count X Axis\nNumber of times to copy strokes across the surface");

  prop = RNA_def_property(srna, "lock_x", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_X);
  RNA_def_property_ui_text(prop, "Lock X", "Lock X\nDisallow changes to the X axis of vertices");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "lock_y", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_Y);
  RNA_def_property_ui_text(prop, "Lock Y", "Lock Y\nDisallow changes to the Y axis of vertices");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "lock_z", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_LOCK_Z);
  RNA_def_property_ui_text(prop, "Lock Z", "Lock Z\nDisallow changes to the Z axis of vertices");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_threaded", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_USE_OPENMP);
  RNA_def_property_ui_text(
      prop, "Use OpenMP", "Use OpenMP\nTake advantage of multiple CPU cores to improve sculpting performance");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_deform_only", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_ONLY_DEFORM);
  RNA_def_property_ui_text(prop,
                           "Use Deform Only",
                           "Use Deform Only\nUse only deformation modifiers (temporary disable all "
                           "constructive modifiers except multi-resolution)");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_Sculpt_update");

  prop = RNA_def_property(srna, "show_diffuse_color", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_SHOW_DIFFUSE);
  RNA_def_property_ui_text(prop,
                           "Show Diffuse Color",
                           "Show Diffuse Color\nShow diffuse color of object and overlay sculpt mask on top of it");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_Sculpt_ShowDiffuseColor_update");

  prop = RNA_def_property(srna, "show_mask", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_negative_sdna(prop, NULL, "flags", SCULPT_HIDE_MASK);
  RNA_def_property_ui_text(prop, "Show Mask", "Show Mask\nShow mask as overlay on object");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_Sculpt_ShowMask_update");

  prop = RNA_def_property(srna, "detail_size", PROP_FLOAT, PROP_PIXEL);
  RNA_def_property_ui_range(prop, 0.5, 40.0, 10, 2);
  RNA_def_property_ui_text(
      prop, "Detail Size", "Detail Size\nMaximum edge length for dynamic topology sculpting (in pixels)");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "detail_percent", PROP_FLOAT, PROP_PERCENTAGE);
  RNA_def_property_ui_range(prop, 0.5, 100.0, 10, 2);
  RNA_def_property_ui_text(
      prop,
      "Detail Percentage",
      "Detail Percentage\nMaximum edge length for dynamic topology sculpting (in brush percenage)");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "constant_detail_resolution", PROP_FLOAT, PROP_NONE);
  RNA_def_property_float_sdna(prop, NULL, "constant_detail");
  RNA_def_property_range(prop, 0.0001, FLT_MAX);
  RNA_def_property_ui_range(prop, 0.001, 1000.0, 10, 2);
  RNA_def_property_ui_text(prop,
                           "Resolution",
                           "Resolution\nMaximum edge length for dynamic topology sculpting (as divisor "
                           "of blender unit - higher value means smaller edge length)");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_smooth_shading", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flags", SCULPT_DYNTOPO_SMOOTH_SHADING);
  RNA_def_property_ui_text(prop,
                           "Smooth Shading",
                           "Smooth Shading\nShow faces in dynamic-topology mode with smooth "
                           "shading rather than flat shaded");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_Sculpt_update");

  prop = RNA_def_property(srna, "symmetrize_direction", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_items(prop, rna_enum_symmetrize_direction_items);
  RNA_def_property_ui_text(prop, "Direction", "Direction\nSource and destination for symmetrize operator");

  prop = RNA_def_property(srna, "detail_refine_method", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_bitflag_sdna(prop, NULL, "flags");
  RNA_def_property_enum_items(prop, detail_refine_items);
  RNA_def_property_ui_text(
      prop, "Detail Refine Method", "Detail Refine Method\nIn dynamic-topology mode, how to add or remove mesh detail");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "detail_type_method", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_bitflag_sdna(prop, NULL, "flags");
  RNA_def_property_enum_items(prop, detail_type_items);
  RNA_def_property_ui_text(
      prop, "Detail Type Method", "Detail Type Method\nIn dynamic-topology mode, how mesh detail size is calculated");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "gravity", PROP_FLOAT, PROP_FACTOR);
  RNA_def_property_float_sdna(prop, NULL, "gravity_factor");
  RNA_def_property_range(prop, 0.0f, 1.0f);
  RNA_def_property_ui_range(prop, 0.0f, 1.0f, 0.1, 3);
  RNA_def_property_ui_text(prop, "Gravity", "Gravity\nAmount of gravity after each dab");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "gravity_object", PROP_POINTER, PROP_NONE);
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(
      prop, "Orientation", "Orientation\nObject whose Z axis defines orientation of gravity");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);
}

static void rna_def_uv_sculpt(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "UvSculpt", "Paint");
  RNA_def_struct_path_func(srna, "rna_UvSculpt_path");
  RNA_def_struct_ui_text(srna, "UV Sculpting", "");
}

static void rna_def_gp_paint(BlenderRNA *brna)
{
  StructRNA *srna;

  srna = RNA_def_struct(brna, "GpPaint", "Paint");
  RNA_def_struct_path_func(srna, "rna_GpPaint_path");
  RNA_def_struct_ui_text(srna, "Grease Pencil Paint", "");
}

/* use for weight paint too */
static void rna_def_vertex_paint(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "VertexPaint", "Paint");
  RNA_def_struct_sdna(srna, "VPaint");
  RNA_def_struct_path_func(srna, "rna_VertexPaint_path");
  RNA_def_struct_ui_text(srna, "Vertex Paint", "Properties of vertex and weight paint mode");

  /* weight paint only */
  prop = RNA_def_property(srna, "use_group_restrict", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", VP_FLAG_VGROUP_RESTRICT);
  RNA_def_property_ui_text(prop, "Restrict", "Restrict\nRestrict painting to vertices in the group");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  /* Mirroring */
  prop = RNA_def_property(srna, "radial_symmetry", PROP_INT, PROP_XYZ);
  RNA_def_property_int_sdna(prop, NULL, "radial_symm");
  RNA_def_property_int_default(prop, 1);
  RNA_def_property_range(prop, 1, 64);
  RNA_def_property_ui_range(prop, 1, 32, 1, 1);
  RNA_def_property_ui_text(
      prop, "Radial Symmetry Count X Axis", "Radial Symmetry Count X Axis\nNumber of times to copy strokes across the surface");
}

static void rna_def_image_paint(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;
  FunctionRNA *func;

  static const EnumPropertyItem paint_type_items[] = {
      {IMAGEPAINT_MODE_MATERIAL,
       "MATERIAL",
       0,
       "Material",
       "Detect image slots from the material"},
      {IMAGEPAINT_MODE_IMAGE,
       "IMAGE",
       0,
       "Single Image",
       "Set image for texture painting directly"},
      {0, NULL, 0, NULL, NULL},
  };

  static const EnumPropertyItem paint_interp_items[] = {
      {IMAGEPAINT_INTERP_LINEAR, "LINEAR", 0, "Linear", "Linear interpolation"},
      {IMAGEPAINT_INTERP_CLOSEST,
       "CLOSEST",
       0,
       "Closest",
       "No interpolation (sample closest texel)"},
      {0, NULL, 0, NULL, NULL},
  };

  srna = RNA_def_struct(brna, "ImagePaint", "Paint");
  RNA_def_struct_sdna(srna, "ImagePaintSettings");
  RNA_def_struct_path_func(srna, "rna_ImagePaintSettings_path");
  RNA_def_struct_ui_text(srna, "Image Paint", "Properties of image and texture painting mode");

  /* functions */
  func = RNA_def_function(srna, "detect_data", "rna_ImaPaint_detect_data");
  RNA_def_function_ui_description(func, "Check if required texpaint data exist");

  /* return type */
  RNA_def_function_return(func, RNA_def_boolean(func, "ok", 1, "", ""));

  /* booleans */
  prop = RNA_def_property(srna, "use_occlude", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_XRAY);
  RNA_def_property_ui_text(
      prop, "Occlude", "Occlude\nOnly paint onto the faces directly under the brush (slower)");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_backface_culling", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_BACKFACE);
  RNA_def_property_ui_text(prop, "Cull", "Cull\nIgnore faces pointing away from the view (faster)");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_normal_falloff", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_FLAT);
  RNA_def_property_ui_text(prop, "Normal", "Normal\nPaint most on faces pointing towards the view");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_stencil_layer", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_STENCIL);
  RNA_def_property_ui_text(prop, "Stencil Layer", "Stencil Layer\nSet the mask layer from the UV map buttons");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_viewport_update");

  prop = RNA_def_property(srna, "invert_stencil", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_STENCIL_INV);
  RNA_def_property_ui_text(prop, "Invert", "Invert\nInvert the stencil layer");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_viewport_update");

  prop = RNA_def_property(srna, "stencil_image", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, NULL, "stencil");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_CONTEXT_UPDATE);
  RNA_def_property_ui_text(prop, "Stencil Image", "Stencil Image\nImage used as stencil");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_stencil_update");

  prop = RNA_def_property(srna, "canvas", PROP_POINTER, PROP_NONE);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_CONTEXT_UPDATE);
  RNA_def_property_ui_text(prop, "Canvas", "Canvas\nImage used as canvas");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_canvas_update");

  prop = RNA_def_property(srna, "clone_image", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, NULL, "clone");
  RNA_def_property_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop, "Clone Image", "Clone Image\nImage used as clone source");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "stencil_color", PROP_FLOAT, PROP_COLOR_GAMMA);
  RNA_def_property_range(prop, 0.0, 1.0);
  RNA_def_property_float_sdna(prop, NULL, "stencil_col");
  RNA_def_property_ui_text(prop, "Stencil Color", "Stencil Color\nStencil color in the viewport");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_viewport_update");

  prop = RNA_def_property(srna, "dither", PROP_FLOAT, PROP_NONE);
  RNA_def_property_range(prop, 0.0, 2.0);
  RNA_def_property_ui_text(prop, "Dither", "Dither\nAmount of dithering when painting on byte images");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_clone_layer", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", IMAGEPAINT_PROJECT_LAYER_CLONE);
  RNA_def_property_ui_text(
      prop,
      "Clone Map",
      "Clone Map\nUse another UV map as clone source, otherwise use the 3D cursor as the source");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_viewport_update");

  /* integers */

  prop = RNA_def_property(srna, "seam_bleed", PROP_INT, PROP_PIXEL);
  RNA_def_property_ui_range(prop, 0, 8, 0, -1);
  RNA_def_property_ui_text(
      prop, "Bleed", "Bleed\nExtend paint beyond the faces UVs to reduce seams (in pixels, slower)");

  prop = RNA_def_property(srna, "normal_angle", PROP_INT, PROP_UNSIGNED);
  RNA_def_property_range(prop, 0, 90);
  RNA_def_property_ui_text(
      prop, "Angle", "Angle\nPaint most on faces pointing towards the view according to this angle");

  prop = RNA_def_int_array(srna,
                           "screen_grab_size",
                           2,
                           NULL,
                           0,
                           0,
                           "screen_grab_size",
                           "Size to capture the image for re-projecting",
                           0,
                           0);
  RNA_def_property_range(prop, 512, 16384);

  prop = RNA_def_property(srna, "mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_enum_items(prop, paint_type_items);
  RNA_def_property_ui_text(prop, "Mode", "Mode\nMode of operation for projection painting");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_mode_update");

  prop = RNA_def_property(srna, "interpolation", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "interp");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_enum_items(prop, paint_interp_items);
  RNA_def_property_ui_text(prop, "Interpolation", "Interpolation\nTexture filtering type");
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_mode_update");

  /* Missing data */
  prop = RNA_def_property(srna, "missing_uvs", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "missing_data", IMAGEPAINT_MISSING_UVS);
  RNA_def_property_ui_text(prop, "Missing UVs", "Missing UVs\nA UV layer is missing on the mesh");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "missing_materials", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "missing_data", IMAGEPAINT_MISSING_MATERIAL);
  RNA_def_property_ui_text(prop, "Missing Materials", "Missing Materials\nThe mesh is missing materials");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "missing_stencil", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "missing_data", IMAGEPAINT_MISSING_STENCIL);
  RNA_def_property_ui_text(prop, "Missing Stencil", "Missing Stencil\nImage Painting does not have a stencil");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);

  prop = RNA_def_property(srna, "missing_texture", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "missing_data", IMAGEPAINT_MISSING_TEX);
  RNA_def_property_ui_text(
      prop, "Missing Texture", "Missing Texture\nImage Painting does not have a texture to paint on");
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
}

static void rna_def_particle_edit(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  static const EnumPropertyItem select_mode_items[] = {
      {SCE_SELECT_PATH, "PATH", ICON_PARTICLE_PATH, "Path", "Path edit mode"},
      {SCE_SELECT_POINT, "POINT", ICON_PARTICLE_POINT, "Point", "Point select mode"},
      {SCE_SELECT_END, "TIP", ICON_PARTICLE_TIP, "Tip", "Tip select mode"},
      {0, NULL, 0, NULL, NULL},
  };

  static const EnumPropertyItem puff_mode[] = {
      {0, "ADD", 0, "Add", "Make hairs more puffy"},
      {1, "SUB", 0, "Sub", "Make hairs less puffy"},
      {0, NULL, 0, NULL, NULL},
  };

  static const EnumPropertyItem length_mode[] = {
      {0, "GROW", 0, "Grow", "Make hairs longer"},
      {1, "SHRINK", 0, "Shrink", "Make hairs shorter"},
      {0, NULL, 0, NULL, NULL},
  };

  static const EnumPropertyItem edit_type_items[] = {
      {PE_TYPE_PARTICLES, "PARTICLES", 0, "Particles", ""},
      {PE_TYPE_SOFTBODY, "SOFT_BODY", 0, "Soft body", ""},
      {PE_TYPE_CLOTH, "CLOTH", 0, "Cloth", ""},
      {0, NULL, 0, NULL, NULL},
  };

  /* edit */

  srna = RNA_def_struct(brna, "ParticleEdit", NULL);
  RNA_def_struct_sdna(srna, "ParticleEditSettings");
  RNA_def_struct_path_func(srna, "rna_ParticleEdit_path");
  RNA_def_struct_ui_text(srna, "Particle Edit", "Properties of particle editing mode");

  prop = RNA_def_property(srna, "tool", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "brushtype");
  RNA_def_property_enum_items(prop, rna_enum_particle_edit_hair_brush_items);
  RNA_def_property_enum_funcs(
      prop, NULL, "rna_ParticleEdit_tool_set", "rna_ParticleEdit_tool_itemf");
  RNA_def_property_ui_text(prop, "Tool", "");

  prop = RNA_def_property(srna, "select_mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_bitflag_sdna(prop, NULL, "selectmode");
  RNA_def_property_enum_items(prop, select_mode_items);
  RNA_def_property_ui_text(prop, "Selection Mode", "Selection Mode\nParticle select and display mode");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_update");

  prop = RNA_def_property(srna, "use_preserve_length", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_KEEP_LENGTHS);
  RNA_def_property_ui_text(prop, "Keep Lengths", "Keep Lengths\nKeep path lengths constant");

  prop = RNA_def_property(srna, "use_preserve_root", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_LOCK_FIRST);
  RNA_def_property_ui_text(prop, "Keep Root", "Keep Root\nKeep root keys unmodified");

  prop = RNA_def_property(srna, "use_emitter_deflect", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_DEFLECT_EMITTER);
  RNA_def_property_ui_text(prop, "Deflect Emitter", "Deflect Emitter\nKeep paths from intersecting the emitter");

  prop = RNA_def_property(srna, "emitter_distance", PROP_FLOAT, PROP_DISTANCE);
  RNA_def_property_float_sdna(prop, NULL, "emitterdist");
  RNA_def_property_ui_range(prop, 0.0f, 10.0f, 10, 3);
  RNA_def_property_ui_text(
      prop, "Emitter Distance", "Emitter Distance\nDistance to keep particles away from the emitter");

  prop = RNA_def_property(srna, "use_fade_time", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_FADE_TIME);
  RNA_def_property_ui_text(
      prop, "Fade Time", "Fade Time\nFade paths and keys further away from current frame");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_update");

  prop = RNA_def_property(srna, "use_auto_velocity", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_AUTO_VELOCITY);
  RNA_def_property_ui_text(prop, "Auto Velocity", "Auto Velocity\nCalculate point velocities automatically");

  prop = RNA_def_property(srna, "show_particles", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_DRAW_PART);
  RNA_def_property_ui_text(prop, "Display Particles", "Display Particles\nDisplay actual particles");
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_redo");

  prop = RNA_def_property(srna, "use_default_interpolate", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_INTERPOLATE_ADDED);
  RNA_def_property_ui_text(
      prop, "Interpolate", "Interpolate\nInterpolate new particles from the existing ones");

  prop = RNA_def_property(srna, "default_key_count", PROP_INT, PROP_NONE);
  RNA_def_property_int_sdna(prop, NULL, "totaddkey");
  RNA_def_property_range(prop, 2, SHRT_MAX);
  RNA_def_property_ui_range(prop, 2, 20, 10, 3);
  RNA_def_property_ui_text(prop, "Keys", "Keys\nHow many keys to make new particles with");

  prop = RNA_def_property(srna, "brush", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "ParticleBrush");
  RNA_def_property_pointer_funcs(prop, "rna_ParticleEdit_brush_get", NULL, NULL, NULL);
  RNA_def_property_ui_text(prop, "Brush", "");

  prop = RNA_def_property(srna, "display_step", PROP_INT, PROP_NONE);
  RNA_def_property_int_sdna(prop, NULL, "draw_step");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_range(prop, 1, 10);
  RNA_def_property_ui_text(prop, "Steps", "Steps\nHow many steps to display the path with");
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_redo");

  prop = RNA_def_property(srna, "fade_frames", PROP_INT, PROP_NONE);
  RNA_def_property_range(prop, 1, 100);
  RNA_def_property_ui_text(prop, "Frames", "Frames\nHow many frames to fade");
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_update");

  prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
  RNA_def_property_flag(prop, PROP_CONTEXT_UPDATE);
  RNA_def_property_enum_sdna(prop, NULL, "edittype");
  RNA_def_property_enum_items(prop, edit_type_items);
  RNA_def_property_ui_text(prop, "Type", "");
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_redo");

  prop = RNA_def_property(srna, "is_editable", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_ParticleEdit_editable_get", NULL);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop, "Editable", "Editable\nA valid edit mode exists");

  prop = RNA_def_property(srna, "is_hair", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_funcs(prop, "rna_ParticleEdit_hair_get", NULL);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop, "Hair", "Hair\nEditing hair");

  prop = RNA_def_property(srna, "object", PROP_POINTER, PROP_NONE);
  RNA_def_property_clear_flag(prop, PROP_EDITABLE);
  RNA_def_property_ui_text(prop, "Object", "Object\nThe edited object");

  prop = RNA_def_property(srna, "shape_object", PROP_POINTER, PROP_NONE);
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_CONTEXT_UPDATE);
  RNA_def_property_ui_text(prop, "Shape Object", "Shape Object\nOuter shape to use for tools");
  RNA_def_property_pointer_funcs(prop, NULL, NULL, NULL, "rna_Mesh_object_poll");
  RNA_def_property_update(prop, NC_OBJECT | ND_DRAW, "rna_ParticleEdit_redo");

  /* brush */

  srna = RNA_def_struct(brna, "ParticleBrush", NULL);
  RNA_def_struct_sdna(srna, "ParticleBrushData");
  RNA_def_struct_path_func(srna, "rna_ParticleBrush_path");
  RNA_def_struct_ui_text(srna, "Particle Brush", "Particle editing brush");

  prop = RNA_def_property(srna, "size", PROP_INT, PROP_PIXEL);
  RNA_def_property_range(prop, 1, SHRT_MAX);
  RNA_def_property_ui_range(prop, 1, MAX_BRUSH_PIXEL_RADIUS, 10, 3);
  RNA_def_property_ui_text(prop, "Radius", "Radius\nRadius of the brush in pixels");

  prop = RNA_def_property(srna, "strength", PROP_FLOAT, PROP_FACTOR);
  RNA_def_property_range(prop, 0.001, 1.0);
  RNA_def_property_ui_text(prop, "Strength", "Strength\nBrush strength");

  prop = RNA_def_property(srna, "count", PROP_INT, PROP_NONE);
  RNA_def_property_range(prop, 1, 1000);
  RNA_def_property_ui_range(prop, 1, 100, 10, 3);
  RNA_def_property_ui_text(prop, "Count", "Count\nParticle count");

  prop = RNA_def_property(srna, "steps", PROP_INT, PROP_NONE);
  RNA_def_property_int_sdna(prop, NULL, "step");
  RNA_def_property_range(prop, 1, SHRT_MAX);
  RNA_def_property_ui_range(prop, 1, 50, 10, 3);
  RNA_def_property_ui_text(prop, "Steps", "Steps\nBrush steps");

  prop = RNA_def_property(srna, "puff_mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "invert");
  RNA_def_property_enum_items(prop, puff_mode);
  RNA_def_property_ui_text(prop, "Puff Mode", "");

  prop = RNA_def_property(srna, "use_puff_volume", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", PE_BRUSH_DATA_PUFF_VOLUME);
  RNA_def_property_ui_text(
      prop,
      "Puff Volume",
      "Puff Volume\nApply puff to unselected end-points (helps maintain hair volume when puffing root)");

  prop = RNA_def_property(srna, "length_mode", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "invert");
  RNA_def_property_enum_items(prop, length_mode);
  RNA_def_property_ui_text(prop, "Length Mode", "");

  /* dummy */
  prop = RNA_def_property(srna, "curve", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "CurveMapping");
  RNA_def_property_pointer_funcs(prop, "rna_ParticleBrush_curve_get", NULL, NULL, NULL);
  RNA_def_property_ui_text(prop, "Curve", "");
}

/* srna -- gpencil speed guides */
static void rna_def_gpencil_guides(BlenderRNA *brna)
{
  StructRNA *srna;
  PropertyRNA *prop;

  srna = RNA_def_struct(brna, "GPencilSculptGuide", NULL);
  RNA_def_struct_sdna(srna, "GP_Sculpt_Guide");
  RNA_def_struct_path_func(srna, "rna_GPencilSculptGuide_path");
  RNA_def_struct_ui_text(srna, "GPencil Sculpt Guide", "Guides for drawing");

  static const EnumPropertyItem prop_gpencil_guidetypes[] = {
      {GP_GUIDE_CIRCULAR, "CIRCULAR", 0, "Circular", "Use single point to create rings"},
      {GP_GUIDE_RADIAL, "RADIAL", 0, "Radial", "Use single point as direction"},
      {GP_GUIDE_PARALLEL, "PARALLEL", 0, "Parallel", "Parallel lines"},
      {GP_GUIDE_GRID, "GRID", 0, "Grid", "Grid allows horizontal and vertical lines"},
      {0, NULL, 0, NULL, NULL},
  };

  static const EnumPropertyItem prop_gpencil_guide_references[] = {
      {GP_GUIDE_REF_CURSOR, "CURSOR", 0, "Cursor", "Use cursor as reference point"},
      {GP_GUIDE_REF_CUSTOM, "CUSTOM", 0, "Custom", "Use custom reference point"},
      {GP_GUIDE_REF_OBJECT, "OBJECT", 0, "Object", "Use object as reference point"},
      {0, NULL, 0, NULL, NULL},
  };

  prop = RNA_def_property(srna, "use_guide", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "use_guide", false);
  RNA_def_property_boolean_default(prop, false);
  RNA_def_property_ui_text(prop, "Use Guides", "Use Guides\nEnable speed guides");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_snapping", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "use_snapping", false);
  RNA_def_property_boolean_default(prop, false);
  RNA_def_property_ui_text(
      prop, "Use Snapping", "Use Snapping\nEnable snapping to guides angle or spacing options");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "reference_object", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, NULL, "reference_object");
  RNA_def_property_ui_text(prop, "Object", "Object\nObject used for reference point");
  RNA_def_property_flag(prop, PROP_EDITABLE | PROP_ID_SELF_CHECK);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_viewport_update");

  prop = RNA_def_property(srna, "reference_point", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "reference_point");
  RNA_def_property_enum_items(prop, prop_gpencil_guide_references);
  RNA_def_property_ui_text(prop, "Type", "Type\nType of speed guide");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_viewport_update");

  prop = RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "type");
  RNA_def_property_enum_items(prop, prop_gpencil_guidetypes);
  RNA_def_property_ui_text(prop, "Type", "Type\nType of speed guide");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "angle", PROP_FLOAT, PROP_ANGLE);
  RNA_def_property_float_sdna(prop, NULL, "angle");
  RNA_def_property_range(prop, -(M_PI * 2.0f), (M_PI * 2.0f));
  RNA_def_property_ui_text(prop, "Angle", "Angle\nDirection of lines");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "angle_snap", PROP_FLOAT, PROP_ANGLE);
  RNA_def_property_float_sdna(prop, NULL, "angle_snap");
  RNA_def_property_range(prop, -(M_PI * 2.0f), (M_PI * 2.0f));
  RNA_def_property_ui_text(prop, "Angle Snap", "Angle Snap\nAngle snapping");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "spacing", PROP_FLOAT, PROP_DISTANCE);
  RNA_def_property_float_sdna(prop, NULL, "spacing");
  RNA_def_property_float_default(prop, 0.01f);
  RNA_def_property_range(prop, 0.0f, FLT_MAX);
  RNA_def_property_ui_range(prop, 0.0f, FLT_MAX, 1, 3);
  RNA_def_property_ui_text(prop, "Spacing", "Spacing\nGuide spacing");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "location", PROP_FLOAT, PROP_DISTANCE);
  RNA_def_property_float_sdna(prop, NULL, "location");
  RNA_def_property_array(prop, 3);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_ui_text(prop, "Location", "Location\nCustom reference point for guides");
  RNA_def_property_range(prop, -FLT_MAX, FLT_MAX);
  RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 3);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_ImaPaint_viewport_update");
}

static void rna_def_gpencil_sculpt(BlenderRNA *brna)
{
  static const EnumPropertyItem prop_direction_items[] = {
      {0, "ADD", ICON_ADD, "Add", "Add effect of brush"},
      {GP_SCULPT_FLAG_INVERT, "SUBTRACT", ICON_REMOVE, "Subtract", "Subtract effect of brush"},
      {0, NULL, 0, NULL, NULL},
  };

  StructRNA *srna;
  PropertyRNA *prop;

  /* == Settings == */
  srna = RNA_def_struct(brna, "GPencilSculptSettings", NULL);
  RNA_def_struct_sdna(srna, "GP_Sculpt_Settings");
  RNA_def_struct_path_func(srna, "rna_GPencilSculptSettings_path");
  RNA_def_struct_ui_text(
      srna, "GPencil Sculpt Settings", "Properties for Grease Pencil stroke sculpting tool");

  prop = RNA_def_property(srna, "sculpt_tool", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "brushtype");
  RNA_def_property_enum_items(prop, rna_enum_gpencil_sculpt_brush_items);
  RNA_def_property_ui_text(prop, "Tool", "");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_GPencil_update");

  prop = RNA_def_property(srna, "weight_tool", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "weighttype");
  RNA_def_property_enum_items(prop, rna_enum_gpencil_weight_brush_items);
  RNA_def_property_ui_text(prop, "Tool", "Tool\nTool for weight painting");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, "rna_GPencil_update");

  prop = RNA_def_property(srna, "brush", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "GPencilSculptBrush");
  RNA_def_property_pointer_funcs(prop, "rna_GPencilSculptSettings_brush_get", NULL, NULL, NULL);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_ui_text(prop, "Brush", "");

  prop = RNA_def_property(srna, "guide", PROP_POINTER, PROP_NONE);
  RNA_def_property_struct_type(prop, "GPencilSculptGuide");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_ui_text(prop, "Guide", "");

  prop = RNA_def_property(srna, "use_select_mask", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_SETT_FLAG_SELECT_MASK);
  RNA_def_property_ui_text(prop, "Selection Mask", "Selection Mask\nOnly sculpt selected stroke points");
  RNA_def_property_ui_icon(prop, ICON_GP_ONLY_SELECTED, 0);
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_edit_position", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_SETT_FLAG_APPLY_POSITION);
  RNA_def_property_ui_text(prop, "Affect Position", "Affect Position\nThe brush affects the position of the point");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_edit_strength", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_SETT_FLAG_APPLY_STRENGTH);
  RNA_def_property_ui_text(
      prop, "Affect Strength", "Affect Strength\nThe brush affects the color strength of the point");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_edit_thickness", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_SETT_FLAG_APPLY_THICKNESS);
  RNA_def_property_ui_text(
      prop, "Affect Thickness", "Affect Thickness\nThe brush affects the thickness of the point");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_edit_uv", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_SETT_FLAG_APPLY_UV);
  RNA_def_property_ui_text(prop, "Affect UV", "Affect UV\nThe brush affects the UV rotation of the point");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_multiframe_falloff", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_SETT_FLAG_FRAME_FALLOFF);
  RNA_def_property_ui_text(
      prop,
      "Use Falloff",
      "Use Falloff\nUse falloff effect when edit in multiframe mode to compute brush effect by frame");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_thickness_curve", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_SETT_FLAG_PRIMITIVE_CURVE);
  RNA_def_property_ui_text(prop, "Use Curve", "Use Curve\nUse curve to define primitive stroke thickness");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  /* custom falloff curve */
  prop = RNA_def_property(srna, "multiframe_falloff_curve", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, NULL, "cur_falloff");
  RNA_def_property_struct_type(prop, "CurveMapping");
  RNA_def_property_ui_text(
      prop, "Curve", "Curve\nCustom curve to control falloff of brush effect by Grease Pencil frames");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  /* custom primitive curve */
  prop = RNA_def_property(srna, "thickness_primitive_curve", PROP_POINTER, PROP_NONE);
  RNA_def_property_pointer_sdna(prop, NULL, "cur_primitive");
  RNA_def_property_struct_type(prop, "CurveMapping");
  RNA_def_property_ui_text(prop, "Curve", "Curve\nCustom curve to control primitive thickness");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  /* lock axis */
  prop = RNA_def_property(srna, "lock_axis", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_sdna(prop, NULL, "lock_axis");
  RNA_def_property_enum_items(prop, rna_enum_gpencil_lock_axis_items);
  RNA_def_property_ui_text(prop, "Lock Axis", "");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_GPENCIL | ND_DATA, "rna_GPencil_update");

  /* threshold for cutter */
  prop = RNA_def_property(srna, "intersection_threshold", PROP_FLOAT, PROP_NONE);
  RNA_def_property_float_sdna(prop, NULL, "isect_threshold");
  RNA_def_property_range(prop, 0.0f, 10.0f);
  RNA_def_property_float_default(prop, 0.1f);
  RNA_def_property_ui_text(prop, "Threshold", "Threshold\nThreshold for stroke intersections");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);

  /* brush */
  srna = RNA_def_struct(brna, "GPencilSculptBrush", NULL);
  RNA_def_struct_sdna(srna, "GP_Sculpt_Data");
  RNA_def_struct_path_func(srna, "rna_GPencilSculptBrush_path");
  RNA_def_struct_ui_text(srna, "GPencil Sculpt Brush", "Stroke editing brush");

  prop = RNA_def_property(srna, "size", PROP_INT, PROP_PIXEL);
  RNA_def_property_range(prop, 1, GP_MAX_BRUSH_PIXEL_RADIUS);
  RNA_def_property_ui_range(prop, 1, 500, 10, 3);
  RNA_def_property_ui_text(prop, "Radius", "Radius\nRadius of the brush in pixels");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "strength", PROP_FLOAT, PROP_FACTOR);
  RNA_def_property_range(prop, 0.001, 1.0);
  RNA_def_property_ui_text(prop, "Strength", "Strength\nBrush strength");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "weight", PROP_FLOAT, PROP_FACTOR);
  RNA_def_property_range(prop, 0.0, 1.0);
  RNA_def_property_ui_text(prop, "Weight", "Weight\nTarget weight");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_pressure_strength", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_FLAG_USE_PRESSURE);
  RNA_def_property_ui_icon(prop, ICON_STYLUS_PRESSURE, 0);
  RNA_def_property_ui_text(
      prop, "Strength Pressure", "Strength Pressure\nEnable tablet pressure sensitivity for strength");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_pressure_radius", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_FLAG_PRESSURE_RADIUS);
  RNA_def_property_ui_icon(prop, ICON_STYLUS_PRESSURE, 0);
  RNA_def_property_ui_text(
      prop, "Radius Pressure", "Radius Pressure\nEnable tablet pressure sensitivity for radius");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_falloff", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_FLAG_USE_FALLOFF);
  RNA_def_property_ui_text(
      prop, "Use Falloff", "Use Falloff\nStrength of brush decays with distance from cursor");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "use_edit_pressure", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_FLAG_SMOOTH_PRESSURE);
  RNA_def_property_ui_text(
      prop, "Affect Pressure", "Affect Pressure\nAffect pressure values as well when smoothing strokes");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  prop = RNA_def_property(srna, "direction", PROP_ENUM, PROP_NONE);
  RNA_def_property_enum_bitflag_sdna(prop, NULL, "flag");
  RNA_def_property_enum_items(prop, prop_direction_items);
  RNA_def_property_ui_text(prop, "Direction", "");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
  RNA_def_property_update(prop, NC_SCENE | ND_TOOLSETTINGS, NULL);

  /* Cursor Color */
  static float default_1[3] = {1.0f, 0.6f, 0.6f};
  static float default_2[3] = {0.6f, 0.6f, 1.0f};

  prop = RNA_def_property(srna, "cursor_color_add", PROP_FLOAT, PROP_COLOR_GAMMA);
  RNA_def_property_float_sdna(prop, NULL, "curcolor_add");
  RNA_def_property_array(prop, 3);
  RNA_def_property_range(prop, 0.0f, 1.0f);
  RNA_def_property_float_array_default(prop, default_1);
  RNA_def_property_ui_text(prop, "Cursor Add", "Cursor Add\nColor for the cursor for addition");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);

  prop = RNA_def_property(srna, "cursor_color_sub", PROP_FLOAT, PROP_COLOR_GAMMA);
  RNA_def_property_float_sdna(prop, NULL, "curcolor_sub");
  RNA_def_property_array(prop, 3);
  RNA_def_property_range(prop, 0.0f, 1.0f);
  RNA_def_property_float_array_default(prop, default_2);
  RNA_def_property_ui_text(prop, "Cursor Sub", "Cursor Sub\nColor for the cursor for subtraction");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);

  prop = RNA_def_property(srna, "use_cursor", PROP_BOOLEAN, PROP_NONE);
  RNA_def_property_boolean_sdna(prop, NULL, "flag", GP_SCULPT_FLAG_ENABLE_CURSOR);
  RNA_def_property_boolean_default(prop, true);
  RNA_def_property_ui_text(prop, "Enable Cursor", "Show Brush\nShow Brush cursor on screen");
  RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
}

void RNA_def_sculpt_paint(BlenderRNA *brna)
{
  /* *** Non-Animated *** */
  RNA_define_animate_sdna(false);
  rna_def_paint_curve(brna);
  rna_def_paint_tool_slot(brna);
  rna_def_paint(brna);
  rna_def_sculpt(brna);
  rna_def_uv_sculpt(brna);
  rna_def_gp_paint(brna);
  rna_def_vertex_paint(brna);
  rna_def_image_paint(brna);
  rna_def_particle_edit(brna);
  rna_def_gpencil_guides(brna);
  rna_def_gpencil_sculpt(brna);
  RNA_define_animate_sdna(true);
}

#endif
