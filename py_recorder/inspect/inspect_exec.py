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
from bpy.types import UIList
from bpy.utils import (register_class, unregister_class)

from .inspect_func import (get_dir, get_inspect_context_panel, get_pre_exec_str, get_relevant_doc,
    string_to_lines_collection)
from ..log_text import (LOG_TEXT_NAME, log_text_append)

# region_type = 'UI'
inspect_panel_classes = {}
INSPECT_PANEL_REGISTER = "class PYREC_PT_%s_Inspect%i(bpy.types.Panel):\n" \
    "    bl_space_type = '%s'\n" \
    "    bl_region_type = '%s'\n" \
    "    bl_category = \"Tool\"\n" \
    "    bl_label = \"%s\"\n" \
    "    panel_num = %i\n" \
    "    def draw(self, context):\n" \
    "        if len(inspect_exec_panel_draw_func) > 0:\n" \
    "            inspect_exec_panel_draw_func[0](self, context)\n" \
    "register_class(PYREC_PT_%s_Inspect%i)\n" \
    "global inspect_panel_classes\n" \
    "inspect_panel_classes['PYREC_PT_%s_Inspect%i'] = PYREC_PT_%s_Inspect%i\n"

inspect_exec_result = {}

inspect_exec_panel_draw_func = []

INSPECT_UL_DOCLINE_LIST_REGISTER = "class PYREC_UL_%s_DocLineList%i(UIList):\n" \
    "    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):\n" \
    "        layout.label(text=item.name)\n" \
    "register_class(PYREC_UL_%s_DocLineList%i)\n" \
    "global inspect_panel_classes\n" \
    "inspect_panel_classes['PYREC_UL_%s_DocLineList%i'] = PYREC_UL_%s_DocLineList%i\n"

# use 'exec()' command to create new class of this for each Py Inspect panel - to prevent list display problems when
# multiple copies of this class are visible
INSPECT_DIR_ATTRIBUTE_LIST_REGISTER = "class PYREC_UL_%s_DirAttributeList%i(UIList):\n" \
    "    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):\n" \
    "        attribute_list_draw_item(self, context, layout, data, item, icon, active_data, active_propname, index)\n" \
    "register_class(PYREC_UL_%s_DirAttributeList%i)\n" \
    "global inspect_panel_classes\n" \
    "inspect_panel_classes['PYREC_UL_%s_DirAttributeList%i'] = PYREC_UL_%s_DirAttributeList%i\n"

def attribute_list_draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
    panel_options = data.panel_options
    split_denominator = 1
    if panel_options.display_dir_attribute_type:
        split_denominator = split_denominator + 1
    if panel_options.display_dir_attribute_value:
        split_denominator = split_denominator + 1
    split = layout.split(factor=1/split_denominator)
    split.label(text=item.name)
    if panel_options.display_dir_attribute_type:
        split.label(text=item.type_name)
    if panel_options.display_dir_attribute_value:
        row = split.row()
        # display value selector, if possible
        if panel_options.display_value_selector and data.dir_inspect_exec_str != "" and item.name != "." and \
            not item.name.startswith("__") and item.name != "bl_rna":
            result_value = get_inspect_exec_result()
            if result_value != None and hasattr(result_value, item.name):
                attr_val = getattr(result_value, item.name)
                # do not display if attribute value is None or if it is a zero-length list/tuple
                if attr_val != None and not ( isinstance(attr_val, (list, tuple)) and len(attr_val) == 0) and \
                    not callable(attr_val):
                    try:
                        row.prop(result_value, item.name, text="")
                        return
                    except:
                        pass
        # show value str if value selector not available
        row.label(text=item.value_str)

def register_inspect_exec_panel_draw_func(draw_func):
    # replace previous draw function, if any
    inspect_exec_panel_draw_func.clear()
    inspect_exec_panel_draw_func.append(draw_func)

