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

from .inspect_func import get_pre_exec_str
from ..log_text import log_text_append

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
    "        panel_options = data.panel_options\n" \
    "        pre_exec_str = get_pre_exec_str(data)\n" \
    "        split_denominator = 1\n" \
    "        if panel_options.display_dir_attribute_type:\n" \
    "            split_denominator = split_denominator + 1\n" \
    "        if panel_options.display_dir_attribute_value:\n" \
    "            split_denominator = split_denominator + 1\n" \
    "        split = layout.split(factor=1/split_denominator)\n" \
    "        split.label(text=item.name)\n" \
    "        if panel_options.display_dir_attribute_type:\n" \
    "            split.label(text=item.type_name)\n" \
    "        if panel_options.display_dir_attribute_value:\n" \
    "            row = split.row()\n" \
    "            # display value selector, if possible\n" \
    "            if panel_options.display_value_selector and data.dir_inspect_exec_str != \"\" and item.name != \".\" and \\\n" \
    "                not item.name.startswith(\"__\") and item.name != \"bl_rna\":\n" \
    "                result_value = get_inspect_exec_result()\n" \
    "                if result_value != None and hasattr(result_value, item.name):\n" \
    "                    attr_val = getattr(result_value, item.name)\n" \
    "                    # do not display if attribute value is None or if it is a zero-length list/tuple\n" \
    "                    if attr_val != None and not ( isinstance(attr_val, (list, tuple)) and len(attr_val) == 0) and \\\n" \
    "                        not callable(attr_val):\n" \
    "                        try:\n" \
    "                            row.prop(result_value, item.name, text=\"\")\n" \
    "                            return\n" \
    "                        except:\n" \
    "                            pass\n" \
    "            # show value str if value selector not available\n" \
    "            row.label(text=item.value_str)\n" \
    "register_class(PYREC_UL_%s_DirAttributeList%i)\n" \
    "global inspect_panel_classes\n" \
    "inspect_panel_classes['PYREC_UL_%s_DirAttributeList%i'] = PYREC_UL_%s_DirAttributeList%i\n"

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
