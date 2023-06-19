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
import inspect
import re
import traceback

import bpy
from bpy.types import (Operator, Panel)

from .object_custom_prop import CPROP_NAME_INIT_PY
from .exec_func import exec_get_exception

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
        # quick access to script with error, and
        # create Text to receive error traceback message as string
        return create_error_text(textblock.name+ERROR_RUN_NAME_APPEND, traceback.format_exc())
    # change context to previous type
    context.area.ui_type = prev_type
    # return None because script did not cause error
    return None

PY_IMPORT_BPY_RE = r"^[\s]*import bpy[\s]*$"

def get_operator_functions(exec_globals):
    search_for = {
        "draw": [ "self", "context" ],
        "execute": [ "self", "context" ],
        "invoke": [ "self", "context", "event" ],
    }
    found_funcs = {}
    for k in search_for:
        test_func = exec_globals.get(k)
        if test_func != None and callable(test_func) and hasattr(test_func, "__code__"):
            test_args = inspect.getargs(test_func.__code__)
            search_args = search_for[k]
            if test_args[0] == search_args:
                found_funcs[k] = test_func
    return found_funcs

# if error, then returns error message string
# if success, then returns dictionary with operator functions found during run of Object's linked code
def run_object_init(context, ob, run_as_text_script, auto_import_bpy):
    init_thing = ob.get(CPROP_NAME_INIT_PY)
    if init_thing != None:
        if isinstance(init_thing, bpy.types.Text):
            print("Py Recorder: Exec Object named '%s', with Text named '%s'" % (ob.name, init_thing.name))
            script_str = init_thing.as_string()
            if run_as_text_script:
                # prepend 'import bpy' line if needed
                import_bpy_prepended = False
                if auto_import_bpy and not re.match(script_str, PY_IMPORT_BPY_RE,
                                                    flags=(re.MULTILINE | re.DOTALL)):
                    add_text_prepend_import_bpy(init_thing)
                    import_bpy_prepended = True
                # if run results in error then return error message
                error_text = run_script_in_text_editor(context, init_thing)
                if error_text != None:
                    return error_text
                # remove 'import bpy' line if it was prepended
                if auto_import_bpy and import_bpy_prepended:
                    remove_text_prepend_import_bpy(init_thing)
            else:
                exec_globals = { "bpy": bpy }
                is_exc, exc_msg = exec_get_exception(script_str, exec_globals)
                if is_exc:
                    full_msg = "Exception raised by Exec of Object named '%s'\n%s" % (ob.name, exc_msg)
                    return create_error_text(init_thing.name+ERROR_RUN_NAME_APPEND, full_msg)
                return get_operator_functions(exec_globals)
        elif isinstance(init_thing, bpy.types.Object) and init_thing.type == 'FONT':
            script_str = init_thing.data.body
            if run_as_text_script:
                # temporary Text name includes Text Object name, to help user identify and debug issues/errors
                temp_text = bpy.data.texts.new(name=init_thing.name+SCRIPT_RUN_NAME_APPEND)
                # write lines from Text Object body to temporary Text
                temp_text.write(script_str)
                if auto_import_bpy and not re.match(script_str, PY_IMPORT_BPY_RE, flags=(re.MULTILINE | re.DOTALL)):
                    add_text_prepend_import_bpy(temp_text)
                print("Py Recorder: Exec Object named '%s', with Text Object named '%s', and Temporary Text " \
                      "named '%s'" % (ob.name, init_thing.name, temp_text.name))
                # return error message if run script resulted in error
                error_text = run_script_in_text_editor(context, temp_text)
                if error_text != None:
                    return error_text
                # remove temporary Text, only if run script did not result in error
                bpy.data.texts.remove(temp_text)
            else:
                print("Py Recorder: Exec Object named '%s' with Text Object named '%s'" % (ob.name, init_thing.name))
                exec_globals = { "bpy": bpy }
                is_exc, exc_msg = exec_get_exception(script_str, exec_globals)
                if is_exc:
                    full_msg = "Exception raised by Exec of Object named '%s'\n%s" % (ob.name, exc_msg)
                    return create_error_text(init_thing.name+ERROR_RUN_NAME_APPEND, full_msg)
                return get_operator_functions(exec_globals)
    # zero errors and zero operator functions, so return empty dictionary
    return {}