def register_inspect_panel(context_name, index, panel_label):
    # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
    if context_name == "PROPERTIES":
        context_name = "VIEW_3D"
    # File Browser context does not have accessible 'UI' region, so use 'Tools' region instead
    if context_name == "FILE_BROWSER":
        region_type = "TOOLS"
    else:
        region_type = "UI"
    try:
        exec(INSPECT_PANEL_REGISTER % (context_name, index, context_name, region_type, panel_label, index,
                                       context_name, index, context_name, index, context_name, index) )
        exec(INSPECT_UL_DOCLINE_LIST_REGISTER % (context_name, index, context_name, index, context_name, index,
                                                 context_name, index) )
        exec(INSPECT_DIR_ATTRIBUTE_LIST_REGISTER % (context_name, index, context_name, index, context_name, index,
                                                    context_name, index) )
    except:
        return False
    return True

def unregister_inspect_panel_class(panel_classname):
    panel_class = inspect_panel_classes.get(panel_classname)
    if panel_class != None:
        del inspect_panel_classes[panel_classname]
        try:
            unregister_class(panel_class)
        except:
            return

def unregister_inspect_panel(context_name, index):
    # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
    if context_name == "PROPERTIES":
        context_name = "VIEW_3D"
    unregister_inspect_panel_class("PYREC_PT_%s_Inspect%i" % (context_name, index) )
    unregister_inspect_panel_class("PYREC_UL_%s_DocLineList%i" % (context_name, index) )
    unregister_inspect_panel_class("PYREC_UL_%s_DirAttributeList%i" % (context_name, index) )

def unregister_all_inspect_panel_classes():
    for panel_class in inspect_panel_classes.values():
        unregister_class(panel_class)
    inspect_panel_classes.clear()

# returns 2-tuple of (output value, error string)
# error string is None if no error occurred during exec
def refresh_inspect_exec_result(pre_exec_str, inspect_exec_str, enable_log):
    if inspect_exec_str == "":
        return None, "Empty Inspect Exec string"
    ie_str = pre_exec_str + "global inspect_exec_result\ninspect_exec_result['result'] = %s" % inspect_exec_str
    # delete previous result if it exists
    if inspect_exec_result.get("result") != None:
        del inspect_exec_result["result"]
    try:
        exec(ie_str)
    except:
        if enable_log:
            # append newline to ie_str, only if ie_str does not already end with newline character
            end_newline = ""
            if ie_str[-1] != "\n":
                end_newline = "\n"
            log_text_append("Exception raised during Inspect Exec of string:\n%s%s\n%s" %
                            (ie_str, end_newline, traceback.format_exc()))
        return None, "Exception raised during Inspect Exec of string"
    return inspect_exec_result["result"], None

def get_inspect_exec_result():
    return inspect_exec_result.get("result")

def inspect_refresh_attribute_list(ic_panel):
    panel_options = ic_panel.panel_options
    if panel_options is None:
        return
    inspect_value = get_inspect_exec_result()
    # dir listing can only be performed if 'inspect_value' is not None, because None does not have attributes
    if inspect_value is None:
        dir_array = []
    else:
        # get current dir() array, and quit if array is empty
        dir_array = get_dir(inspect_value)
    ic_panel.dir_attributes.clear()
    ic_panel.dir_attributes_index = 0

    # prepend two items in dir_attributes, to include self value and indexed value, so these values are in same format
    # as dir() attributes, because self is attribute of its parent object, and indexed values are dynamic attributes
    dir_item = ic_panel.dir_attributes.add()
    dir_item.name = "."
    dir_item.type_name = ". Self value"
    for attr_name in dir_array:
        # check that inspect_value has attribute, to avoid errors in case 'inspect_value' is indexed
        # (e.g. array, dictionary)
        if not hasattr(inspect_value, attr_name):
            continue
        if panel_options.display_attr_type_only:
            if not (
                (panel_options.display_attr_type_function and callable(getattr(inspect_value, attr_name))) or \
                (panel_options.display_attr_type_builtin and attr_name.startswith("__")) or \
                (panel_options.display_attr_type_bl and attr_name.startswith("bl_")) ):
                continue
        else:
            if not panel_options.display_attr_type_function and callable(getattr(inspect_value, attr_name)):
                continue
            if not panel_options.display_attr_type_builtin and attr_name.startswith("__"):
                continue
            if not panel_options.display_attr_type_bl and attr_name.startswith("bl_"):
                continue
        # create item and set item info
        dir_item = ic_panel.dir_attributes.add()
        dir_item.name = attr_name
        item_value = getattr(inspect_value, attr_name)
        if item_value is None:
            dir_item.type_name = "None"
        else:
            dir_item.type_name = type(item_value).__name__
        dir_item.value_str = str(item_value)

