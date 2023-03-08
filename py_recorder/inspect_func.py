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

from .lex_py_attributes import lex_py_attributes

INSPECT_PANEL_CLASS_MATCH_STR = "^PYREC_PT_[A-Za-z0-9_]+_Inspect[0-9]+$"

# returns dir(val) without duplicates (e.g. '__doc__' duplicates)
def get_dir(val):
    temp_dict = {}
    for attr in dir(val):
        temp_dict[attr] = True
    return temp_dict.keys()

def get_inspect_context_panel(panel_num, context_name, inspect_context_collections):
    if panel_num < 0 or context_name == "" or inspect_context_collections is None:
        return None
    coll = inspect_context_collections.get(context_name)
    if coll is None:
        return None
    return coll.inspect_context_panels.get(str(panel_num))

# returns 2-tuple of (exec_str less last attribute, last attribute)
def remove_last_py_attribute(exec_str):
    output, e = lex_py_attributes(exec_str)
    # cannot remove last attribute if error, or no output, or too few output attributes
    if e != None or output is None or len(output) < 2:
        return None, None
    # use end_position of last output item to return exec_str up to, and including, end of second last attribute
    return exec_str[ : output[-2][1]+1 ], exec_str[ output[-1][0] : output[-1][1]+1 ]

def match_inspect_panel_name(input_str):
    return re.match(INSPECT_PANEL_CLASS_MATCH_STR, input_str)

def get_active_thing_name(context):
    if context.space_data.type == "VIEW_3D":
        if context.active_object is None:
            return ""
        if context.mode == "EDIT_ARMATURE":
            if context.active_bone != None:
                return context.active_bone.name
        elif context.mode == "POSE":
            if context.active_pose_bone != None:
                return context.active_pose_bone.name
        # default to OBJECT if mode is unknown
        return context.active_object.name
    elif context.space_data.type == "NODE_EDITOR":
        if context.active_node is None:
            return ""
        return context.active_node.name
    return ""

def get_active_thing_inspect_str(context):
    context_type = context.space_data.type
    active_object = context.active_object
    if context_type == "VIEW_3D":
        if active_object is None:
            return ""
        if context.mode == "EDIT_ARMATURE":
            if context.active_bone != None:
                return "bpy.data.armatures[\"%s\"].bones[\"%s\"]" % (active_object.data.name,
                                                                     context.active_bone.name)
        elif context.mode == "POSE":
            if context.active_pose_bone != None:
                return "bpy.data.objects[\"%s\"].pose.bones[\"%s\"]" % (active_object.name,
                                                                        context.active_pose_bone.name)
        # default to OBJECT if mode is unknown
        return "bpy.data.objects[\"%s\"]" % active_object.name
    elif context_type == "NODE_EDITOR":
        if context.active_node is None:
            return ""
        if context.space_data.edit_tree.name in bpy.data.node_groups:
            return "bpy.data.node_groups[\"%s\"].nodes[\"%s\"]" % (context.space_data.edit_tree.name,
                                                                   context.active_node.name)
        elif isinstance(context.space_data.id, bpy.types.Material):
            return "bpy.data.materials[\"%s\"].node_tree.nodes[\"%s\"]" % (context.space_data.id.name,
                                                                           context.active_node.name)
        else:
            return "bpy.context.active_node"
    return ""
