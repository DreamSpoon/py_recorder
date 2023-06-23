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

import re

import bpy
from bpy.types import Menu

from .operator import (PYREC_OT_AddInspectPanel, PYREC_OT_PyInspectActiveObject)
from .func import get_inspect_active_type_items

class PYREC_MT_InspectActive(Menu):
    bl_label = "Py Inspect Active"
    bl_idname = "PYREC_MT_InspectActive"

    def draw(self, context):
        layout = self.layout
        layout.label(text=str(context.space_data.type)+" context")
        for type_name, nice_name, _ in get_inspect_active_type_items(None, context):
            layout.operator(PYREC_OT_PyInspectActiveObject.bl_idname, text=nice_name).inspect_type = type_name

def draw_inspect_context_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(PYREC_OT_AddInspectPanel.bl_idname)

def draw_inspect_active_context_menu(self, context):
    layout = self.layout
    layout.menu(PYREC_MT_InspectActive.bl_idname)

def append_context_menu_all(draw_func, menu_list):
    for type_name in dir(bpy.types):
        # e.g. 'VIEW3D_MT_object_context_menu', 'NODE_MT_context_menu'
        if not re.match("^[A-Za-z0-9_]+_MT[A-Za-z0-9_]*_context_menu$", type_name):
            continue
        attr_value = getattr(bpy.types, type_name)
        if attr_value is None:
            continue
        try:
            attr_value.append(draw_func)
            menu_list.append(attr_value)
        except:
            pass

def remove_context_menu_all(draw_func, menu_list):
    for d in menu_list:
        d.remove(draw_func)
    menu_list.clear()

inspect_context_menu_removes = []
def append_inspect_context_menu_all():
    append_context_menu_all(draw_inspect_context_menu, inspect_context_menu_removes)

def remove_inspect_context_menu_all():
    remove_context_menu_all(draw_inspect_context_menu, inspect_context_menu_removes)

inspect_active_context_menu_removes = []
def append_inspect_active_context_menu_all():
    append_context_menu_all(draw_inspect_active_context_menu, inspect_active_context_menu_removes)

def remove_inspect_active_context_menu_all():
    remove_context_menu_all(draw_inspect_active_context_menu, inspect_active_context_menu_removes)
