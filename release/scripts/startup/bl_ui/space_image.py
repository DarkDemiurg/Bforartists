# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
import bpy
from bpy.types import (
    Header,
    Menu,
    Panel,
    UIList,
)
from .properties_paint_common import (
    UnifiedPaintPanel,
    brush_texture_settings,
    brush_texpaint_common,
    brush_texpaint_common_color,
    brush_texpaint_common_gradient,
    brush_texpaint_common_clone,
    brush_texpaint_common_options,
    brush_mask_texture_settings,
)
from .properties_grease_pencil_common import (
    AnnotationDataPanel,
)
from .space_toolsystem_common import (
    ToolActivePanelHelper,
)

from bpy.app.translations import pgettext_iface as iface_


class ImagePaintPanel(UnifiedPaintPanel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'


class BrushButtonsPanel(UnifiedPaintPanel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'

    @classmethod
    def poll(cls, context):
        tool_settings = context.tool_settings.image_paint
        return tool_settings.brush


class IMAGE_PT_active_tool(ToolActivePanelHelper, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"


# Workaround to separate the tooltips for Toggle Maximize Area
class IMAGE_MT_view_view_fit(bpy.types.Operator):
    """View Fit\nFits the content area into the window"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "image.view_all_fit"        # unique identifier for buttons and menu items to reference.
    bl_label = "View Fit"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.image.view_all(fit_view = True)
        return {'FINISHED'}  


class IMAGE_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        show_uvedit = sima.show_uvedit
        show_render = sima.show_render

        layout.prop(sima, "show_region_toolbar")
        layout.prop(sima, "show_region_ui")
        layout.prop(sima, "show_region_tool_header")
        layout.prop(sima, "show_region_hud")

        layout.separator()

        layout.operator("image.view_zoom_in", icon = "ZOOM_IN")
        layout.operator("image.view_zoom_out", icon = "ZOOM_OUT")
        layout.operator("image.view_zoom_border", icon = "ZOOM_BORDER")

        layout.separator()

        layout.menu("IMAGE_MT_view_zoom")

        layout.separator()

        if show_uvedit:
            layout.operator("image.view_selected", text = "View Selected", icon='VIEW_SELECTED')

        layout.operator("image.view_all", icon = "VIEWALL" )
        layout.operator("image.view_all_fit", text="View Fit", icon = "VIEW_FIT") # bfa - separated tooltip

        layout.separator()

        if show_render:
            layout.operator("image.render_border", icon = "RENDERBORDER")
            layout.operator("image.clear_render_border", icon = "RENDERBORDER_CLEAR")

            layout.separator()

            layout.operator("image.cycle_render_slot", text="Render Slot Cycle Next", icon = "FRAME_NEXT")
            layout.operator("image.cycle_render_slot", text="Render Slot Cycle Previous", icon = "FRAME_PREV").reverse = True

            layout.separator()

        layout.menu("INFO_MT_area")


class IMAGE_MT_view_zoom(Menu):
    bl_label = "Fractional Zoom"

    def draw(self, _context):
        layout = self.layout

        ratios = ((1, 8), (1, 4), (1, 2), (1, 1), (2, 1), (4, 1), (8, 1))

        for i, (a, b) in enumerate(ratios):
            if i in {3, 4}:  # Draw separators around Zoom 1:1.
                layout.separator()

            layout.operator(
                "image.view_zoom_ratio",
                text=iface_(f"Zoom {a:d}:{b:d}"),
                translate=False,
            ).ratio = a / b


# Workaround to separate the tooltips
class IMAGE_MT_select_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "uv.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.uv.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class IMAGE_MT_select_none(bpy.types.Operator):
    """None\nDeselects everything """         # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "uv.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.uv.select_all(action = 'DESELECT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class IMAGE_MT_select_linked_pick_extend(bpy.types.Operator):
    """Linked Pick Extend\nSelect all UV vertices under the mouse with extend method\nHotkey Only tool! """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "uv.select_linked_pick_extend"        # unique identifier for buttons and menu items to reference.
    bl_label = "Linked Pick Extend"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.uv.select_linked_pick(extend = True)
        return {'FINISHED'} 

# Workaround to separate the tooltips
class IMAGE_MT_select_linked_extend(bpy.types.Operator):
    """Linked Extend\nSelect all UV vertices linked to the active keymap extended"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "uv.select_linked_extend"        # unique identifier for buttons and menu items to reference.
    bl_label = "Linked Extend"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.uv.select_linked(extend = True)
        return {'FINISHED'}


class IMAGE_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("uv.select_all", text="All", icon='SELECT_ALL').action = 'SELECT'
        layout.operator("uv.select_all_none", text="None", icon = 'SELECT_NONE') # bfa - separated tooltip
        layout.operator("uv.select_all_inverse", text="Inverse", icon = 'INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("uv.select_box", icon='BORDER_RECT').pinned = False
        layout.operator("uv.select_box", text = "Box Select Pinned", icon='BORDER_RECT').pinned = True
        layout.operator("uv.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()
      
        layout.operator("uv.select_linked", text = "Linked", icon = "LINKED")
        layout.operator("uv.select_linked_extend", text = "Linked Extend", icon = "LINKED") # bfa - separated tooltip
        layout.operator("uv.select_linked_pick", text="Linked Pick", icon = "LINKED").extend = False
        layout.operator("uv.select_linked_pick_extend", text="Linked Pick Extend", icon = "LINKED") # bfa - separated tooltip

        layout.separator()

        layout.operator("uv.select_pinned", text = "Pinned", icon = "PINNED")
        layout.operator("uv.select_split", text = "Split", icon = "SPLIT")

        layout.separator()

        layout.operator("uv.select_more", text="More", icon = "SELECTMORE")
        layout.operator("uv.select_less", text="Less", icon = "SELECTLESS")


class IMAGE_MT_brush(Menu):
    bl_label = "Brush"

    def draw(self, context):
        layout = self.layout

        #radial control button brush size
        myvar = layout.operator("wm.radial_control", text = "Brush Radius", icon = "BRUSHSIZE")
        myvar.data_path_primary = 'tool_settings.image_paint.brush.size'
        myvar.data_path_secondary = 'tool_settings.unified_paint_settings.size'
        myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_size'
        myvar.rotation_path = 'tool_settings.image_paint.brush.mask_texture_slot.angle'
        myvar.color_path = 'tool_settings.image_paint.brush.cursor_color_add'
        myvar.fill_color_path = 'tool_settings.image_paint.brush.color'
        myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
        myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
        myvar.zoom_path = 'space_data.zoom'
        myvar.image_id = 'tool_settings.image_paint.brush'
        myvar.secondary_tex = True

        #radial control button brush strength
        myvar = layout.operator("wm.radial_control", text = "Brush Strength", icon = "BRUSHSTRENGTH")
        myvar.data_path_primary = 'tool_settings.image_paint.brush.strength'
        myvar.data_path_secondary = 'tool_settings.unified_paint_settings.strength'
        myvar.use_secondary = 'tool_settings.unified_paint_settings.use_unified_strength'
        myvar.rotation_path = 'tool_settings.image_paint.brush.mask_texture_slot.angle'
        myvar.color_path = 'tool_settings.image_paint.brush.cursor_color_add'
        myvar.fill_color_path = 'tool_settings.image_paint.brush.color'
        myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
        myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
        myvar.zoom_path = ''
        myvar.image_id = 'tool_settings.image_paint.brush'
        myvar.secondary_tex = True

        #radial control button brush angle
        myvar = layout.operator("wm.radial_control", text = "Texture Brush Angle", icon = "BRUSHANGLE")
        myvar.data_path_primary = 'tool_settings.image_paint.brush.texture_slot.angle'
        myvar.data_path_secondary = ''
        myvar.use_secondary = ''
        myvar.rotation_path = 'tool_settings.image_paint.brush.texture_slot.angle'
        myvar.color_path = 'tool_settings.image_paint.brush.cursor_color_add'
        myvar.fill_color_path = 'tool_settings.image_paint.brush.color'
        myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
        myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
        myvar.zoom_path = ''
        myvar.image_id = 'tool_settings.image_paint.brush'
        myvar.secondary_tex = False

        #radial control button brush angle secondary texture
        myvar = layout.operator("wm.radial_control", text = "Texture Brush Angle", icon = "BRUSHANGLE")
        myvar.data_path_primary = 'tool_settings.image_paint.brush.mask_texture_slot.angle'
        myvar.data_path_secondary = ''
        myvar.use_secondary = ''
        myvar.rotation_path = 'tool_settings.image_paint.brush.mask_texture_slot.angle'
        myvar.color_path = 'tool_settings.image_paint.brush.cursor_color_add'
        myvar.fill_color_path = 'tool_settings.image_paint.brush.color'
        myvar.fill_color_override_path = 'tool_settings.unified_paint_settings.color'
        myvar.fill_color_override_test_path = 'tool_settings.unified_paint_settings.use_unified_color'
        myvar.zoom_path = ''
        myvar.image_id = 'tool_settings.image_paint.brush'
        myvar.secondary_tex = True


class IMAGE_MT_image(Menu):
    bl_label = "Image"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        ima = sima.image
        show_render = sima.show_render

        layout.operator("image.new", text="New", icon='IMAGE_DATA')
        layout.operator("image.open", text="Open...", icon='FILE_FOLDER')

        layout.operator("image.read_viewlayers", icon = "RENDERLAYERS")

        if ima:
            layout.separator()

            if not show_render:
                layout.operator("image.replace", text="Replace", icon='FILE_FOLDER')
                layout.operator("image.reload", text="Reload",icon = "FILE_REFRESH")

            layout.operator("image.external_edit", text="Edit Externally", icon = "EDIT_EXTERNAL")

        layout.separator()

        if ima:
            layout.operator("image.save", icon='FILE_TICK')
            layout.operator("image.save_as", icon='SAVE_AS')
            layout.operator("image.save_as", text="Save a Copy", icon='SAVE_COPY').copy = True

        if ima and ima.source == 'SEQUENCE':
            layout.operator("image.save_sequence", icon='SAVE_All')

        layout.operator("image.save_all_modified", text="Save All Images", icon = "SAVE_ALL")

        if ima:
            layout.separator()

            layout.menu("IMAGE_MT_image_invert")

        if ima and not show_render:
            if ima.packed_file:
                if len(ima.filepath):
                    layout.separator()
                    layout.operator("image.unpack", text="Unpack")
            else:
                layout.separator()
                layout.operator("image.pack", text="Pack")


class IMAGE_MT_image_invert(Menu):
    bl_label = "Invert"

    def draw(self, _context):
        layout = self.layout

        props = layout.operator("image.invert", text="Invert Image Colors", icon='IMAGE_RGB')
        props.invert_r = True
        props.invert_g = True
        props.invert_b = True

        layout.separator()

        layout.operator("image.invert", text="Invert Red Channel", icon='COLOR_RED').invert_r = True
        layout.operator("image.invert", text="Invert Green Channel", icon='COLOR_GREEN').invert_g = True
        layout.operator("image.invert", text="Invert Blue Channel", icon='COLOR_BLUE').invert_b = True
        layout.operator("image.invert", text="Invert Alpha Channel", icon='IMAGE_ALPHA').invert_a = True


class IMAGE_MT_uvs_showhide(Menu):
    bl_label = "Show/Hide Faces"

    def draw(self, _context):
        layout = self.layout

        layout.operator("uv.reveal", icon = "RESTRICT_VIEW_OFF")
        layout.operator("uv.hide", text="Hide Selected", icon = "RESTRICT_VIEW_ON").unselected = False
        layout.operator("uv.hide", text="Hide Unselected", icon = "HIDE_UNSELECTED").unselected = True


class IMAGE_MT_uvs_transform(Menu):
    bl_label = "Transform"

    def draw(self, _context):
        layout = self.layout

        layout.operator("transform.translate", icon ='TRANSFORM_MOVE')
        layout.operator("transform.rotate", icon ='TRANSFORM_ROTATE')
        layout.operator("transform.resize", icon ='TRANSFORM_SCALE')

        layout.separator()

        layout.operator("transform.shear", icon = 'SHEAR')


class IMAGE_MT_uvs_snap(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'EXEC_REGION_WIN'

        layout.operator("uv.snap_selected", text="Selected to Pixels", icon = "SNAP_TO_PIXELS").target = 'PIXELS'
        layout.operator("uv.snap_selected", text="Selected to Cursor", icon = "SELECTIONTOCURSOR").target = 'CURSOR'
        layout.operator("uv.snap_selected", text="Selected to Cursor (Offset)", icon = "SELECTIONTOCURSOROFFSET").target = 'CURSOR_OFFSET'
        layout.operator("uv.snap_selected", text="Selected to Adjacent Unselected", icon = "SNAP_TO_ADJACENT").target = 'ADJACENT_UNSELECTED'

        layout.separator()

        layout.operator("uv.snap_cursor", text="Cursor to Pixels", icon = "CURSOR_TO_PIXELS").target = 'PIXELS'
        layout.operator("uv.snap_cursor", text="Cursor to Selected", icon = "CURSORTOSELECTION").target = 'SELECTED'


class IMAGE_MT_uvs_mirror(Menu):
    bl_label = "Mirror"

    def draw(self, _context):
        layout = self.layout

        layout.operator("mesh.faces_mirror_uv", icon = "COPYMIRRORED")

        layout.separator()

        layout.operator_context = 'EXEC_REGION_WIN'

        layout.operator("transform.mirror", text="X Axis", icon = "MIRROR_X").constraint_axis[0] = True
        layout.operator("transform.mirror", text="Y Axis", icon = "MIRROR_Y").constraint_axis[1] = True


class IMAGE_MT_uvs_weldalign(Menu):
    bl_label = "Weld/Align"

    def draw(self, _context):
        layout = self.layout

        layout.operator("uv.weld", icon='WELD')  # W, 1.
        layout.operator("uv.remove_doubles", icon='REMOVE_DOUBLES')
        layout.operator_enum("uv.align", "axis")  # W, 2/3/4.


# Tooltip and operator for Clear Seam.
class IMAGE_MT_uvs_clear_seam(bpy.types.Operator):
    """Clear Seam\nClears the UV Seam for selected edges"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "uv.clear_seam"        # unique identifier for buttons and menu items to reference.
    bl_label = "Clear seam"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.uv.mark_seam(clear=True)
        return {'FINISHED'}  


class IMAGE_MT_uvs(Menu):
    bl_label = "UV"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        uv = sima.uv_editor

        layout.menu("IMAGE_MT_uvs_transform")
        layout.menu("IMAGE_MT_uvs_mirror")
        layout.menu("IMAGE_MT_uvs_snap")

        layout.separator()

        layout.operator("uv.unwrap", text = "Unwrap ABF", icon='UNWRAP_ABF').method = 'ANGLE_BASED'
        layout.operator("uv.unwrap", text = "Unwrap Conformal", icon='UNWRAP_LSCM').method = 'CONFORMAL'
        layout.operator("uv.follow_active_quads", icon = "FOLLOWQUADS")
        layout.operator("uv.pin", text="Unpin", icon = "UNPINNED").clear = True
        layout.operator("uv.pin", icon = "PINNED").clear = False

        layout.separator()

        layout.operator("uv.pack_islands", icon ="PACKISLAND")
        layout.operator("uv.average_islands_scale", icon ="AVERAGEISLANDSCALE")
        layout.operator("uv.minimize_stretch", icon = "MINIMIZESTRETCH")
        layout.operator("uv.stitch", icon = "STITCH")

        layout.separator()

        layout.operator("uv.mark_seam", icon ="MARK_SEAM").clear = False
        layout.operator("uv.clear_seam", text="Clear Seam", icon = 'CLEAR_SEAM')
        layout.operator("uv.seams_from_islands", icon ="SEAMSFROMISLAND")

        layout.separator()

        layout.menu("IMAGE_MT_uvs_weldalign")
        layout.menu("IMAGE_MT_uvs_select_mode")

        layout.separator()

        layout.menu("IMAGE_MT_uvs_showhide")


class IMAGE_MT_uvs_select_mode(Menu):
    bl_label = "UV Select Mode"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_REGION_WIN'
        tool_settings = context.tool_settings

        # Do smart things depending on whether uv_select_sync is on.

        if tool_settings.use_uv_select_sync:
            props = layout.operator("wm.context_set_value", text="Vertex", icon='VERTEXSEL')
            props.value = "(True, False, False)"
            props.data_path = "tool_settings.mesh_select_mode"

            props = layout.operator("wm.context_set_value", text="Edge", icon='EDGESEL')
            props.value = "(False, True, False)"
            props.data_path = "tool_settings.mesh_select_mode"

            props = layout.operator("wm.context_set_value", text="Face", icon='FACESEL')
            props.value = "(False, False, True)"
            props.data_path = "tool_settings.mesh_select_mode"

        else:
            props = layout.operator("wm.context_set_string", text="Vertex", icon='UV_VERTEXSEL')
            props.value = 'VERTEX'
            props.data_path = "tool_settings.uv_select_mode"

            props = layout.operator("wm.context_set_string", text="Edge", icon='UV_EDGESEL')
            props.value = 'EDGE'
            props.data_path = "tool_settings.uv_select_mode"

            props = layout.operator("wm.context_set_string", text="Face", icon='UV_FACESEL')
            props.value = 'FACE'
            props.data_path = "tool_settings.uv_select_mode"

            props = layout.operator("wm.context_set_string", text="Island", icon='UV_ISLANDSEL')
            props.value = 'ISLAND'
            props.data_path = "tool_settings.uv_select_mode"


class IMAGE_MT_uvs_context_menu(Menu):
    bl_label = "UV Context Menu"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data

        # UV Edit Mode
        if sima.show_uvedit:
            # Add
            layout.operator("uv.unwrap")
            layout.operator("uv.follow_active_quads")

            layout.separator()

            # Modify
            layout.operator("uv.pin").clear = False
            layout.operator("uv.pin", text="Unpin").clear = True

            layout.separator()

            layout.operator("uv.weld")
            layout.operator("uv.stitch")

            layout.separator()

            layout.operator_enum("uv.align", "axis")  # W, 2/3/4.

            layout.separator()

            layout.operator("transform.mirror", text="Mirror X").constraint_axis[0] = True
            layout.operator("transform.mirror", text="Mirror Y").constraint_axis[1] = True

            layout.separator()

            layout.menu("IMAGE_MT_uvs_snap")


class IMAGE_MT_pivot_pie(Menu):
    bl_label = "Pivot Point"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()

        pie.prop_enum(context.space_data, "pivot_point", value='CENTER')
        pie.prop_enum(context.space_data, "pivot_point", value='CURSOR')
        pie.prop_enum(context.space_data, "pivot_point", value='INDIVIDUAL_ORIGINS')
        pie.prop_enum(context.space_data, "pivot_point", value='MEDIAN')


class IMAGE_MT_uvs_snap_pie(Menu):
    bl_label = "Snap"

    def draw(self, _context):
        layout = self.layout
        pie = layout.menu_pie()

        layout.operator_context = 'EXEC_REGION_WIN'

        pie.operator(
            "uv.snap_selected",
            text="Selected to Pixels",
            icon='RESTRICT_SELECT_OFF',
        ).target = 'PIXELS'
        pie.operator(
            "uv.snap_cursor",
            text="Cursor to Pixels",
            icon='PIVOT_CURSOR',
        ).target = 'PIXELS'
        pie.operator(
            "uv.snap_cursor",
            text="Cursor to Selected",
            icon='PIVOT_CURSOR',
        ).target = 'SELECTED'
        pie.operator(
            "uv.snap_selected",
            text="Selected to Cursor",
            icon='RESTRICT_SELECT_OFF',
        ).target = 'CURSOR'
        pie.operator(
            "uv.snap_selected",
            text="Selected to Cursor (Offset)",
            icon='RESTRICT_SELECT_OFF',
        ).target = 'CURSOR_OFFSET'
        pie.operator(
            "uv.snap_selected",
            text="Selected to Adjacent Unselected",
            icon='RESTRICT_SELECT_OFF',
        ).target = 'ADJACENT_UNSELECTED'


class IMAGE_HT_tool_header(Header):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOL_HEADER'

    def draw(self, context):
        layout = self.layout

        self.draw_tool_settings(context)

        layout.separator_spacer()

        self.draw_mode_settings(context)

    def draw_tool_settings(self, context):
        layout = self.layout

        # Active Tool
        # -----------
        from .space_toolsystem_common import ToolSelectPanelHelper
        tool = ToolSelectPanelHelper.draw_active_tool_header(context, layout)
        tool_mode = context.mode if tool is None else tool.mode

        # Object Mode Options
        # -------------------

        # Example of how tool_settings can be accessed as pop-overs.

        # TODO(campbell): editing options should be after active tool options
        # (obviously separated for from the users POV)
        draw_fn = getattr(_draw_tool_settings_context_mode, tool_mode, None)
        if draw_fn is not None:
            draw_fn(context, layout, tool)

        if tool_mode == 'PAINT':
            if (tool is not None) and tool.has_datablock:
                layout.popover_group(
                    space_type='IMAGE_EDITOR',
                    region_type='UI',
                    context=".paint_common_2d",
                    category="",
                )
        elif tool_mode == 'UV':
            if (tool is not None) and tool.has_datablock:
                layout.popover_group(space_type='IMAGE_EDITOR', region_type='UI', context=".uv_sculpt", category="")

    def draw_mode_settings(self, context):
        layout = self.layout

        # Active Tool
        # -----------
        from .space_toolsystem_common import ToolSelectPanelHelper
        tool = ToolSelectPanelHelper.tool_active_from_context(context)
        tool_mode = context.mode if tool is None else tool.mode

        if tool_mode == 'PAINT':
            layout.popover_group(space_type='IMAGE_EDITOR', region_type='UI', context=".imagepaint_2d", category="")


class _draw_tool_settings_context_mode:
    @staticmethod
    def UV(context, layout, tool):
        if tool and tool.has_datablock:
            if context.mode == 'EDIT_MESH':
                tool_settings = context.tool_settings
                uv_sculpt = tool_settings.uv_sculpt
                brush = uv_sculpt.brush
                if brush:
                    from .properties_paint_common import UnifiedPaintPanel

                    row = layout.row(align=True)
                    UnifiedPaintPanel.prop_unified_size(row, context, brush, "size", slider=True)
                    UnifiedPaintPanel.prop_unified_size(row, context, brush, "use_pressure_size", text="")

                    row = layout.row(align=True)
                    UnifiedPaintPanel.prop_unified_strength(row, context, brush, "strength", slider=True)
                    UnifiedPaintPanel.prop_unified_strength(row, context, brush, "use_pressure_strength", text="")

    @staticmethod
    def PAINT(context, layout, tool):
        if (tool is None) or (not tool.has_datablock):
            return

        paint = context.tool_settings.image_paint
        layout.template_ID_preview(paint, "brush", rows=3, cols=8, hide_buttons=True)

        brush = paint.brush
        if brush is None:
            return

        from .properties_paint_common import (
            UnifiedPaintPanel,
            brush_basic_texpaint_settings,
        )
        capabilities = brush.image_paint_capabilities
        if capabilities.has_color:
            UnifiedPaintPanel.prop_unified_color(layout, context, brush, "color", text="")
        brush_basic_texpaint_settings(layout, context, brush, compact=True)


class IMAGE_HT_header(Header):
    bl_space_type = 'IMAGE_EDITOR'

    @staticmethod
    def draw_xform_template(layout, context):
        sima = context.space_data
        show_uvedit = sima.show_uvedit
        show_maskedit = sima.show_maskedit

        if show_uvedit or show_maskedit:
            layout.prop(sima, "pivot_point", icon_only=True)

        if show_uvedit:
            tool_settings = context.tool_settings

            # Snap.
            row = layout.row(align=True)
            row.prop(tool_settings, "use_snap", text="")
            row.prop(tool_settings, "snap_uv_element", icon_only=True)
            if tool_settings.snap_uv_element != 'INCREMENT':
                row.prop(tool_settings, "snap_target", text="")

            # Proportional Editing
            row = layout.row(align=True)
            row.prop(tool_settings, "use_proportional_edit", icon_only=True)
            sub = row.row(align=True)
            sub.active = tool_settings.use_proportional_edit
            sub.prop(tool_settings, "proportional_edit_falloff", icon_only=True)


    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        ima = sima.image
        iuser = sima.image_user
        tool_settings = context.tool_settings
        uv = sima.uv_editor

        show_render = sima.show_render
        show_uvedit = sima.show_uvedit
        show_maskedit = sima.show_maskedit

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        if sima.mode != 'UV':
            layout.prop(sima, "ui_mode", text="")

        # UV editing.
        if show_uvedit:
            uvedit = sima.uv_editor

            layout.prop(tool_settings, "use_uv_select_sync", text="")

            if tool_settings.use_uv_select_sync:
                layout.template_edit_mode_selection()
            else:
                layout.prop(tool_settings, "uv_select_mode", text="", expand=True)
                layout.prop(uvedit, "sticky_select_mode", icon_only=True)

        MASK_MT_editor_menus.draw_collapsible(context, layout)    

        #layout.separator_spacer()

        layout.template_ID(sima, "image", new="image.new", open="image.open")

        if show_maskedit:
            row = layout.row()
            row.template_ID(sima, "mask", new="mask.new")

        if not show_render:
            layout.prop(sima, "use_image_pin", text="", emboss=False)

        layout.separator_spacer()

        if show_uvedit:
            uvedit = sima.uv_editor

            mesh = context.edit_object.data
            layout.prop_search(mesh.uv_layers, "active", mesh, "uv_layers", text="")

        if ima:
            if ima.is_stereo_3d:
                row = layout.row()
                row.prop(sima, "show_stereo_3d", text="")

            # layers.
            layout.template_image_layers(ima, iuser)

            # draw options.
            row = layout.row()
            row.prop(sima, "display_channels", icon_only=True)

            row = layout.row(align=True)
            if ima.type == 'COMPOSITE':
                row.operator("image.record_composite", icon='REC')
            if ima.type == 'COMPOSITE' and ima.source in {'MOVIE', 'SEQUENCE'}:
                row.operator("image.play_composite", icon='PLAY')

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class MASK_MT_editor_menus(Menu):
    bl_idname = "MASK_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        sima = context.space_data
        ima = sima.image

        show_uvedit = sima.show_uvedit
        show_maskedit = sima.show_maskedit
        show_paint = sima.show_paint

        layout.menu("IMAGE_MT_view")

        if show_uvedit:
            layout.menu("IMAGE_MT_select")
        if show_maskedit:
            layout.menu("MASK_MT_select")
        if show_paint:
            layout.menu("IMAGE_MT_brush")

        if ima and ima.is_dirty:
            layout.menu("IMAGE_MT_image", text="Image*")
        else:
            layout.menu("IMAGE_MT_image", text="Image")

        if show_uvedit:
            layout.menu("IMAGE_MT_uvs")
        if show_maskedit:
            layout.menu("MASK_MT_add")
            layout.menu("MASK_MT_mask")


# -----------------------------------------------------------------------------
# Mask (similar code in space_clip.py, keep in sync)
# note! - panel placement does _not_ fit well with image panels... need to fix.

from .properties_mask_common import (
    MASK_PT_mask,
    MASK_PT_layers,
    MASK_PT_spline,
    MASK_PT_point,
    MASK_PT_display,
)


class IMAGE_PT_mask(MASK_PT_mask, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image"


class IMAGE_PT_mask_layers(MASK_PT_layers, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image"


class IMAGE_PT_mask_display(MASK_PT_display, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image"


class IMAGE_PT_active_mask_spline(MASK_PT_spline, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image"


class IMAGE_PT_active_mask_point(MASK_PT_point, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image"


# --- end mask ---

class IMAGE_PT_image_options(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image"
    bl_label = "Options"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        uv = sima.uv_editor
        tool_settings = context.tool_settings
        paint = tool_settings.image_paint

        show_uvedit = sima.show_uvedit
        show_render = sima.show_render

        if sima.mode == 'UV':

            layout.prop(uv, "lock_bounds")
            layout.prop(uv, "use_live_unwrap")

        layout.prop(sima, "use_realtime_update")
        if show_uvedit:
            layout.prop(tool_settings, "show_uv_local_view")

        layout.prop(uv, "show_metadata")

        if paint.brush and (context.image_paint_object or sima.mode == 'PAINT'):
            layout.prop(uv, "show_texpaint")
            layout.prop(tool_settings, "show_uv_local_view", text="Show Same Material")

class IMAGE_PT_image_options_unified(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_parent_id = "IMAGE_PT_image_options"
    bl_category = "Image"
    bl_label = "Unified Brush"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        settings = tool_settings.image_paint
        brush = settings.brush
        ups = context.tool_settings.unified_paint_settings

        layout.prop(ups, "use_unified_size", text="Unified Size")
        layout.prop(ups, "use_unified_strength", text="Unified Strength")
        layout.prop(ups, "use_unified_color", text="Unified Color")


class IMAGE_PT_image_properties(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image"
    bl_label = "Image"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return (sima.image)

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        iuser = sima.image_user

        layout.template_image(sima, "image", iuser, multiview=True)


class IMAGE_PT_view_display(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Display"
    bl_category = "View"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return (sima and (sima.image or sima.show_uvedit))

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        sima = context.space_data
        ima = sima.image

        show_uvedit = sima.show_uvedit
        show_maskedit = sima.show_maskedit
        uvedit = sima.uv_editor

        col = layout.column()

        if ima:
            col.use_property_split = True
            col.prop(ima, "display_aspect", text="Aspect Ratio")
            col.use_property_split = False
            col.prop(sima, "show_repeat", text="Repeat Image")

        if show_uvedit:
            col.prop(uvedit, "show_pixel_coords", text="Pixel Coordinates")


class IMAGE_PT_view_display_uv_edit_overlays(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Overlays"
    bl_parent_id = 'IMAGE_PT_view_display'
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return (sima and (sima.show_uvedit))

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sima = context.space_data
        uvedit = sima.uv_editor

        col = layout.column()

        col.prop(uvedit, "edge_display_type", text="Display As")
        col.prop(uvedit, "show_edges", text="Edges")
        col.prop(uvedit, "show_faces", text="Faces")

        col = layout.column()
        col.prop(uvedit, "show_smooth_edges", text="Smooth")
        col.prop(uvedit, "show_modified_edges", text="Modified")


class IMAGE_PT_view_display_uv_edit_overlays_stretch(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Stretching"
    bl_parent_id = 'IMAGE_PT_view_display_uv_edit_overlays'
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return (sima and (sima.show_uvedit))

    def draw_header(self, context):
        sima = context.space_data
        uvedit = sima.uv_editor
        self.layout.prop(uvedit, "show_stretch", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        sima = context.space_data
        uvedit = sima.uv_editor

        layout.active = uvedit.show_stretch
        layout.prop(uvedit, "display_stretch_type", text="Type")


class IMAGE_UL_render_slots(UIList):
    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname, _index):
        slot = item
        layout.prop(slot, "name", text="", emboss=False)


class IMAGE_PT_render_slots(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Image"
    bl_label = "Render Slots"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        return (sima and sima.image and sima.show_render)

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        ima = sima.image

        row = layout.row()

        col = row.column()
        col.template_list(
            "IMAGE_UL_render_slots", "render_slots", ima,
            "render_slots", ima.render_slots, "active_index", rows=3
        )

        col = row.column(align=True)
        col.operator("image.add_render_slot", icon='ADD', text="")
        col.operator("image.remove_render_slot", icon='REMOVE', text="")

        col.separator()

        col.operator("image.clear_render_slot", icon='X', text="")


class IMAGE_PT_paint(Panel, ImagePaintPanel):
    bl_label = "Brush"
    bl_context = ".paint_common_2d"
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.tool_settings.image_paint
        brush = settings.brush

        col = layout.column()
        col.template_ID_preview(settings, "brush", new="brush.add", rows=2, cols=6)

        if brush:
            brush_texpaint_common(self, context, layout, brush, settings)


class IMAGE_PT_paint_color(Panel, ImagePaintPanel):
    bl_category = "Tool"
    bl_context = ".paint_common_2d"
    bl_parent_id = "IMAGE_PT_paint"
    bl_label = "Color Picker"

    @classmethod
    def poll(cls, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush
        capabilities = brush.image_paint_capabilities

        return capabilities.has_color

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings.image_paint
        brush = settings.brush

        layout.active = not brush.use_gradient

        brush_texpaint_common_color(self, context, layout, brush, settings, True)


class IMAGE_PT_paint_swatches(Panel, ImagePaintPanel):
    bl_category = "Tool"
    bl_context = ".paint_common_2d"
    bl_parent_id = "IMAGE_PT_paint"
    bl_label = "Color Palette"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush
        capabilities = brush.image_paint_capabilities

        return capabilities.has_color

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings.image_paint

        layout.template_ID(settings, "palette", new="palette.new")
        if settings.palette:
            layout.template_palette(settings, "palette", color=True)


class IMAGE_PT_paint_gradient(Panel, ImagePaintPanel):
    bl_category = "Tool"
    bl_context = ".paint_common_2d"
    bl_parent_id = "IMAGE_PT_paint"
    bl_label = "Gradient"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush
        capabilities = brush.image_paint_capabilities

        return capabilities.has_color

    def draw_header(self, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush
        self.layout.prop(brush, "use_gradient", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False  # No animation.
        settings = context.tool_settings.image_paint
        brush = settings.brush

        layout.active = brush.use_gradient

        brush_texpaint_common_gradient(self, context, layout, brush, settings, True)


class IMAGE_PT_paint_clone(Panel, ImagePaintPanel):
    bl_category = "Tool"
    bl_context = ".paint_common_2d"
    bl_parent_id = "IMAGE_PT_paint"
    bl_label = "Clone from Image/UV Map"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush

        return brush.image_tool == 'CLONE'

    def draw_header(self, context):
        settings = context.tool_settings.image_paint
        self.layout.prop(settings, "use_clone_layer", text="")

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings.image_paint
        brush = settings.brush

        layout.active = settings.use_clone_layer

        brush_texpaint_common_clone(self, context, layout, brush, settings, True)


class IMAGE_PT_paint_options(Panel, ImagePaintPanel):
    bl_category = "Tool"
    bl_context = ".paint_common_2d"
    bl_parent_id = "IMAGE_PT_paint"
    bl_label = "Options"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush
        capabilities = brush.image_paint_capabilities

        return capabilities.has_color

    def draw(self, context):
        layout = self.layout
        settings = context.tool_settings.image_paint
        brush = settings.brush

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        brush_texpaint_common_options(self, context, layout, brush, settings, True)


class IMAGE_PT_tools_brush_display(BrushButtonsPanel, Panel):
    bl_label = "Display"
    bl_context = ".paint_common_2d"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        tool_settings = context.tool_settings.image_paint
        brush = tool_settings.brush
        tex_slot = brush.texture_slot
        tex_slot_mask = brush.mask_texture_slot

        col = layout.column()

        col.label(text="Curve:")

        row = col.row(align=True)
        row.prop(
            brush,
            "use_cursor_overlay",
            text="",
            toggle=True,
            icon='RESTRICT_VIEW_ON' if brush.use_cursor_overlay else 'RESTRICT_VIEW_OFF',
        )

        sub = row.row(align=True)
        sub.prop(brush, "cursor_overlay_alpha", text="Curve Alpha")
        sub.prop(brush, "use_cursor_overlay_override", toggle=True, text="", icon='BRUSH_DATA')
        row.prop(
            brush, "use_cursor_overlay", text="", toggle=True,
            icon='HIDE_OFF' if brush.use_cursor_overlay else 'HIDE_ON',
        )

        col.active = brush.brush_capabilities.has_overlay
        col.label(text="Texture:")
        row = col.row(align=True)

        sub = row.row(align=True)
        sub.prop(brush, "texture_overlay_alpha", text="Texture Alpha")
        sub.prop(brush, "use_primary_overlay_override", toggle=True, text="", icon='BRUSH_DATA')
        if tex_slot.map_mode != 'STENCIL':
            row.prop(
                brush,
                "use_primary_overlay",
                text="",
                toggle=True,
                icon='RESTRICT_VIEW_ON' if brush.use_primary_overlay else 'RESTRICT_VIEW_OFF',
            )

        sub = row.row(align=True)
        sub.prop(brush, "texture_overlay_alpha", text="Alpha")
        sub.prop(brush, "use_primary_overlay_override", toggle=True, text="", icon='BRUSH_DATA')

        col.label(text="Mask Texture:")

        row = col.row(align=True)

        sub = row.row(align=True)
        sub.prop(brush, "mask_overlay_alpha", text="Mask Texture Alpha")
        sub.prop(brush, "use_secondary_overlay_override", toggle=True, text="", icon='BRUSH_DATA')
        if tex_slot_mask.map_mode != 'STENCIL':
            row.prop(
                brush,
                "use_secondary_overlay",
                text="",
                toggle=True,
                icon='RESTRICT_VIEW_ON' if brush.use_secondary_overlay else 'RESTRICT_VIEW_OFF',
            )


class IMAGE_PT_tools_brush_display_show_brush(BrushButtonsPanel, Panel):
    bl_context = ".paint_common_2d"  # dot on purpose (access from topbar)
    bl_label = "Show Brush"
    bl_parent_id = "IMAGE_PT_tools_brush_display"
    bl_category = "Tool"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        settings = context.tool_settings.image_paint

        self.layout.prop(settings, "show_brush", text="")

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.tool_settings.image_paint
        brush = settings.brush

        col = layout.column()
        col.active = settings.show_brush

        if context.sculpt_object and context.tool_settings.sculpt:
            if brush.sculpt_capabilities.has_secondary_color:
                col.prop(brush, "cursor_color_add", text="Add")
                col.prop(brush, "cursor_color_subtract", text="Subtract")
            else:
                col.prop(brush, "cursor_color_add", text="Color")
        else:
            col.prop(brush, "cursor_color_add", text="Color")


class IMAGE_PT_tools_brush_display_custom_icon(BrushButtonsPanel, Panel):
    bl_context = ".paint_common_2d"  # dot on purpose (access from topbar)
    bl_label = "Custom Icon"
    bl_parent_id = "IMAGE_PT_tools_brush_display"
    bl_category = "Tool"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush

        self.layout.prop(brush, "use_custom_icon", text="")

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.tool_settings.image_paint
        brush = settings.brush

        col = layout.column()
        col.active = brush.use_custom_icon
        col.prop(brush, "icon_filepath", text="")


class IMAGE_PT_tools_brush_texture(BrushButtonsPanel, Panel):
    bl_label = "Texture"
    bl_context = ".paint_common_2d"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings.image_paint
        brush = tool_settings.brush

        col = layout.column()
        col.template_ID_preview(brush, "texture", new="texture.new", rows=3, cols=8)

        brush_texture_settings(col, brush, 0)


class IMAGE_PT_tools_mask_texture(BrushButtonsPanel, Panel):
    bl_label = "Texture Mask"
    bl_context = ".paint_common_2d"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout

        brush = context.tool_settings.image_paint.brush

        col = layout.column()

        col.template_ID_preview(brush, "mask_texture", new="texture.new", rows=3, cols=8)

        brush_mask_texture_settings(col, brush)


class IMAGE_PT_paint_stroke(BrushButtonsPanel, Panel):
    bl_label = "Stroke"
    bl_context = ".paint_common_2d"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings.image_paint
        brush = tool_settings.brush

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()

        col.label(text="Stroke Method:")

        col.prop(brush, "stroke_method", text="")

        if brush.use_anchor:
            col.separator()
            col.prop(brush, "use_edge_to_edge", text="Edge To Edge")

        if brush.use_airbrush:
            col.separator()
            col.prop(brush, "rate", text="Rate", slider=True)

        if brush.use_space:
            col.separator()
            row = col.row(align=True)
            row.prop(brush, "spacing", text="Spacing")
            row.prop(brush, "use_pressure_spacing", toggle=True, text="")

        if brush.use_line or brush.use_curve:
            col.separator()
            row = col.row(align=True)
            row.prop(brush, "spacing", text="Spacing")

        if brush.use_curve:
            col.separator()
            col.template_ID(brush, "paint_curve", new="paintcurve.new")
            col.operator("paintcurve.draw")

        col = layout.column()
        col.separator()

        row = col.row(align=True)
        row.prop(brush, "use_relative_jitter", icon_only=True)
        if brush.use_relative_jitter:
            row.prop(brush, "jitter", slider=True)
        else:
            row.prop(brush, "jitter_absolute")
        row.prop(brush, "use_relative_jitter", icon_only=True)
        row.prop(brush, "use_pressure_jitter", toggle=True, text="")

        col.prop(tool_settings, "input_samples")


class IMAGE_PT_paint_stroke_smooth_stroke(BrushButtonsPanel, Panel):
    bl_context = ".paint_common_2d"  # dot on purpose (access from topbar)
    bl_label = "Smooth Stroke"
    bl_parent_id = "IMAGE_PT_paint_stroke"
    bl_category = "Tool"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush
        if brush.brush_capabilities.has_smooth_stroke:
            return True

    def draw_header(self, context):
        settings = context.tool_settings.image_paint
        brush = settings.brush

        self.layout.prop(brush, "use_smooth_stroke", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.tool_settings.image_paint
        brush = settings.brush

        col = layout.column()
        col.active = brush.use_smooth_stroke
        col.prop(brush, "smooth_stroke_radius", text="Radius", slider=True)
        col.prop(brush, "smooth_stroke_factor", text="Factor", slider=True)


class IMAGE_PT_paint_curve(BrushButtonsPanel, Panel):
    bl_label = "Falloff"
    bl_context = ".paint_common_2d"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tool"

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings.image_paint
        brush = tool_settings.brush

        layout.template_curve_mapping(brush, "curve")

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("brush.curve_preset", icon='SMOOTHCURVE', text="").shape = 'SMOOTH'
        row.operator("brush.curve_preset", icon='SPHERECURVE', text="").shape = 'ROUND'
        row.operator("brush.curve_preset", icon='ROOTCURVE', text="").shape = 'ROOT'
        row.operator("brush.curve_preset", icon='SHARPCURVE', text="").shape = 'SHARP'
        row.operator("brush.curve_preset", icon='LINCURVE', text="").shape = 'LINE'
        row.operator("brush.curve_preset", icon='NOCURVE', text="").shape = 'MAX'


class IMAGE_PT_tools_imagepaint_symmetry(BrushButtonsPanel, Panel):
    bl_category = "Tool"
    bl_context = ".imagepaint_2d"
    bl_label = "Tiling"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        ipaint = tool_settings.image_paint

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(ipaint, "tile_x", text="X", toggle=True)
        row.prop(ipaint, "tile_y", text="Y", toggle=True)


class IMAGE_PT_uv_sculpt_brush(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_context = ".uv_sculpt"  # dot on purpose (access from topbar)
    bl_category = "Tool"
    bl_label = "Brush"

    @classmethod
    def poll(cls, context):
        sima = context.space_data
        # TODO(campbell): nicer way to check if we're in uv sculpt mode.
        if sima and sima.show_uvedit:
            from .space_toolsystem_common import ToolSelectPanelHelper
            tool = ToolSelectPanelHelper.tool_active_from_context(context)
            if tool.has_datablock:
                return True
        return False

    def draw(self, context):
        from .properties_paint_common import UnifiedPaintPanel
        layout = self.layout

        tool_settings = context.tool_settings
        uvsculpt = tool_settings.uv_sculpt

        layout.template_ID(uvsculpt, "brush")

        brush = uvsculpt.brush

        if not self.is_popover:
            if brush:
                col = layout.column()

                row = col.row(align=True)
                UnifiedPaintPanel.prop_unified_size(row, context, brush, "size", slider=True)
                UnifiedPaintPanel.prop_unified_size(row, context, brush, "use_pressure_size", text="")

                row = col.row(align=True)
                UnifiedPaintPanel.prop_unified_strength(row, context, brush, "strength", slider=True)
                UnifiedPaintPanel.prop_unified_strength(row, context, brush, "use_pressure_strength", text="")

        col = layout.column()
        col.prop(tool_settings, "uv_sculpt_lock_borders")
        col.prop(tool_settings, "uv_sculpt_all_islands")

        if brush:
            if brush.uv_sculpt_tool == 'RELAX':
                col.prop(tool_settings, "uv_relax_method")

        col.prop(uvsculpt, "show_brush")


class IMAGE_PT_uv_sculpt_curve(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = ".uv_sculpt"  # dot on purpose (access from topbar)
    bl_category = "Options"
    bl_label = "UV Sculpt Curve"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return (context.uv_sculpt_object is not None)

    def draw(self, context):
        layout = self.layout

        tool_settings = context.tool_settings
        uvsculpt = tool_settings.uv_sculpt
        brush = uvsculpt.brush

        layout.template_curve_mapping(brush, "curve")

        row = layout.row(align=True)
        row.operator("brush.curve_preset", icon='SMOOTHCURVE', text="").shape = 'SMOOTH'
        row.operator("brush.curve_preset", icon='SPHERECURVE', text="").shape = 'ROUND'
        row.operator("brush.curve_preset", icon='ROOTCURVE', text="").shape = 'ROOT'
        row.operator("brush.curve_preset", icon='SHARPCURVE', text="").shape = 'SHARP'
        row.operator("brush.curve_preset", icon='LINCURVE', text="").shape = 'LINE'
        row.operator("brush.curve_preset", icon='NOCURVE', text="").shape = 'MAX'


class IMAGE_PT_uv_sculpt(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = ".uv_sculpt"  # dot on purpose (access from topbar)
    bl_category = "Options"
    bl_label = "UV Sculpt"

    @classmethod
    def poll(cls, context):
        return (context.uv_sculpt_object is not None)

    def draw(self, context):
        from .properties_paint_common import UnifiedPaintPanel
        layout = self.layout

        tool_settings = context.tool_settings
        uvsculpt = tool_settings.uv_sculpt
        brush = uvsculpt.brush

        if not self.is_popover:
            if brush:
                col = layout.column()

                row = col.row(align=True)
                UnifiedPaintPanel.prop_unified_size(row, context, brush, "size", slider=True)
                UnifiedPaintPanel.prop_unified_size(row, context, brush, "use_pressure_size", text="")

                row = col.row(align=True)
                UnifiedPaintPanel.prop_unified_strength(row, context, brush, "strength", slider=True)
                UnifiedPaintPanel.prop_unified_strength(row, context, brush, "use_pressure_strength", text="")

        col = layout.column()
        col.prop(tool_settings, "uv_sculpt_lock_borders")
        col.prop(tool_settings, "uv_sculpt_all_islands")

        col.prop(tool_settings, "uv_sculpt_tool")
        if tool_settings.uv_sculpt_tool == 'RELAX':
            col.prop(tool_settings, "uv_relax_method")

        col.prop(uvsculpt, "show_brush")

class ImageScopesPanel:
    @classmethod
    def poll(cls, context):
        sima = context.space_data

        if not (sima and sima.image):
            return False

        # scopes are not updated in paint modes, hide.
        if sima.mode == 'PAINT':
            return False

        ob = context.active_object
        if ob and ob.mode in {'TEXTURE_PAINT', 'EDIT'}:
            return False

        return True


class IMAGE_PT_view_histogram(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Scopes"
    bl_label = "Histogram"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        hist = sima.scopes.histogram

        layout.template_histogram(sima.scopes, "histogram")

        row = layout.row(align=True)
        row.prop(hist, "mode", expand=True)
        row.prop(hist, "show_line", text="")


class IMAGE_PT_view_waveform(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Scopes"
    bl_label = "Waveform"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data

        layout.template_waveform(sima, "scopes")
        row = layout.split(factor=0.75)
        row.prop(sima.scopes, "waveform_alpha")
        row.prop(sima.scopes, "waveform_mode", text="")


class IMAGE_PT_view_vectorscope(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Scopes"
    bl_label = "Vectorscope"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        layout.template_vectorscope(sima, "scopes")
        layout.prop(sima.scopes, "vectorscope_alpha")


class IMAGE_PT_sample_line(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Scopes"
    bl_label = "Sample Line"

    def draw(self, context):
        layout = self.layout

        sima = context.space_data
        hist = sima.sample_histogram

        layout.operator("image.sample_line")
        layout.template_histogram(sima, "sample_histogram")

        row = layout.row(align=True)
        row.prop(hist, "mode", expand=True)
        row.prop(hist, "show_line", text="")


class IMAGE_PT_scope_sample(ImageScopesPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Scopes"
    bl_label = "Samples"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        sima = context.space_data

        col = flow.column()
        col.prop(sima.scopes, "use_full_resolution")

        col = flow.column()
        col.active = not sima.scopes.use_full_resolution
        col.prop(sima.scopes, "accuracy")


class IMAGE_PT_uv_cursor(Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "2D Cursor"

    @classmethod
    def poll(cls, context):
        sima = context.space_data

        return (sima and (sima.show_uvedit or sima.show_maskedit))

    def draw(self, context):
        layout = self.layout

        sima = context.space_data

        col = layout.column()

        col = layout.column()
        col.prop(sima, "cursor_location", text="Cursor Location")


# Grease Pencil properties
class IMAGE_PT_grease_pencil(AnnotationDataPanel, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"

    # NOTE: this is just a wrapper around the generic GP Panel.

# Grease Pencil drawing tools.


classes = (
    ALL_MT_editormenu,
    IMAGE_MT_view_view_fit,
    IMAGE_MT_view,
    IMAGE_MT_view_zoom,
    IMAGE_MT_select_linked_pick_extend,
    IMAGE_MT_select_linked_extend,
    IMAGE_MT_select_inverse,
    IMAGE_MT_select_none,
    IMAGE_MT_select,
    IMAGE_MT_brush,
    IMAGE_MT_image,
    IMAGE_MT_image_invert,
    IMAGE_MT_uvs_clear_seam,
    IMAGE_MT_uvs,
    IMAGE_MT_uvs_showhide,
    IMAGE_MT_uvs_transform,
    IMAGE_MT_uvs_snap,
    IMAGE_MT_uvs_mirror,
    IMAGE_MT_uvs_weldalign,
    IMAGE_MT_uvs_select_mode,
    IMAGE_MT_uvs_context_menu,
    IMAGE_MT_pivot_pie,
    IMAGE_MT_uvs_snap_pie,
    IMAGE_HT_tool_header,
    IMAGE_HT_header,
    MASK_MT_editor_menus,
    IMAGE_PT_active_tool,
    IMAGE_PT_mask,
    IMAGE_PT_mask_layers,
    IMAGE_PT_mask_display,
    IMAGE_PT_active_mask_spline,
    IMAGE_PT_active_mask_point,
    IMAGE_PT_image_options,
    IMAGE_PT_image_options_unified,
    IMAGE_PT_image_properties,
    IMAGE_UL_render_slots,
    IMAGE_PT_render_slots,
    IMAGE_PT_view_display,
    IMAGE_PT_view_display_uv_edit_overlays,
    IMAGE_PT_view_display_uv_edit_overlays_stretch,
    IMAGE_PT_paint,
    IMAGE_PT_paint_color,
    IMAGE_PT_paint_swatches,
    IMAGE_PT_paint_gradient,
    IMAGE_PT_paint_clone,
    IMAGE_PT_paint_options,
    IMAGE_PT_tools_brush_texture,
    IMAGE_PT_tools_mask_texture,
    IMAGE_PT_paint_stroke,
    IMAGE_PT_paint_stroke_smooth_stroke,
    IMAGE_PT_paint_curve,
    IMAGE_PT_tools_brush_display,
    IMAGE_PT_tools_brush_display_show_brush,
    IMAGE_PT_tools_brush_display_custom_icon,
    IMAGE_PT_tools_imagepaint_symmetry,
    IMAGE_PT_uv_sculpt_brush,
    IMAGE_PT_uv_sculpt_curve,
    IMAGE_PT_view_histogram,
    IMAGE_PT_view_waveform,
    IMAGE_PT_view_vectorscope,
    IMAGE_PT_sample_line,
    IMAGE_PT_scope_sample,
    IMAGE_PT_uv_cursor,
    IMAGE_PT_grease_pencil,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
