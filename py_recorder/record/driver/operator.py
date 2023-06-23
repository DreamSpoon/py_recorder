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

from .func import (create_driver_py_from_data_item, set_bool_vec_state)

class PYREC_OT_DriversToPython(Operator):
    bl_description = "Convert all drivers of selected data sources to Python code, available in the Text Editor"
    bl_idname = "py_rec.driver_editor_record_driver"
    bl_label = "Record Driver"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        dr = context.window_manager.py_rec.record_options.driver
        text = create_driver_py_from_data_item(dr.num_space_pad, dr.make_function, dr.animdata_bool_vec)
        self.report({'INFO'}, "Driver(s) recorded to Python in Text named '%s'" % text.name)
        return {'FINISHED'}

class PYREC_OT_SelectAnimdataSrcAll(Operator):
    bl_description = "Select all available data sources"
    bl_idname = "py_rec.driver_editor_select_animdata_src_all"
    bl_label = "Select All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        dr = context.window_manager.py_rec.record_options.driver
        set_bool_vec_state(dr.animdata_bool_vec, True)
        return {'FINISHED'}

class PYREC_OT_SelectAnimdataSrcNone(Operator):
    bl_description = "Select all available data sources"
    bl_idname = "py_rec.driver_editor_select_animdata_src_none"
    bl_label = "Select None"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        dr = context.window_manager.py_rec.record_options.driver
        set_bool_vec_state(dr.animdata_bool_vec, False)
        return {'FINISHED'}
