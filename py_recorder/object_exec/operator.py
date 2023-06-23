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

from .func import run_object_init
from ..object_custom_prop import CPROP_NAME_INIT_PY

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
        object_exec_options = context.window_manager.py_rec.object_exec_options
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
            run_result = run_object_init(context, ob, object_exec_options.run_as_text_script,
                                         object_exec_options.run_auto_import_bpy)
            if isinstance(run_result, bpy.types.Text):
                self.report({'ERROR'}, "Error, see details of run of Object named '%s' in error message " \
                            "Textblock named '%s'" % (o_name, run_result.name))
                return {'CANCELLED'}
            elif isinstance(run_result, dict) and object_exec_options.use_operator_functions:
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
        object_exec_options = context.window_manager.py_rec.object_exec_options
        ret_val = {'FINISHED'}
        if object_exec_options.use_operator_functions:
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
        object_exec_options = context.window_manager.py_rec.object_exec_options
        if not object_exec_options.use_operator_functions:
            return
        # run 'draw' operator function, if found
        draw_func = self.operator_functions.get("draw")
        if draw_func != None:
            draw_func(self, context)

    def invoke(self, context, event):
        object_exec_options = context.window_manager.py_rec.object_exec_options
        # get active Object and run its linked code, if linked code is found
        act_ob = context.active_object
        o_name = act_ob.name
        run_result = run_object_init(context, act_ob, object_exec_options.run_as_text_script,
                                     object_exec_options.run_auto_import_bpy)
        if isinstance(run_result, bpy.types.Text):
            self.report({'ERROR'}, "Error, see details of run of Object named '%s' in error message " \
                        "Textblock named '%s'" % (o_name, run_result.name))
            return {'CANCELLED'}
        # check/do Operator function 'invoke'
        invoke_ret_val = None
        if isinstance(run_result, dict) and object_exec_options.use_operator_functions:
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
