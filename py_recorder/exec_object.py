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
from datetime import datetime as dt

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
def run_script_in_text_editor(context, textblock, auto_import_bpy):
    # prepend 'import bpy' line if needed
    if auto_import_bpy:
        add_text_prepend_import_bpy(textblock)
    # switch context UI type to Text Editor
    prev_type = context.area.ui_type
    context.area.ui_type = 'TEXT_EDITOR'
    # set Text as active in Text Editor
    context.space_data.text = textblock
    # try to run script, allowing for graceful fail, where graceful fail is:
    #   -Python error, lines after run_script will not be run, i.e.
    #     -remain in Text Editor with temporary Text active, so user has quick access to Text script with error
    try:
        print("Py Recorder: bpy.ops.text.run_script() called with Text named: " + textblock.name)
        bpy.ops.text.run_script()
    except:
        # return False because script caused an error, so Text Editor will remain as current context, and user has
        # quick access to script with error
        tb = traceback.format_exc()
        print(tb)   # print(tb) replaces traceback.print_exc()
        # create Text to receive error traceback message as string
        create_error_text(textblock.name+ERROR_RUN_NAME_APPEND, tb)
        return False
    # change context to previous type
    context.area.ui_type = prev_type
    # remove 'import bpy' line if it was prepended
    if auto_import_bpy:
        remove_text_prepend_import_bpy(textblock)
    # return True because script did not cause error
    return True

# returns False on error, otherwise returns True
def run_text_object_body(context, text_ob, use_temp_text, auto_import_bpy):
    text_str = text_ob.data.body
    if use_temp_text:
        # temporary Text name includes Text Object name, to help user identify and debug issues/errors
        temp_text = bpy.data.texts.new(name=text_ob.name+SCRIPT_RUN_NAME_APPEND)
        # write lines from Text Object body to temporary Text
        temp_text.write(text_str)
        # return False if run script resulted in error
        if not run_script_in_text_editor(context, temp_text, auto_import_bpy):
            return False
        # remove temporary Text, only if run script did not result in error
        bpy.data.texts.remove(temp_text)
    else:
        print("Py Recorder: exec() with Text Object named: " + text_ob.name)
        succeed, error_msg = exec_str(text_str, auto_import_bpy)
        if not succeed:
            create_error_text(text_ob.name+ERROR_RUN_NAME_APPEND, error_msg)
            return False
    return True

# returns False on error, otherwise returns True
def run_object_init(context, ob, use_temp_text, auto_import_bpy):
    init_thing = ob.get(CPROP_NAME_INIT_PY)
    if init_thing != None:
        if isinstance(init_thing, bpy.types.Text):
            # if run results in error then return False to indicate error result
            if not run_script_in_text_editor(context, init_thing, auto_import_bpy):
                return False
        elif isinstance(init_thing, bpy.types.Object) and init_thing.type == 'FONT':
            # if run results in error then return False to indicate error result
            if not run_text_object_body(context, init_thing, use_temp_text, auto_import_bpy):
                return False
    # no errors, so return True
    return True

class PYREC_OT_VIEW3D_RunObjectScript(Operator):
    bl_idname = "py_rec.view3d_run_object_script"
    bl_label = "Exec Object"
    bl_description = "Run selected Objects' Custom Property '"+CPROP_NAME_INIT_PY+"' as script. If property is " \
        "Text Object type: Text Object body is copied to temporary Text, and Text is run as script. If property is " \
        "Text type: Text is run as script using '.run_script()'"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        for ob in context.selected_objects:
            # get Object name before running init, to prevent errors in case Object is removed by running init
            o_name = ob.name
            # if run results in error, then halt and print name of Object that has script with error
            if not run_object_init(context, ob, pr_ir.use_temp_text, pr_ir.run_auto_import_bpy):
                self.report({'ERROR'}, "Error, see System Console for details of run of Object named: " + o_name)
                return {'CANCELLED'}
        return {'FINISHED'}
