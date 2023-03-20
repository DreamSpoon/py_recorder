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

import traceback

import bpy
from bpy.props import (BoolProperty, EnumProperty, PointerProperty, StringProperty)
from bpy.types import (Operator, PropertyGroup)
from bpy.utils import (register_class, unregister_class)

from .log_text import (LOG_TEXT_NAME, log_text_append)

exec_panel_classes = {}
EXEC_PANEL_REGISTER = "class PYREC_PT_%s_Exec(bpy.types.Panel):\n" \
      "    bl_space_type = '%s'\n" \
      "    bl_region_type = 'UI'\n" \
      "    bl_category = \"Tool\"\n" \
      "    bl_label = \"Py Exec\"\n" \
      "    bl_options = {'DEFAULT_CLOSED'}\n" \
      "    def draw(self, context):\n" \
      "        exec_panel_draw(self, context)\n" \
      "register_class(PYREC_PT_%s_Exec)\n" \
      "global exec_panel_classes\n" \
      "exec_panel_classes['PYREC_PT_%s_Exec'] = PYREC_PT_%s_Exec\n"

def register_exec_panel(context_name):
    try:
        exec(EXEC_PANEL_REGISTER % (context_name, context_name, context_name, context_name, context_name))
    except:
        return False
    return True

def unregister_exec_panel(context_name):
    panel_classname = "PYREC_PT_%s_Exec" % context_name
    panel_class = exec_panel_classes.get(panel_classname)
    if panel_class is None:
        return False
    try:
        del exec_panel_classes[panel_classname]
        unregister_class(panel_class)
        return True
    except:
        return False

#ALL_CONTEXT_NAMES = ('EMPTY', 'VIEW_3D', 'IMAGE_EDITOR', 'NODE_EDITOR', 'SEQUENCE_EDITOR', 'CLIP_EDITOR',
#    'DOPESHEET_EDITOR', 'GRAPH_EDITOR', 'NLA_EDITOR', 'TEXT_EDITOR', 'CONSOLE', 'INFO', 'TOPBAR', 'STATUSBAR',
#    'OUTLINER', 'PROPERTIES', 'FILE_BROWSER', 'SPREADSHEET', 'PREFERENCES')
EXEC_CONTEXT_NAMES = ('VIEW_3D', 'IMAGE_EDITOR', 'NODE_EDITOR', 'SEQUENCE_EDITOR', 'CLIP_EDITOR', 'DOPESHEET_EDITOR',
    'GRAPH_EDITOR', 'NLA_EDITOR', 'TEXT_EDITOR', 'SPREADSHEET', 'PREFERENCES')
def append_exec_context_panel_all():
    for context_name in EXEC_CONTEXT_NAMES:
        register_exec_panel(context_name)

def remove_exec_context_panel_all():
    for context_name in EXEC_CONTEXT_NAMES:
        unregister_exec_panel(context_name)

class PYREC_PG_ExecOptions(PropertyGroup):
    exec_type: EnumProperty(name="Type", items=[ ("single_line", "Single Line", ""), ("textblock", "Text", "") ],
        default="single_line", description="Exec single line of code, or multi-line Text (see Text-Editor)")
    single_line: StringProperty(description="Single line of code to exec()")
    textblock: PointerProperty(description="Text to exec()", type=bpy.types.Text)
    run_auto_import_bpy: BoolProperty(name="Auto 'import bpy'", description="Automatically prepend line to script, " +
        "if needed, to prevent error: \"NameError: name 'bpy' is not defined\"", default=True)
    run_as_text_script: BoolProperty(name="Run in Text Editor", description="If enabled then Python code from " +
        "Textblock / Text Object will be 'run as script' in Text Editor. If disabled then Python code will be " +
        "run directly with exec()", default=False)
    use_operator_functions: BoolProperty(name="Operator Functions", description="Use Operator functions ('invoke', " +
        "'draw', 'execute'), if found. Notes: Operator Functions are not available if 'Run in Text Editor', and " +
        "windows will not display if 'Batch Exec' is used; only 'execute' is run during 'Batch Exec'",
        default=True)

def context_exec_single_line(single_line, enable_log):
    try:
        exec(single_line)
        return True
    except:
        if enable_log:
            log_text_append("Exception raised during Exec of single line:\n%s\n\n%s" %
                            (single_line, traceback.format_exc()))
        return False

def context_exec_textblock(textblock, enable_log):
    try:
        exec(textblock.as_string())
        return True
    except:
        if enable_log:
            log_text_append("Exception raised during Exec of Text:\n%s\n\n%s" %
                            (textblock.name, traceback.format_exc()))
        return False

class PYREC_OT_ContextExec(Operator):
    bl_description = ""
    bl_idname = "py_rec.context_exec"
    bl_label = "Exec"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_eo = context.window_manager.py_rec.exec_options
        if pr_eo.exec_type == "single_line":
            single_line = pr_eo.single_line
            if pr_eo.single_line == "":
                self.report({'INFO'}, "Single Line is empty, nothing to exec()")
                return {'CANCELLED'}
            if not context_exec_single_line(single_line, True):
                self.report({'INFO'}, "Exception occurred during exec() of Single Line, see '%s' in Text Editor" % \
                            LOG_TEXT_NAME)
                return {'CANCELLED'}
        else:
            textblock = pr_eo.textblock
            if pr_eo.textblock is None:
                self.report({'INFO'}, "Text name is missing, nothing to exec()")
                return {'CANCELLED'}
            text_name = textblock.name
            if not context_exec_textblock(textblock, True):
                self.report({'INFO'}, "Exception occurred during exec() of Text named '%s', see '%s' in Text Editor"% \
                            (text_name, LOG_TEXT_NAME))
        return {'FINISHED'}

def exec_panel_draw(self, context):
    pr_eo = context.window_manager.py_rec.exec_options
    layout = self.layout
    box = layout.box()
    box.prop(pr_eo, "exec_type")
    if pr_eo.exec_type == "single_line":
        box.prop(pr_eo, "single_line", text="")
    else:
        box.prop(pr_eo, "textblock", text="")
    box.operator(PYREC_OT_ContextExec.bl_idname)
