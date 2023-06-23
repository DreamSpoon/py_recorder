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

from .func import (get_info_lines, copy_filtered_info_lines, get_copy_info_options)

class PYREC_OT_VIEW3D_StartRecordInfoLine(Operator):
    bl_idname = "py_rec.view3d_start_record_info_line"
    bl_label = "Start Record"
    bl_description = "Mark current end line of Info lines as 'Start Record' line. When 'Stop Record' is used, " \
        "then lines from Info context will be copied, beginning at 'Start Record' line and ending at 'Stop Record' " \
        "line, inclusive. See Info context window"
    bl_options = {'REGISTER'}

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        pr_ir.record_info_line = True
        pr_ir.record_info_start_line_offset = len(get_info_lines(context).splitlines())
        self.report({'INFO'}, "Start Record: begin at Info line number %i" % pr_ir.record_info_start_line_offset)
        return {'FINISHED'}

class PYREC_OT_VIEW3D_StopRecordInfoLine(Operator):
    bl_idname = "py_rec.view3d_stop_record_info_line"
    bl_label = "Stop Record"
    bl_description = "Copy Info context lines to Text or Text Object body, and link Text / Text Object to active " \
        "Object (active Object must be selected). Copy begins at 'Start Record' line and ends at 'Stop Record' " \
        "line of Info context, inclusive"
    bl_options = {'REGISTER'}

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        line_start = pr_ir.record_info_start_line_offset
        line_end, filter_line_count, output_thing = copy_filtered_info_lines(context,
                                                                             get_copy_info_options(pr_ir, line_start))
        # reset recording variables
        pr_ir.record_info_line = False
        pr_ir.record_info_start_line_offset = 0
        if output_thing is None:
            self.report({'ERROR'}, "Stop Record: Zero filtered Info lines found, no lines written")
            return {'CANCELLED'}
        if isinstance(output_thing, bpy.types.Object):
            thing_type = "Object"
        elif isinstance(output_thing, bpy.types.Text):
            thing_type = "Text"
        else:
            thing_type = "thing"
        if line_start+1 == line_end:
            l_str = " %i" % line_end
        else:
            l_str = "s beginning at %i, ending at %i," % (line_start+1, line_end)
        if hasattr(output_thing, "name"):
            thing_name = output_thing.name
        else:
            thing_name = str(output_thing)
        self.report({'INFO'}, "Stop Record: copy Info line"+l_str+" (filtered line count %i) to %s %s" %
                    (filter_line_count, thing_type, thing_name))
        return {'FINISHED'}

class PYREC_OT_VIEW3D_CopyInfoToObjectText(Operator):
    bl_idname = "py_rec.view3d_copy_info_to_object_text"
    bl_label = "Copy Info"
    bl_description = "Copy recently run Blender commands (e.g. rotate Object, create Mesh Plane) to Text or Text " \
        "Object body, and link Text / Text Object to active Object (active Object must be selected). See Info " \
        "context window"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        line_end, filter_line_count, output_thing = copy_filtered_info_lines(context,
                                                                             get_copy_info_options(pr_ir, None))
        if output_thing is None:
            self.report({'ERROR'}, "Copy Info: Zero filtered Info lines found, no lines written")
            return {'CANCELLED'}
        if isinstance(output_thing, bpy.types.Object):
            thing_type = "Object"
        elif isinstance(output_thing, bpy.types.Text):
            thing_type = "Text"
        else:
            thing_type = "thing"
        if line_end == 1:
            l_str = " 1"
        else:
            l_str = "s from 1 to %i" % line_end
        if hasattr(output_thing, "name"):
            thing_name = output_thing.name
        else:
            thing_name = str(output_thing)
        self.report({'INFO'}, "Copy Info: copy Info line"+l_str+" (filtered line count %i) to %s %s" %
                    (filter_line_count, thing_type, thing_name))
        return {'FINISHED'}
