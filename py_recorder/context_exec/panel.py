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
from bpy.utils import (register_class, unregister_class)

from .operator import PYREC_OT_ContextExec

exec_panel_classes = {}
EXEC_PANEL_REGISTER = "class PYREC_PT_%s_Exec(Panel):\n" \
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

def exec_panel_draw(self, context):
    pr_eo = context.window_manager.py_rec.context_exec_options
    layout = self.layout
    box = layout.box()
    box.prop(pr_eo, "exec_type")
    if pr_eo.exec_type == "single_line":
        box.prop(pr_eo, "single_line", text="")
    else:
        box.prop(pr_eo, "textblock", text="")
    box.operator(PYREC_OT_ContextExec.bl_idname)

def register_exec_panel(context_name):
    try:
        exec(EXEC_PANEL_REGISTER % (context_name, context_name, context_name, context_name, context_name))
    except:
        return False
#    exec(EXEC_PANEL_REGISTER % (context_name, context_name, context_name, context_name, context_name))
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
    'GRAPH_EDITOR', 'NLA_EDITOR', 'TEXT_EDITOR', 'SPREADSHEET')
exec_panels_registered = [ False ]
def append_exec_context_panel_all():
    if not exec_panels_registered[0]:
        for context_name in EXEC_CONTEXT_NAMES:
            register_exec_panel(context_name)
        exec_panels_registered[0] = True

def remove_exec_context_panel_all():
    if exec_panels_registered[0]:
        for context_name in EXEC_CONTEXT_NAMES:
            unregister_exec_panel(context_name)
        exec_panels_registered[0] = False
