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

from bpy.types import Panel

from .operator import PYREC_OT_RecordNodetree

class PYREC_PT_RecordNodetree(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_label = "Py Record Nodetree"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ntr = context.window_manager.py_rec.record_options.nodetree
        layout = self.layout

        layout.operator(PYREC_OT_RecordNodetree.bl_idname)
        layout.label(text="General Options")
        box = layout.box()
        box.prop(ntr, "num_space_pad")
        box.prop(ntr, "keep_links")
        box.prop(ntr, "make_function")
        box.prop(ntr, "delete_existing")
        box.prop(ntr, "ng_output_min_max_def")
        layout.label(text="Node Attribute Options")
        box = layout.box()
        box.prop(ntr, "write_attrib_name")
        box.prop(ntr, "write_attrib_select")
        box.prop(ntr, "write_attrib_width_and_height")
        box.prop(ntr, "write_loc_decimal_places")
        layout.label(text="Write Defaults Options")
        box = layout.box()
        box.prop(ntr, "write_default_values")
        box.prop(ntr, "write_linked_default_values")
