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

from bpy.types import Operator

from .func import (context_exec_single_line, context_exec_textblock)
from ..log_text import log_text_name

class PYREC_OT_ContextExec(Operator):
    bl_description = "Run exec() Python command with given string, from either Single Line or Text"
    bl_idname = "py_rec.context_exec"
    bl_label = "Exec"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_eo = context.window_manager.py_rec.context_exec_options
        if pr_eo.exec_type == "single_line":
            single_line = pr_eo.single_line
            if pr_eo.single_line == "":
                self.report({'INFO'}, "Single Line is empty, nothing to exec()")
                return {'CANCELLED'}
            if not context_exec_single_line(single_line, True):
                self.report({'INFO'}, "Exception occurred during exec() of Single Line, see '%s' in Text Editor" % \
                            log_text_name())
                return {'CANCELLED'}
        else:
            textblock = pr_eo.textblock
            if pr_eo.textblock is None:
                self.report({'INFO'}, "Text name is missing, nothing to exec()")
                return {'CANCELLED'}
            text_name = textblock.name
            if not context_exec_textblock(textblock, True):
                self.report({'INFO'}, "Exception occurred during exec() of Text named '%s', see '%s' in " \
                            "Text Editor" %  (text_name, log_text_name()) )
        return {'FINISHED'}
