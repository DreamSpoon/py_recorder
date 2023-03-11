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

def get_action_fcurve_index(fcurves, data_path, array_index):
    for index in range(len(fcurves)):
        if fcurves[index].array_index == array_index and fcurves[index].data_path == data_path:
            return index
    return None

def get_inspect_active_type_items(self, context):
    active_items = []
    # add active_items based on context type, and available active things
    if context.space_data.type == "DOPESHEET_EDITOR":
        if context.active_action != None and context.space_data.ui_mode == "ACTION":
            active_items.append( ("active_action", "Action", "") )
    elif context.space_data.type == "GRAPH_EDITOR":
        if context.active_action != None:
            active_items.append( ("active_action", "Action", "") )
            if context.active_editable_fcurve != None:
                fcurve_index = get_action_fcurve_index(context.active_action.fcurves,
                                                       context.active_editable_fcurve.data_path,
                                                       context.active_editable_fcurve.array_index)
                if fcurve_index != None:
                    active_items.append( ("active_editable_fcurve", "Editable F-Curve", "") )
    elif context.space_data.type == "NLA_EDITOR":
        if context.active_object != None:
            active_items.append( ("active_object", "Object", "") )
            if context.active_nla_track != None:
                active_items.append( ("active_nla_track", "NLA Track", "") )
                if context.active_nla_strip != None:
                    active_items.append( ("active_nla_strip", "NLA Strip", "") )
    elif context.space_data.type == "NODE_EDITOR":
        if context.space_data.edit_tree != None:
            active_items.append( ("nodetree", "Nodetree", "") )
            if context.active_node != None:
                active_items.append( ("active_node", "Node", "") )
    elif context.space_data.type == "VIEW_3D":
        if context.active_object != None:
            active_items.append( ("active_object", "Object", "") )
            if context.active_object.type == "ARMATURE":
                active_items.append( ("armature", "Armature", "") )
            elif context.active_object.type == "CAMERA":
                active_items.append( ("camera", "Camera", "") )
            elif context.active_object.type == "LIGHT":
                active_items.append( ("light", "Light", "") )
            elif context.active_object.type == "MESH":
                active_items.append( ("mesh", "Mesh", "") )
            if context.active_bone != None:
                active_items.append( ("active_bone", "Bone", "") )
            if context.active_pose_bone != None:
                active_items.append( ("active_pose_bone", "Pose Bone", "") )
    # if active_items is empty then return empty list (list needs at least one item or exception will occur)
    if len(active_items) < 1:
        return [ (" ", "", "") ]
    return active_items

def get_active_thing_inspect_str(context, active_type):
    # check for empty (single space is checked because enum is used for active_type, and enum needs at least one item)
    if active_type == "" or active_type == " ":
        return ""
    # check active type and return active thing if available
    if active_type == "active_object" and context.active_object != None:
        return "bpy.data.objects[\"%s\"]" % context.active_object.name
    elif active_type == "armature" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.armatures[\"%s\"]" % context.active_object.data.name
    elif active_type == "camera" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.cameras[\"%s\"]" % context.active_object.data.name
    elif active_type == "light" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.lights[\"%s\"]" % context.active_object.data.name
    elif active_type == "mesh" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.meshes[\"%s\"]" % context.active_object.data.name
    elif active_type in ["active_action", "active_editable_fcurve"]:
        if context.active_action is None:
            return ""
        if active_type == "active_action":
            return "bpy.data.actions[\"%s\"]" % context.active_action.name
        else:
            fcurve_index = get_action_fcurve_index(context.active_action.fcurves,
                                                   context.active_editable_fcurve.data_path,
                                                   context.active_editable_fcurve.array_index)
            if fcurve_index != None:
                return "bpy.data.actions[\"%s\"].fcurves[%i]" % (context.active_action.name, fcurve_index)
    elif active_type in ["active_nla_track", "active_nla_strip"]:
        if context.active_object is None or context.active_nla_track is None:
            return ""
        inspect_str = "bpy.data.objects[\"%s\"].animation_data.nla_tracks[\"%s\"]" % (context.active_object.name,
                                                                                      context.active_nla_track.name)
        if active_type == "active_nla_track":
            return inspect_str
        if context.active_nla_strip != None:
            return inspect_str + (".strips[\"%s\"]" % context.active_nla_strip.name)
    elif active_type in ["nodetree", "active_node"]:
        if context.space_data.edit_tree is None:
            return ""
        if context.space_data.edit_tree.name in bpy.data.node_groups:
            inspect_str = "bpy.data.node_groups[\"%s\"]" % context.space_data.edit_tree.name
        elif isinstance(context.space_data.id, bpy.types.Material):
            inspect_str = "bpy.data.materials[\"%s\"].node_tree" % context.space_data.id.name
        else:
            return ""
        if active_type == "nodetree":
            return inspect_str
        if context.active_node != None:
            return inspect_str + (".nodes[\"%s\"]" % context.active_node.name)
    elif active_type in ["active_bone", "active_pose_bone"]:
        if context.active_object is None:
            return ""
        elif active_type == "active_bone":
            if context.active_bone != None and context.active_object.data != None:
                return "bpy.data.armatures[\"%s\"].bones[\"%s\"]" % (context.active_object.data.name,
                                                                     context.active_bone.name)
        elif active_type == "active_pose_bone":
            if context.active_pose_bone != None:
                return "bpy.data.objects[\"%s\"].pose.bones[\"%s\"]" % (context.active_object.name,
                                                                        context.active_pose_bone.name)
    return ""
