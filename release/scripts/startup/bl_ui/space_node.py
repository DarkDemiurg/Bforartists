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
import nodeitems_utils
from bpy.types import Header, Menu, Panel
from bpy.app.translations import pgettext_iface as iface_
from bpy.app.translations import contexts as i18n_contexts
from bl_ui.utils import PresetPanel
from .properties_grease_pencil_common import (
    AnnotationDataPanel,
    GreasePencilToolsPanel,
)
from .space_toolsystem_common import (
    ToolActivePanelHelper,
)
from .properties_material import (
    EEVEE_MATERIAL_PT_settings,
    MATERIAL_PT_viewport
)
from .properties_world import (
    WORLD_PT_viewport_display
)
from .properties_data_light import (
    DATA_PT_light,
    DATA_PT_EEVEE_light,
)


class NODE_HT_header(Header):
    bl_space_type = 'NODE_EDITOR'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        snode = context.space_data
        snode_id = snode.id
        id_from = snode.id_from
        tool_settings = context.tool_settings
        is_compositor = snode.tree_type == 'CompositorNodeTree'

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu

        # Now expanded via the 'ui_type'
        # layout.prop(snode, "tree_type", text="")

        if snode.tree_type == 'ShaderNodeTree':
            layout.prop(snode, "shader_type", text="")

            ob = context.object
            if snode.shader_type == 'OBJECT' and ob:
                ob_type = ob.type

                NODE_MT_editor_menus.draw_collapsible(context, layout)

                types_that_support_material = {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'GPENCIL'}
                # disable material slot buttons when pinned, cannot find correct slot within id_from (#36589)
                # disable also when the selected object does not support materials
                has_material_slots = not snode.pin and ob_type in types_that_support_material

                if ob_type != 'LIGHT':
                    row = layout.row()
                    row.enabled = has_material_slots
                    row.ui_units_x = 4
                    row.popover(panel="NODE_PT_material_slots")

                row = layout.row()
                row.enabled = has_material_slots

                # Show material.new when no active ID/slot exists
                if not id_from and ob_type in types_that_support_material:
                    row.template_ID(ob, "active_material", new="material.new")
                # Material ID, but not for Lights
                if id_from and ob_type != 'LIGHT':
                    row.template_ID(id_from, "active_material", new="material.new")

            if snode.shader_type == 'WORLD':
                NODE_MT_editor_menus.draw_collapsible(context, layout)

                row = layout.row()
                row.enabled = not snode.pin
                row.template_ID(scene, "world", new="world.new")

            if snode.shader_type == 'LINESTYLE':
                view_layer = context.view_layer
                lineset = view_layer.freestyle_settings.linesets.active

                if lineset is not None:
                    NODE_MT_editor_menus.draw_collapsible(context, layout)

                    row = layout.row()
                    row.enabled = not snode.pin
                    row.template_ID(lineset, "linestyle", new="scene.freestyle_linestyle_new")

        elif snode.tree_type == 'TextureNodeTree':
            layout.prop(snode, "texture_type", text="")

            NODE_MT_editor_menus.draw_collapsible(context, layout)

            if id_from:
                if snode.texture_type == 'BRUSH':
                    layout.template_ID(id_from, "texture", new="texture.new")
                else:
                    layout.template_ID(id_from, "active_texture", new="texture.new")

        elif snode.tree_type == 'CompositorNodeTree':

            NODE_MT_editor_menus.draw_collapsible(context, layout)

            if snode_id:
                layout.prop(snode_id, "use_nodes")

        else:
            # Custom node tree is edited as independent ID block
            NODE_MT_editor_menus.draw_collapsible(context, layout)

            layout.template_ID(snode, "node_tree", new="node.new_node_tree")

        #################### options at the right ###################################

        layout.separator_spacer()

        # Put pin on the right for Compositing
        if is_compositor:
            layout.prop(snode, "pin", text="", emboss=False)

        # -------------------- use nodes ---------------------------

        if snode.tree_type == 'ShaderNodeTree':

            if snode.shader_type == 'OBJECT' and ob:

                # No shader nodes for Eevee lights
                if snode_id and not (context.engine == 'BLENDER_EEVEE' and ob_type == 'LIGHT'):
                    row = layout.row()
                    row.prop(snode_id, "use_nodes")

            if snode.shader_type == 'WORLD':

                if snode_id:
                    row = layout.row()
                    row.prop(snode_id, "use_nodes")

            if snode.shader_type == 'LINESTYLE':

                if lineset is not None:

                    if snode_id:
                        row = layout.row()
                        row.prop(snode_id, "use_nodes")


        elif snode.tree_type == 'TextureNodeTree':

            if snode_id:
                layout.prop(snode_id, "use_nodes")


        elif snode.tree_type == 'CompositorNodeTree':

            if snode_id:
                layout.prop(snode_id, "use_nodes")


        # ----------------- rest of the options
        

        # Put pin next to ID block
        if not is_compositor:
            layout.prop(snode, "pin", text="", emboss=False)

        layout.operator("node.tree_path_parent", text="", icon='FILE_PARENT')

        # Backdrop
        if is_compositor:
            row=layout.row(align=True)
            row.prop(snode, "show_backdrop", toggle=True)
            sub=row.row(align=True)
            sub.active = snode.show_backdrop
            sub.prop(snode, "backdrop_channels", icon_only=True, text="", expand=True)

        # Snap
        row = layout.row(align=True)
        row.prop(tool_settings, "use_snap", text="")
        if tool_settings.use_snap:
            row.prop(tool_settings, "snap_node_element", icon_only=True)
            if tool_settings.snap_node_element != 'GRID':
                row.prop(tool_settings, "snap_target", text="")

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class NODE_MT_editor_menus(Menu):
    bl_idname = "NODE_MT_editor_menus"
    bl_label = ""

    def draw(self, _context):
        layout = self.layout
        layout.menu("NODE_MT_view")
        layout.menu("NODE_MT_select")
        layout.menu("NODE_MT_add")
        layout.menu("NODE_MT_node")


