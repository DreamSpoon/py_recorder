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

class PYREC_OT_InspectOptions(Operator):
    bl_description = "Open Py Inspect panel Options window"
    bl_idname = "py_rec.inspect_options"
    bl_label = "Options"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        context_name = context.space_data.type
        p_r = context.scene.py_rec
        ic_panel = get_inspect_context_panel(self.panel_num, context_name, p_r.inspect_context_collections)
        panel_options = ic_panel.panel_options
        layout = self.layout

        box = layout.box()
        box.label(text="Inspect Panel")
        box.prop(panel_options, "display_datablock_refresh")
        box.prop(panel_options, "display_exec_refresh")
        box.prop(panel_options, "display_value_attributes")

        row = layout.row()
        box = row.box()
        box.label(text="Attribute Column")
        box.prop(panel_options, "display_dir_attribute_type")
        box.prop(panel_options, "display_dir_attribute_value")
        box = row.box()
        box.label(text="Attribute Value")
        box.prop(panel_options, "display_value_selector")

        box = layout.box()
        box.label(text="Attribute Description")
        row = box.row()
        row.prop(panel_options, "display_attr_doc")

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