def inspect_exec_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.window_manager.py_rec.inspect_context_collections)
    if ic_panel is None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because cannot get Inspect Panel"
    panel_options = ic_panel.panel_options
    if panel_options is None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because cannot get Inspect Panel Options"
    # clear index, and dir() attribute listing
    ic_panel.array_index_key_type = "none"
    ic_panel.array_index = 0
    ic_panel.array_index_max = 0
    ic_panel.array_key_set.clear()
    ic_panel.dir_inspect_exec_str = ""
    # clear label strings
    ic_panel.dir_item_value_str = ""
    ic_panel.dir_item_value_typename_str = ""
    ic_panel.dir_item_doc_lines.clear()

    # if Inspect Exec string is empty then quit
    if ic_panel.inspect_exec_str == "":
        return 'CANCELLED', "Unable to refresh Inspect Value, because Inspect Exec string is empty"

    # get total_exec_str, which includes pre-exec lines of code, if any
    post_exec_str = ic_panel.inspect_exec_str
    pre_exec_str = get_pre_exec_str(ic_panel)
    # get 'Inspect Exec' result value, and update label strings based on result
    inspect_value, inspect_error = refresh_inspect_exec_result(pre_exec_str, post_exec_str, True)
    if inspect_error != None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because exception raised during exec, see " \
            "details in log Text named '%s'" % LOG_TEXT_NAME

    ic_panel.dir_inspect_exec_str = ic_panel.inspect_exec_str

    # update index props
    if inspect_value != None and hasattr(inspect_value, "__len__") and len(inspect_value) > 0:
        # check for string type keys (for string type index)
        has_index_str = False
        if hasattr(inspect_value, "keys") and callable(inspect_value.keys):
            has_index_str = True
            # create list of strings (key names) for index string enum
            for key_name in inspect_value.keys():
                if not isinstance(key_name, str):
                    continue
                index_str_item = ic_panel.array_key_set.add()
                index_str_item.name = key_name
        # check for integer type index
        has_array_index = False
        try:
            _ = inspect_value[0]    # this line will raise exception if inspect_value cannot be indexed with integer
            # the following lines in the 'try' block will be run only if inspect_value can be indexed with integer
            has_array_index = True
            ic_panel.array_index_max = len(inspect_value)-1
            ic_panel.array_index = 0
        except:
            pass
        # set prop to indicate available index types
        if has_array_index and has_index_str:
            ic_panel.array_index_key_type = "int_str"
        elif has_array_index:
            ic_panel.array_index_key_type = "int"
        elif has_index_str:
            ic_panel.array_index_key_type = "str"
    # refresh attribute list after refreshing inspect value
    inspect_refresh_attribute_list(ic_panel)
    # set 'value' label
    ic_panel.dir_item_value_str = str(inspect_value)
    # set 'type name' label
    ic_panel.dir_item_value_typename_str = type(inspect_value).__name__
    # set '__doc__' lines
    string_to_lines_collection(get_relevant_doc(inspect_value), ic_panel.dir_item_doc_lines)
    return 'FINISHED', ""