class NODE_MT_add(bpy.types.Menu):
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Add"
    bl_translation_context = i18n_contexts.operator_default

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'
        props = layout.operator("node.add_search", text="Search...", icon='VIEWZOOM')
        props.use_transform = True

        layout.separator()

        # actual node submenus are defined by draw functions from node categories
        nodeitems_utils.draw_node_categories_menu(self, context)


class NODE_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        snode = context.space_data

        layout.prop(snode, "show_region_toolbar")
        layout.prop(snode, "show_region_ui")
        
        layout.separator()

        layout.operator("view2d.zoom_in", icon = "ZOOM_IN")
        layout.operator("view2d.zoom_out", icon = "ZOOM_OUT")
        layout.operator("view2d.zoom_border", icon = "ZOOM_BORDER")

        layout.separator()

        layout.operator("node.view_selected", icon='VIEW_SELECTED')
        layout.operator("node.view_all", icon = "VIEWALL" )

        if context.space_data.show_backdrop:
            layout.separator()

            layout.operator("node.backimage_move", text="Backdrop Move", icon ='TRANSFORM_MOVE')
            layout.operator("node.backimage_zoom", text="Backdrop Zoom In", icon = "ZOOM_IN").factor = 1.2
            layout.operator("node.backimage_zoom", text="Backdrop Zoom Out", icon = "ZOOM_OUT").factor = 1.0 / 1.2
            layout.operator("node.backimage_fit", text="Fit Backdrop", icon = "VIEW_FIT")
            layout.operator("node.clear_viewer_border", icon = "RENDERBORDER_CLEAR")
            layout.operator("node.viewer_border", icon = "RENDERBORDER")

        layout.separator()

        layout.menu("INFO_MT_area")

# Workaround to separate the tooltips
class NODE_MT_select_inverse(bpy.types.Operator):
    """Inverse\nInverts the current selection """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "node.select_all_inverse"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select Inverse"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.node.select_all(action = 'INVERT')
        return {'FINISHED'}

# Workaround to separate the tooltips
class NODE_MT_select_none(bpy.types.Operator):
    """None\nDeselects everything """      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "node.select_all_none"        # unique identifier for buttons and menu items to reference.
    bl_label = "Select None"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.node.select_all(action = 'DESELECT')
        return {'FINISHED'}


class NODE_MT_select(Menu):
    bl_label = "Select"

    def draw(self, _context):
        layout = self.layout

        layout.operator("node.select_all",text = "All", icon = 'SELECT_ALL').action = 'SELECT'
        layout.operator("node.select_all_none", text="None", icon='SELECT_NONE') # bfa - separated tooltip
        layout.operator("node.select_all_inverse", text="Inverse", icon='INVERSE') # bfa - separated tooltip

        layout.separator()

        layout.operator("node.select_box", icon = 'BORDER_RECT').tweak = False
        layout.operator("node.select_circle", icon = 'CIRCLE_SELECT')

        layout.separator()

        layout.operator("node.select_linked_from", text = "Linked From", icon = "LINKED")
        layout.operator("node.select_linked_to", text = "Linked To", icon = "LINKED")

        layout.separator()

        layout.operator("node.select_grouped", text = "Grouped Extend", icon = "GROUP").extend = True
        layout.operator("node.select_grouped", text = "Grouped", icon = "GROUP").extend = False
        layout.operator("node.select_same_type_step", text="Activate Same Type Previous", icon = "PREVIOUSACTIVE").prev = True
        layout.operator("node.select_same_type_step", text="Activate Same Type Next", icon = "NEXTACTIVE").prev = False

        layout.separator()

        layout.operator("node.find_node", icon='VIEWZOOM')

