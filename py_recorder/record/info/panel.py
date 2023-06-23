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

from .operator import (PYREC_OT_VIEW3D_StopRecordInfoLine, PYREC_OT_VIEW3D_StartRecordInfoLine,
    PYREC_OT_VIEW3D_CopyInfoToObjectText)

class PYREC_PT_VIEW3D_RecordInfo(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Py Record Info"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        layout = self.layout

        box = layout.box()
        # show 'Stop Record' button if recording is on,
        if pr_ir.record_info_line:
            box.operator(PYREC_OT_VIEW3D_StopRecordInfoLine.bl_idname)
        # show 'Start Record' button if recording is off
        else:
            box.operator(PYREC_OT_VIEW3D_StartRecordInfoLine.bl_idname)

        rec_state = "Off"
        if pr_ir.record_info_line:
            rec_state = "On"
        box.label(text="Recording: " + rec_state)

        layout.operator(PYREC_OT_VIEW3D_CopyInfoToObjectText.bl_idname)

        layout.prop(pr_ir, "record_auto_import_bpy")
        layout.prop(pr_ir, "filter_line_count")

        layout.prop(pr_ir, "root_init")
        layout.prop(pr_ir, "create_root_object")
        layout.prop(pr_ir, "use_text_object")
        if pr_ir.use_text_object:
            layout.prop(pr_ir, "output_text_object", text="Text Object")
        else:
            layout.prop(pr_ir, "output_text", text="Text")

        layout = layout.box()
        layout.label(text="Line Options")
        row = layout.row()
        row.label(text="Type")
        row.label(text="Include/Comment")
        box = layout.box()
        row = box.row()
        row.label(text="Context")
        row.prop(pr_ir, "include_line_type_context", text="")
        row.prop(pr_ir, "comment_line_type_context", text="")
        row = box.row()
        row.label(text="Info")
        row.prop(pr_ir, "include_line_type_info", text="")
        row.prop(pr_ir, "comment_line_type_info", text="")
        row = box.row()
        row.label(text="Macro")
        row.prop(pr_ir, "include_line_type_macro", text="")
        row.prop(pr_ir, "comment_line_type_macro", text="")
        row = box.row()
        row.label(text="Operation")
        row.prop(pr_ir, "include_line_type_operation", text="")
        row.prop(pr_ir, "comment_line_type_operation", text="")
        row = box.row()
        row.label(text="Prev Duplicate")
        row.prop(pr_ir, "include_line_type_prev_dup", text="")
        row.prop(pr_ir, "comment_line_type_prev_dup", text="")
        row = box.row()
        row.label(text="Py Recorder")
        row.prop(pr_ir, "include_line_type_py_rec", text="")
        row.prop(pr_ir, "comment_line_type_py_rec", text="")
