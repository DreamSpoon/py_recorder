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

CPROP_NAME_INIT_PY = "__init__.py"

class PYREC_OT_OBJ_ModifyInit(Operator):
    bl_description = "Modify active Object's custom property '"+CPROP_NAME_INIT_PY+""
    bl_idname = "py_rec.object_modify_init"
    bl_label = "Modify Data Type"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        if pr_ir.modify_data_type == "texts":
            context.active_object[CPROP_NAME_INIT_PY] = pr_ir.modify_data_text
        elif pr_ir.modify_data_type == "objects":
            context.active_object[CPROP_NAME_INIT_PY] = pr_ir.modify_data_obj
        else:
            try:
                del context.active_object[CPROP_NAME_INIT_PY]
            except:
                pass
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        pr_ir = context.window_manager.py_rec.record_options.info
        layout.prop(pr_ir, "modify_data_type")
        if pr_ir.modify_data_type == "texts":
            layout.prop(pr_ir, "modify_data_text")
        elif pr_ir.modify_data_type == "objects":
            layout.prop(pr_ir, "modify_data_obj")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class PYREC_OT_OBJ_AddCP_Data(Operator):
    bl_idname = "py_rec.object_add_custom_property_data"
    bl_label = "New"
    bl_description = "Create new Custom Property on active Object, with given Name and Data"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        return context.active_object != None and pr_ir.add_cp_data_name not in [None, ""] and \
            pr_ir.add_cp_datablock not in [None, ""]

    def execute(self, context):
        act_ob = context.active_object
        pr_ir = context.window_manager.py_rec.record_options.info
        v = getattr(bpy.data, pr_ir.add_cp_data_type).get(pr_ir.add_cp_datablock)
        if v != None:
            act_ob[pr_ir.add_cp_data_name] = v
        return {'FINISHED'}