class NODE_MT_node_group_separate(Menu):
    bl_label = "Separate"

    def draw(self, context):
        layout = self.layout

        layout.operator("node.group_separate", text = "Copy", icon = "SEPARATE").type = 'COPY'
        layout.operator("node.group_separate", text = "Move", icon = "SEPARATE").type = 'MOVE'


class NODE_MT_node(Menu):
    bl_label = "Node"

    def draw(self, _context):
        layout = self.layout

        myvar = layout.operator("transform.translate", icon = "TRANSFORM_MOVE")
        myvar.release_confirm = True
        layout.operator("transform.rotate", icon = "TRANSFORM_ROTATE")
        layout.operator("transform.resize",  icon = "TRANSFORM_SCALE")       

        layout.separator()
        layout.operator("node.clipboard_copy", text="Copy", icon='COPYDOWN')
        layout.operator("node.clipboard_paste", text="Paste", icon='PASTEDOWN')


        layout.separator()

        layout.operator("node.duplicate_move_keep_inputs", text = "Duplicate Keep Input", icon = "DUPLICATE")
        layout.operator("node.duplicate_move", icon = "DUPLICATE")
        layout.operator("node.delete", icon = "DELETE")
        layout.operator("node.delete_reconnect", icon = "DELETE")

        layout.separator()

        layout.operator("node.join", text="Join in New Frame", icon = "JOIN")
        layout.operator("node.detach", text="Remove from Frame", icon = "DELETE")

        layout.separator()

        layout.operator("node.link_make", icon = "LINK_DATA").replace = False
        layout.operator("node.link_make", text="Make and Replace Links", icon = "LINK_DATA").replace = True
        layout.operator("node.links_cut", icon = "CUT_LINKS")
        layout.operator("node.links_detach", icon = "DETACH_LINKS")
        layout.operator("node.move_detach_links", text = "Detach Links Move", icon = "DETACH_LINKS")
        layout.operator("node.parent_set", icon = "PARENT_SET")

        layout.separator()

        layout.operator("node.group_edit", icon = "NODE_EDITGROUP").exit = False
        layout.operator("node.group_edit_exit", text="Exit Edit Group", icon = "NODE_EXITEDITGROUP") # bfa - separated tooltip
        layout.operator("node.group_ungroup", icon = "NODE_UNGROUP")
        layout.operator("node.group_make", icon = "NODE_MAKEGROUP")
        layout.operator("node.group_insert", icon = "NODE_GROUPINSERT")
        layout.menu("NODE_MT_node_group_separate")

        layout.separator()

        layout.operator("node.hide_toggle", icon = "RESTRICT_VIEW_ON")
        layout.operator("node.mute_toggle", icon = "TOGGLE_NODE_MUTE")
        layout.operator("node.preview_toggle", icon = "TOGGLE_NODE_PREVIEW")
        layout.operator("node.hide_socket_toggle", icon = "RESTRICT_VIEW_OFF")
        layout.operator("node.options_toggle", icon = "TOGGLE_NODE_OPTIONS")
        layout.operator("node.collapse_hide_unused_toggle", icon = "HIDE_UNSELECTED")

        layout.separator()

        layout.operator("node.read_viewlayers", icon = "RENDERLAYERS")
        layout.operator("node.render_changed", icon = "RENDERLAYERS")


