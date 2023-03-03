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
from bpy.utils import (register_class, unregister_class)

inspect_panel_classes = {}
PANEL_REGISTER_EXEC_STR = "class PYREC_PT_%s_Inspect%i(bpy.types.Panel):\n" \
      "    bl_space_type = '%s'\n" \
      "    bl_region_type = 'UI'\n" \
      "    bl_category = \"Tool\"\n" \
      "    bl_label = \"%s\"\n" \
      "    panel_num = %i\n" \
      "    def draw(self, context):\n" \
      "        if len(inspect_exec_panel_draw_func) > 0:\n" \
      "            inspect_exec_panel_draw_func[0](self, context)\n" \
      "register_class(PYREC_PT_%s_Inspect%i)\n" \
      "global inspect_panel_classes\n" \
      "inspect_panel_classes['PYREC_PT_%s_Inspect%i'] = PYREC_PT_%s_Inspect%i\n"

PANEL_UNREGISTER_EXEC_STR = "global inspect_panel_classes\n" \
                            "c = inspect_panel_classes[\"PYREC_PT_%s_Inspect%i\"]\n" \
                            "del inspect_panel_classes[\"PYREC_PT_%s_Inspect%i\"]\n" \
                            "unregister_class(c)\n"
inspect_exec_result = {}

inspect_exec_panel_draw_func = []

def register_inspect_exec_panel_draw_func(draw_func):
    # replace previous draw function, if any
    inspect_exec_panel_draw_func.clear()
    inspect_exec_panel_draw_func.append(draw_func)

def register_inspect_panel_exec(context, index, panel_label):
    context_name = context.space_data.type
    exec_str = PANEL_REGISTER_EXEC_STR % (context_name, index, context_name, panel_label, index, context_name, index,
                                          context_name, index, context_name, index)
    try:
        exec(exec_str)
    except:
        return False
    return True

def unregister_inspect_panel_exec(context, index):
    context_name = context.space_data.type
    if inspect_panel_classes.get("PYREC_PT_%s_Inspect%i" % (context_name, index)) is None:
        return
    # remove from list of classes before unregistering class, to prevent reference errors
    exec_str = PANEL_UNREGISTER_EXEC_STR % (context_name, index, context_name, index)
    try:
        exec(exec_str)
    except:
        return False
    return True

def unregister_all_inspect_panel_classes():
    for panel_class in inspect_panel_classes.values():
        unregister_class(panel_class)
    inspect_panel_classes.clear()

# returns 2-tuple of (output value, error string)
# error string is None if no error occurred during exec
def get_inspect_exec_result(inspect_exec_str):
    if inspect_exec_str == "":
        return None, "empty inspect exec string"
    ie_str = "global inspect_exec_result\ninspect_exec_result['result'] = %s" % inspect_exec_str
    try:
        exec(ie_str)
    except:
        return None, "exception raised during exec"
    r = inspect_exec_result["result"]
    del inspect_exec_result["result"]
    return r, None
