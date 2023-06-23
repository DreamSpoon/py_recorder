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

from .operator import (PYREC_OT_ExecObject, PYREC_OT_BatchExecObject)

class PYREC_PT_VIEW3D_ExecObject(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Py Exec Object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        p_r = context.window_manager.py_rec
        layout = self.layout

        layout.operator(PYREC_OT_ExecObject.bl_idname)
        layout.operator(PYREC_OT_BatchExecObject.bl_idname)
        layout.label(text="Options")
        layout.prop(p_r.object_exec_options, "run_auto_import_bpy")
        layout.prop(p_r.object_exec_options, "run_as_text_script")
        col = layout.column()
        col.active = not p_r.object_exec_options.run_as_text_script
        col.prop(p_r.object_exec_options, "use_operator_functions")
