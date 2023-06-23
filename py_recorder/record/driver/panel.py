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

from .func import ANIMDATA_BOOL_NAMES
from .operator import (PYREC_OT_DriversToPython, PYREC_OT_SelectAnimdataSrcAll, PYREC_OT_SelectAnimdataSrcNone)

class PYREC_PT_RecordDriver(Panel):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_label = "Py Record Drivers"

    def draw(self, context):
        layout = self.layout
        dr = context.window_manager.py_rec.record_options.driver

        layout.operator(PYREC_OT_DriversToPython.bl_idname)
        layout.prop(dr, "num_space_pad")
        layout.prop(dr, "make_function")
        layout.operator(PYREC_OT_SelectAnimdataSrcAll.bl_idname)
        layout.operator(PYREC_OT_SelectAnimdataSrcNone.bl_idname)
        layout.label(text="Driver Data Source")
        box = layout.box()
        for i in range(len(ANIMDATA_BOOL_NAMES)):
            box.prop(dr, "animdata_bool_vec", index=i, text=ANIMDATA_BOOL_NAMES[i])