# TODO display INFO about results of operator, e.g. number of Objects (with links to code) that were run
class PYREC_OT_BatchExecObject(Operator):
    bl_idname = "py_rec.batch_exec_object"
    bl_label = "Batch Exec"
    bl_description = "Run Python code linked to all selected Objects. Python code is linked by Object Custom " \
        "Property '"+CPROP_NAME_INIT_PY+"'. Link to Text Object type: run code from Text Object body. Link "\
        "to Text type (see Text Editor): run code from Text"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        pr_eo = context.window_manager.py_rec.exec_options
        # make a static copy of selected objects, in case it changes when Object code is run
        selected_objects = [ ob for ob in context.selected_objects ]
        for ob in selected_objects:
            # to avoid errors, do not run code from Objects that have been dereferenced/deleted
            if bpy.data.objects.get(ob.name) is None:
                continue
            # get this Object name before running init, to prevent errors in case Object is removed by running init
            o_name = ob.name
            # make this Object the active Object before running this Object's linked code
            context.view_layer.objects.active = ob
            # if run results in error, then halt and print name of Object that has script with error
            run_result = run_object_init(context, ob, pr_eo.run_as_text_script, pr_eo.run_auto_import_bpy)
            if isinstance(run_result, bpy.types.Text):
                self.report({'ERROR'}, "Error, see details of run of Object named '%s' in error message " \
                            "Textblock named '%s'" % (o_name, run_result.name))
                return {'CANCELLED'}
            elif isinstance(run_result, dict) and pr_eo.use_operator_functions:
                execute_func = run_result.get("execute")
                # run 'execute' operator function, if found - do not return result of running execute
                if execute_func != None:
                    execute_func(self, context)
        return {'FINISHED'}

class PYREC_OT_ExecObject(Operator):
    bl_idname = "py_rec.exec_object"
    bl_label = "Exec Object"
    bl_description = "Run Python code linked to active Object. Python code is linked by Object Custom " \
        "Property '"+CPROP_NAME_INIT_PY+"'. Link to Text Object type: lines from Text Object body are run. Link "\
        "to Text type (see Text Editor): lines of Text are run"
    bl_options = {'REGISTER', 'UNDO'}

    operator_functions = {}

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        pr_eo = context.window_manager.py_rec.exec_options
        ret_val = {'FINISHED'}
        if pr_eo.use_operator_functions:
            execute_func = self.operator_functions.get("execute")
            # reset operator functions dictionary
            self.operator_functions = {}
            # run 'execute' operator function, if found
            if execute_func != None:
                ef_val = execute_func(self, context)
                # prevent a common error, where execute() did not return a value
                if ef_val != None:
                    ret_val = ef_val
        return ret_val

    def draw(self, context):
        pr_eo = context.window_manager.py_rec.exec_options
        if not pr_eo.use_operator_functions:
            return
        # run 'draw' operator function, if found
        draw_func = self.operator_functions.get("draw")
        if draw_func != None:
            draw_func(self, context)

    def invoke(self, context, event):
        pr_eo = context.window_manager.py_rec.exec_options
        # get active Object and run its linked code, if linked code is found
        act_ob = context.active_object
        o_name = act_ob.name
        run_result = run_object_init(context, act_ob, pr_eo.run_as_text_script, pr_eo.run_auto_import_bpy)
        if isinstance(run_result, bpy.types.Text):
            self.report({'ERROR'}, "Error, see details of run of Object named '%s' in error message " \
                        "Textblock named '%s'" % (o_name, run_result.name))
            return {'CANCELLED'}
        # check/do Operator function 'invoke'
        invoke_ret_val = None
        if isinstance(run_result, dict) and pr_eo.use_operator_functions:
            # copy operator functions found
            for k in run_result:
                self.operator_functions[k] = run_result[k]
            # run 'invoke' operator function, if found
            invoke_func = run_result.get("invoke")
            if invoke_func != None:
                temp = invoke_func(self, context, event)
                if isinstance(temp, set):
                    invoke_ret_val = temp
        # if not already 'running modal', and if Operator function for draw() is found, then invoke props dialog
        if (not isinstance(invoke_ret_val, set) or len(invoke_ret_val.intersection({"RUNNING_MODAL"})) < 1) and \
            run_result.get("draw") != None:
            return context.window_manager.invoke_props_dialog(self)
        if invoke_ret_val is None:
            return {'FINISHED'}
        return invoke_ret_val

class PYREC_PT_VIEW3D_ExecObject(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Py Exec Object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pr_eo = context.window_manager.py_rec.exec_options
        layout = self.layout
        box = layout.box()
        box.operator(PYREC_OT_ExecObject.bl_idname)
        box = layout.box()
        box.operator(PYREC_OT_BatchExecObject.bl_idname)
        box = layout.box()
        box.label(text="Options")
        box.prop(pr_eo, "run_auto_import_bpy")
        box.prop(pr_eo, "run_as_text_script")
        col = box.column()
        col.active = not pr_eo.run_as_text_script
        col.prop(pr_eo, "use_operator_functions")
