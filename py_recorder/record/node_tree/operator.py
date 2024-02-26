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

# from mathutils import (Color, Vector)
# import bpy
# from bpy.props import (BoolProperty, IntProperty)

# from ...bpy_value_string import bpy_value_to_string

from bpy.types import Operator

from .func import (LOC_DEC_PLACES_UNI_NODE_OPT, WRITE_ATTR_NAME_UNI_NODE_OPT, WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT,
    WRITE_ATTR_SELECT_UNI_NODE_OPT, create_code_text)

class PYREC_OT_RecordNodetree(Operator):
    bl_idname = "py_rec.node_editor_record_nodetree"
    bl_label = "Record Nodetree"
    bl_description = "Make Python text-block from current node tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        s = context.space_data
        if s.type == 'NODE_EDITOR' and s.node_tree != None and \
            s.tree_type in ('CompositorNodeTree', 'ShaderNodeTree', 'TextureNodeTree', 'GeometryNodeTree'):
            return True
        return False

    def execute(self, context):
        ntr = context.window_manager.py_rec.record_options.nodetree
        uni_node_options = {
            LOC_DEC_PLACES_UNI_NODE_OPT: ntr.write_loc_decimal_places,
            WRITE_ATTR_NAME_UNI_NODE_OPT: ntr.write_attrib_name,
            WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT: ntr.write_attrib_width_and_height,
            WRITE_ATTR_SELECT_UNI_NODE_OPT: ntr.write_attrib_select,
        }
        text = create_code_text(context, ntr.ng_output_min_max_def, uni_node_options)
        self.report({'INFO'}, "Nodetree recorded to Python in Text named '%s'" % text.name)
        return {'FINISHED'}
