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

from datetime import datetime as dt
import re
import traceback

import bpy
from bpy.types import Operator

from .string_exec import exec_str
from .object_custom_prop import CPROP_NAME_INIT_PY

SCRIPT_RUN_NAME_APPEND = "_RunTemp"
ERROR_RUN_NAME_APPEND = "_Error"

def create_error_text(error_text_name, error_msg):
    date_time = dt.now().strftime("Error date: %m/%d/%Y\nError time: %H:%M:%S\n")
    # create Text to receive error message string
    print("Py Recorder: create error traceback Text named: " + error_text_name)
    error_text = bpy.data.texts.new(name=error_text_name)
    error_text.from_string(date_time+error_msg)
    return error_text

def add_text_prepend_import_bpy(text):
    # save state of Text current/select line/character, with plus one line because 'import bpy' will be prepended
    old_data = (text.current_character, text.current_line_index+1,
                text.select_end_character, text.select_end_line_index+1)
    # write prepend to first character of first line of text
    (text.current_character, text.current_line_index,
     text.select_end_character, text.select_end_line_index) = (0, 0, 0, 0)
    text.write("import bpy\n")
    # restore state of Text current and select line/character
    (text.current_character, text.current_line_index,
     text.select_end_character, text.select_end_line_index) = old_data

def remove_text_prepend_import_bpy(text):
    # save state of Text current/select line/character, with minus one line because 'import bpy' will be removed
    current_line_index = text.current_line_index-1
    if current_line_index < 0:
        current_line_index = 0
    select_end_line_index = text.select_end_line_index-1
    if select_end_line_index < 0:
        select_end_line_index = 0
    old_data = (text.current_character, current_line_index,
                text.select_end_character, select_end_line_index)
    # select first line of 'text'
    (text.current_character, text.current_line_index,
     text.select_end_character, text.select_end_line_index) = (0, 0, 0, 1)
    # write empty string to 'delete' selected line
    text.write("")
    # restore state of Text current and select line/character
    (text.current_character, text.current_line_index,
     text.select_end_character, text.select_end_line_index) = old_data

# returns False on error, otherwise returns True
def run_script_in_text_editor(context, textblock):
    # switch context UI type to Text Editor
    prev_type = context.area.ui_type
    context.area.ui_type = 'TEXT_EDITOR'
    # set Text as active in Text Editor
    context.space_data.text = textblock
    # try to run script, allowing for graceful fail, where graceful fail is:
    #   -Python error, lines after run_script will not be run, i.e.
    #     -remain in Text Editor with temporary Text active, so user has quick access to Text script with error
    try:
        bpy.ops.text.run_script()
    except:
        # return False because script caused an error, so Text Editor will remain as current context, and user has
        # quick access to script with error
        tb = traceback.format_exc()
        # create Text to receive error traceback message as string
        return create_error_text(textblock.name+ERROR_RUN_NAME_APPEND, tb)
    # change context to previous type
    context.area.ui_type = prev_type
    # return None because script did not cause error
    return None

PY_IMPORT_BPY_RE = r"^[\s]*import bpy[\s]*$"

# returns False on error, otherwise returns True
def run_object_init(context, ob, run_as_text_script, auto_import_bpy):
    init_thing = ob.get(CPROP_NAME_INIT_PY)
    if init_thing != None:
        if isinstance(init_thing, bpy.types.Text):
            print("Py Recorder: Exec Object with Text named: " + init_thing.name)
            if run_as_text_script:
                # prepend 'import bpy' line if needed
                import_bpy_prepended = False
                if auto_import_bpy and not re.match(init_thing.as_string(), PY_IMPORT_BPY_RE,
                                                    flags=(re.MULTILINE | re.DOTALL)):
                    add_text_prepend_import_bpy(init_thing)
                    import_bpy_prepended = True
                # if run results in error then return False to indicate error result
                error_text = run_script_in_text_editor(context, init_thing)
                # remove 'import bpy' line if it was prepended
                if auto_import_bpy and import_bpy_prepended:
                    remove_text_prepend_import_bpy(init_thing)
                return error_text
            else:
                succeed, error_msg = exec_str(init_thing.as_string())
                if not succeed:
                    return create_error_text(init_thing.name+ERROR_RUN_NAME_APPEND, error_msg)
        elif isinstance(init_thing, bpy.types.Object) and init_thing.type == 'FONT':
            text_str = init_thing.data.body
            if run_as_text_script:
                # temporary Text name includes Text Object name, to help user identify and debug issues/errors
                temp_text = bpy.data.texts.new(name=init_thing.name+SCRIPT_RUN_NAME_APPEND)
                # write lines from Text Object body to temporary Text
                temp_text.write(text_str)
                if auto_import_bpy and not re.match(text_str, PY_IMPORT_BPY_RE, flags=(re.MULTILINE | re.DOTALL)):
                    add_text_prepend_import_bpy(temp_text)
                print("Py Recorder: Exec Object with Text Object named '%s', and Temporary Text named '%s'" % \
                      (init_thing.name, temp_text.name))
                # return False if run script resulted in error
                error_text = run_script_in_text_editor(context, temp_text)
                if error_text != None:
                    return error_text
                # remove temporary Text, only if run script did not result in error
                bpy.data.texts.remove(temp_text)
            else:
                print("Py Recorder: Exec Object with Text Object named: " + init_thing.name)
                succeed, error_msg = exec_str(text_str)
                if not succeed:
                    return create_error_text(init_thing.name+ERROR_RUN_NAME_APPEND, error_msg)
    # no errors, so return None
    return None

class PYREC_OT_VIEW3D_RunObjectScript(Operator):
    bl_idname = "py_rec.view3d_run_object_script"
    bl_label = "Exec Object"
    bl_description = "Run selected Objects' Custom Property '"+CPROP_NAME_INIT_PY+"' as script. If property links " \
        "to Text Object type: Text Object body is run. If property is Text type (see Text Editor): lines of Text " \
        "are run"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        for ob in context.selected_objects:
            # get Object name before running init, to prevent errors in case Object is removed by running init
            o_name = ob.name
            # if run results in error, then halt and print name of Object that has script with error
            error_text = run_object_init(context, ob, pr_ir.run_as_text_script, pr_ir.run_auto_import_bpy)
            if error_text != None:
                self.report({'ERROR'}, "Error, see details of run of Object named '%s' in error message " \
                            "Textblock named '%s'" % (o_name, error_text.name))
                return {'CANCELLED'}
        return {'FINISHED'}
