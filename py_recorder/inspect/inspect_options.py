# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

import bpy
from bpy.types import Operator
from bpy.props import IntProperty

from .inspect_func import get_inspect_context_panel
from .inspect_exec import (inspect_refresh_attribute_list, register_inspect_panel, unregister_inspect_panel)

class PYREC_OT_InspectOptions(Operator):
    bl_description = "Open Py Inspect panel Options window"
    bl_idname = "py_rec.inspect_options"
    bl_label = "Options"
    bl_options = {'REGISTER'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        p_r = context.window_manager.py_rec
        context_name = context.space_data.type
        ic_panel = get_inspect_context_panel(self.panel_num, context_name, p_r.inspect_context_collections)
        if ic_panel is None:
            return
        panel_options = ic_panel.panel_options
        if panel_options is None:
            return
        # check for change of panel name
        old_label = ic_panel.panel_label
        new_label = panel_options.panel_option_label
        if new_label != old_label:
            # unregister old panel
            unregister_inspect_panel(context_name, self.panel_num)
            # change prop to new label
            ic_panel.panel_label = panel_options.panel_option_label
            # register again with new label
            if not register_inspect_panel(context_name, self.panel_num, new_label):
                self.report({'ERROR'}, "Unable to change label of Py Inspect panel previously with label '%s'" % \
                            old_label)
                return {'CANCELLED'}
        # refresh the Attributes List
        inspect_refresh_attribute_list(ic_panel)
        return {'FINISHED'}

    def draw(self, context):
        p_r = context.window_manager.py_rec
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type, p_r.inspect_context_collections)
        if ic_panel is None:
            return
        panel_options = ic_panel.panel_options
        if panel_options is None:
            return
        layout = self.layout

        box = layout.box()
        box.prop(panel_options, "panel_option_label")

        box = layout.box()
        box.label(text="Attribute Value")
        box.prop(panel_options, "display_value_selector")

        box = layout.box()
        box.label(text="Attribute Type")
        row = box.row()
        row.prop(panel_options, "display_attr_type_only")
        col = row.column()
        col.prop(panel_options, "display_attr_type_function")
        col.prop(panel_options, "display_attr_type_builtin")
        col.prop(panel_options, "display_attr_type_bl")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
