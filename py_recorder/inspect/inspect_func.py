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
    # panel classes in "Properties" context are shared with "View3D" context
    if context_name == "PROPERTIES":
        context_name = "VIEW_3D"
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
    elif context.space_data.type == "IMAGE_EDITOR":
        if context.space_data.image != None:
            active_items.append( ("image", "Image", "") )
        if context.space_data.mask != None:
            active_items.append( ("mask", "Mask", "") )
    elif context.space_data.type == "NLA_EDITOR":
        if context.active_object != None:
            active_items.append( ("active_object", "Object", "") )
            if context.active_nla_track != None:
                active_items.append( ("active_nla_track", "NLA Track", "") )
                if context.active_nla_strip != None:
                    active_items.append( ("active_nla_strip", "NLA Strip", "") )
    elif context.space_data.type == "NODE_EDITOR":
        if context.space_data.edit_tree != None:
            active_items.append( ("node_tree", "Node Tree", "") )
            if context.active_node != None:
                active_items.append( ("active_node", "Node", "") )
        if isinstance(context.space_data.id, bpy.types.FreestyleLineStyle):
            active_items.append( ("line_style", "Line Style", "") )
        elif isinstance(context.space_data.id, bpy.types.Material):
            active_items.append( ("material", "Material", "") )
        elif isinstance(context.space_data.id, bpy.types.Texture):
            active_items.append( ("texture", "Texture", "") )
        elif isinstance(context.space_data.id, bpy.types.World):
            active_items.append( ("world", "World", "") )
    elif context.space_data.type == "TEXT_EDITOR":
        if context.space_data.text != None:
            active_items.append( ("text", "Text", "") )
    elif context.space_data.type == "VIEW_3D":
        if context.view_layer.active_layer_collection != None:
            active_items.append( ("collection", "Collection", "") )
        if context.active_object != None:
            active_items.append( ("active_object", "Object", "") )
            if context.active_object.type == "ARMATURE":
                active_items.append( ("armature", "Armature", "") )
            elif context.active_object.type == "CAMERA":
                active_items.append( ("camera", "Camera", "") )
            elif context.active_object.type in ["CURVE", "FONT"]:
                active_items.append( ("curve", "Curve", "") )
            elif context.active_object.type == "LIGHT":
                active_items.append( ("light", "Light", "") )
            elif context.active_object.type == "LATTICE":
                active_items.append( ("lattice", "Lattice", "") )
            elif context.active_object.type == "LIGHT_PROBE":
                active_items.append( ("light_probe", "Light Probe", "") )
            elif context.active_object.type == "MESH":
                active_items.append( ("mesh", "Mesh", "") )
                if context.active_object.vertex_groups.active_index != -1:
                    active_items.append( ("vertex_group", "Vertex Group", "") )
                if context.active_object.data.uv_layers.active_index != -1:
                    active_items.append( ("uv_layer", "UV Map", "") )
                if context.active_object.active_shape_key != None:
                    active_items.append( ("shape_key", "Shape Key", "") )
            elif context.active_object.type == "META":
                active_items.append( ("metaball", "Metaball", "") )
            elif context.active_object.type == "SPEAKER":
                active_items.append( ("speaker", "Speaker", "") )
            elif context.active_object.type == "VOLUME":
                active_items.append( ("volume", "Volume", "") )
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
    elif active_type == "curve" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.curves[\"%s\"]" % context.active_object.data.name
    elif active_type == "light" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.lights[\"%s\"]" % context.active_object.data.name
    elif active_type == "lattice" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.lattices[\"%s\"]" % context.active_object.data.name
    elif active_type == "light_probe" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.lightprobes[\"%s\"]" % context.active_object.data.name
    elif active_type == "mesh" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.meshes[\"%s\"]" % context.active_object.data.name
    elif active_type == "metaball" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.metaballs[\"%s\"]" % context.active_object.data.name
    elif active_type == "speaker" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.speakers[\"%s\"]" % context.active_object.data.name
    elif active_type == "volume" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.volumes[\"%s\"]" % context.active_object.data.name
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
    elif active_type in ["node_tree", "active_node"]:
        if context.space_data.edit_tree is None:
            return ""
        if isinstance(context.space_data.id, bpy.types.FreestyleLineStyle):
            inspect_str = "bpy.data.linestyles[\"%s\"].node_tree" % context.space_data.id.name
        elif isinstance(context.space_data.id, bpy.types.Material):
            inspect_str = "bpy.data.materials[\"%s\"].node_tree" % context.space_data.id.name
        elif isinstance(context.space_data.id, bpy.types.Scene):    # compositor nodetree
            inspect_str = "bpy.data.scenes[\"%s\"].node_tree" % context.space_data.id.name
        elif isinstance(context.space_data.id, bpy.types.Texture):
            inspect_str = "bpy.data.textures[\"%s\"].node_tree" % context.space_data.id.name
        elif isinstance(context.space_data.id, bpy.types.World):
            inspect_str = "bpy.data.worlds[\"%s\"].node_tree" % context.space_data.id.name
        elif context.space_data.edit_tree.name in bpy.data.node_groups:
            inspect_str = "bpy.data.node_groups[\"%s\"]" % context.space_data.edit_tree.name
        else:
            return ""
        if active_type == "node_tree":
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
    elif active_type == "collection":
        if context.view_layer.active_layer_collection != None:
            coll_name = context.view_layer.active_layer_collection.name
            coll = bpy.data.collections.get(coll_name)
            # check for 'Scene Collection', which is not in bpy.data.collections, rather it is part of Scene class
            if coll is None or coll == context.scene.collection:
                return "bpy.data.scenes[\"%s\"].collection" % context.scene.name
            return "bpy.data.collections[\"%s\"]" % coll_name
    elif active_type == "image":
        if context.space_data.image != None:
            return "bpy.data.images[\"%s\"]" % context.space_data.image.name
    elif active_type == "line_style":
        if hasattr(context.space_data, "id") and isinstance(context.space_data.id, bpy.types.FreestyleLineStyle):
            return "bpy.data.linestyles[\"%s\"]" % context.space_data.id.name
    elif active_type == "mask":
        if context.space_data.mask != None:
            return "bpy.data.masks[\"%s\"]" % context.space_data.mask.name
    elif active_type == "material":
        if hasattr(context.space_data, "id") and isinstance(context.space_data.id, bpy.types.Material):
            return "bpy.data.materials[\"%s\"]" % context.space_data.id.name
    elif active_type == "shape_key":
        if context.active_object != None and context.active_object.data != None and \
            context.active_object.active_shape_key != None:
            return "bpy.data.shape_keys[\"%s\"].key_blocks[\"%s\"]" % (context.active_object.data.shape_keys.name,
                context.active_object.active_shape_key.name)
    elif active_type == "texture":
        if hasattr(context.space_data, "id") and isinstance(context.space_data.id, bpy.types.Texture):
            return "bpy.data.textures[\"%s\"]" % context.space_data.id.name
    elif active_type == "text":
        if context.space_data.text != None:
            return "bpy.data.texts[\"%s\"]" % context.space_data.text.name
    elif active_type == "uv_layer":
        if context.active_object != None and context.active_object.data != None and \
            context.active_object.data.uv_layers.active_index != -1:
            return "bpy.data.meshes[\"%s\"].uv_layers[\"%s\"]" % (context.active_object.data.name,
                context.active_object.data.uv_layers[context.active_object.data.uv_layers.active_index].name)
    elif active_type == "vertex_group":
        if context.active_object != None and context.active_object.vertex_groups.active_index != -1:
            return "bpy.data.objects[\"%s\"].vertex_groups[\"%s\"]" % (context.active_object.name,
                context.active_object.vertex_groups[context.active_object.vertex_groups.active_index].name)
    return ""