class NODE_PT_active_tool(ToolActivePanelHelper, Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Tool"


class NODE_PT_material_slots(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'HEADER'
    bl_label = "Slot"
    bl_ui_units_x = 8

    def draw_header(self, context):
        ob = context.object
        self.bl_label = (
            "Slot " + str(ob.active_material_index + 1) if ob.material_slots else
            "Slot"
        )

    # Duplicate part of 'EEVEE_MATERIAL_PT_context_material'.
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()

        ob = context.object
        col.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index")

        col = row.column(align=True)
        col.operator("object.material_slot_add", icon='ADD', text="")
        col.operator("object.material_slot_remove", icon='REMOVE', text="")

        col.separator()

        col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

        if len(ob.material_slots) > 1:
            col.separator()

            col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'


class NODE_PT_node_color_presets(PresetPanel, Panel):
    """Predefined node color"""
    bl_label = "Color Presets"
    preset_subdir = "node_color"
    preset_operator = "script.execute_preset"
    preset_add_operator = "node.node_color_preset_add"


class NODE_MT_node_color_context_menu(Menu):
    bl_label = "Node Color Specials"

    def draw(self, _context):
        layout = self.layout

        layout.operator("node.node_copy_color", icon='COPY_ID')


class NODE_MT_context_menu(Menu):
    bl_label = "Node Context Menu"

    def draw(self, context):
        layout = self.layout

        selected_nodes_len = len(context.selected_nodes)

        # If nothing is selected
        # (disabled for now until it can be made more useful).
        '''
        if selected_nodes_len == 0:
            layout.operator_context = 'INVOKE_DEFAULT'
            layout.menu("NODE_MT_add")
            layout.operator("node.clipboard_paste", text="Paste")
            return
        '''

        # If something is selected
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("node.duplicate_move")
        layout.operator("node.delete")
        layout.operator("node.clipboard_copy", text="Copy")
        layout.operator("node.clipboard_paste", text="Paste")
        layout.operator_context = 'EXEC_DEFAULT'

        layout.operator("node.delete_reconnect")

        if selected_nodes_len > 1:
            layout.separator()

            layout.operator("node.link_make").replace = False
            layout.operator("node.link_make", text="Make and Replace Links").replace = True
            layout.operator("node.links_detach")

            layout.separator()

            layout.operator("node.group_make", text="Group")

        layout.operator("node.group_ungroup", text="Ungroup")
        layout.operator("node.group_edit").exit = False

        layout.separator()

        layout.operator("node.hide_toggle")
        layout.operator("node.mute_toggle")
        layout.operator("node.preview_toggle")
        layout.operator("node.hide_socket_toggle")
        layout.operator("node.options_toggle")
        layout.operator("node.collapse_hide_unused_toggle")


class NODE_PT_active_node_generic(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Item"
    bl_label = "Node"

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def draw(self, context):
        layout = self.layout
        node = context.active_node

        layout.prop(node, "name", icon='NODE')
        layout.prop(node, "label", icon='NODE')


class NODE_PT_active_node_color(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Item"
    bl_label = "Color"
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = 'NODE_PT_active_node_generic'

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def draw_header(self, _context):
        node = context.active_node
        self.layout.prop(node, "use_custom_color", text="")

    def draw_header_preset(self, context):
        NODE_PT_node_color_presets.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout
        node = context.active_node

        layout.enabled = node.use_custom_color

        row = layout.row()
        row.prop(node, "color", text="")
        row.menu("NODE_MT_node_color_context_menu", text="", icon='DOWNARROW_HLT')


class NODE_PT_active_node_properties(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Item"
    bl_label = "Properties"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def draw(self, context):
        layout = self.layout
        node = context.active_node
        # set "node" context pointer for the panel layout
        layout.context_pointer_set("node", node)

        if hasattr(node, "draw_buttons_ext"):
            node.draw_buttons_ext(context, layout)
        elif hasattr(node, "draw_buttons"):
            node.draw_buttons(context, layout)

        # XXX this could be filtered further to exclude socket types
        # which don't have meaningful input values (e.g. cycles shader)
        value_inputs = [socket for socket in node.inputs if socket.enabled and not socket.is_linked]
        if value_inputs:
            layout.separator()
            layout.label(text="Inputs:")
            for socket in value_inputs:
                row = layout.row()
                socket.draw(context, row, node, iface_(socket.name, socket.bl_rna.translation_context))


class NODE_PT_texture_mapping(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Item"
    bl_label = "Texture Mapping"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_EEVEE', 'BLENDER_WORKBENCH'}

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node and hasattr(node, "texture_mapping") and (context.engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        node = context.active_node
        mapping = node.texture_mapping

        layout.prop(mapping, "vector_type")

        layout.separator()

        col = layout.column(align=True)
        col.prop(mapping, "mapping_x", text="Projection X")
        col.prop(mapping, "mapping_y", text="Y")
        col.prop(mapping, "mapping_z", text="Z")

        layout.separator()

        layout.prop(mapping, "translation")
        layout.prop(mapping, "rotation")
        layout.prop(mapping, "scale")


# Node Backdrop options
class NODE_PT_backdrop(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_label = "Backdrop"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'CompositorNodeTree'

    def draw_header(self, context):
        snode = context.space_data
        self.layout.prop(snode, "show_backdrop", text="")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        snode = context.space_data
        layout.active = snode.show_backdrop

        col = layout.column()

        col.prop(snode, "backdrop_channels", text="Channels")
        col.prop(snode, "backdrop_zoom", text="Zoom")

        col.prop(snode, "backdrop_offset", text="Offset")

        col.separator()

        col.operator("node.backimage_move", text="Move")
        col.operator("node.backimage_fit", text="Fit")


class NODE_PT_quality(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Options"
    bl_label = "Performance"

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type == 'CompositorNodeTree' and snode.node_tree is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        snode = context.space_data
        tree = snode.node_tree

        col = layout.column()
        col.prop(tree, "render_quality", text="Render")
        col.prop(tree, "edit_quality", text="Edit")
        col.prop(tree, "chunk_size")

        col = layout.column()
        col.prop(tree, "use_opencl")
        col.prop(tree, "use_groupnode_buffer")
        col.prop(tree, "use_two_pass")
        col.prop(tree, "use_viewer_border")
        col.separator()
        col.prop(snode, "use_auto_render")


class NODE_UL_interface_sockets(bpy.types.UIList):
    def draw_item(self, context, layout, _data, item, icon, _active_data, _active_propname, _index):
        socket = item
        color = socket.draw_color(context)

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)

            # inputs get icon on the left
            if not socket.is_output:
                row.template_node_socket(color=color)

            row.prop(socket, "name", text="", emboss=False, icon_value=icon)

            # outputs get icon on the right
            if socket.is_output:
                row.template_node_socket(color=color)

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.template_node_socket(color=color)


# Grease Pencil properties
class NODE_PT_grease_pencil(AnnotationDataPanel, Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}

    # NOTE: this is just a wrapper around the generic GP Panel

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode is not None and snode.node_tree is not None


class NODE_PT_grease_pencil_tools(GreasePencilToolsPanel, Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "View"
    bl_options = {'DEFAULT_CLOSED'}

    # NOTE: this is just a wrapper around the generic GP tools panel
    # It contains access to some essential tools usually found only in
    # toolbar, but which may not necessarily be open


def node_draw_tree_view(_layout, _context):
    pass


# Workaround to separate the tooltips for Show Hide for Armature in Edit Mode
class NODE_MT_exit_edit_group(bpy.types.Operator):
    """Exit Edit Group\nExit edit node group"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "node.group_edit_exit"        # unique identifier for buttons and menu items to reference.
    bl_label = "Group Edit Exit"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

# Adapt properties editor panel to display in node editor. We have to
# copy the class rather than inherit due to the way bpy registration works.
def node_panel(cls):
    node_cls = type('NODE_' + cls.__name__, cls.__bases__, dict(cls.__dict__))

    node_cls.bl_space_type = 'NODE_EDITOR'
    node_cls.bl_region_type = 'UI'
    node_cls.bl_category = "Options"
    if hasattr(node_cls, 'bl_parent_id'):
        node_cls.bl_parent_id = 'NODE_' + node_cls.bl_parent_id

    return node_cls

class NODE_PT_view(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Node"
    bl_label = "View"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        snode = context.space_data
        return snode.tree_type in ('CompositorNodeTree', 'TextureNodeTree')

    def draw(self, context):
        layout = self.layout

        snode = context.space_data

        # Auto-offset nodes (called "insert_offset" in code)
        layout.prop(snode, "use_insert_offset")

classes = (
    ALL_MT_editormenu,
    NODE_HT_header,
    NODE_MT_editor_menus,
    NODE_MT_add,
    NODE_MT_view,
    NODE_MT_select_inverse,
    NODE_MT_select_none,
    NODE_MT_select,
    NODE_MT_node_group_separate,
    NODE_MT_node,
    NODE_MT_node_color_context_menu,
    NODE_MT_context_menu,
    NODE_PT_material_slots,
    NODE_PT_node_color_presets,
    NODE_PT_active_node_generic,
    NODE_PT_active_node_color,
    NODE_PT_active_node_properties,
    NODE_PT_texture_mapping,
    NODE_PT_active_tool,
    NODE_PT_backdrop,
    NODE_PT_quality,
    NODE_PT_grease_pencil,
    NODE_PT_grease_pencil_tools,
    NODE_UL_interface_sockets,

    node_panel(EEVEE_MATERIAL_PT_settings),
    node_panel(MATERIAL_PT_viewport),
    node_panel(WORLD_PT_viewport_display),
    node_panel(DATA_PT_light),
    node_panel(DATA_PT_EEVEE_light),
    NODE_MT_exit_edit_group, # BFA - Draise
    NODE_PT_view,
)


if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
