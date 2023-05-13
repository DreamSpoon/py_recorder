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

import inspect
import re

import bpy
import mathutils

from .lex_py_attributes import lex_py_attributes

INSPECT_PANEL_CLASS_MATCH_STR = "^PYREC_PT_[A-Za-z0-9_]+_Inspect[0-9]+$"

# returns dir(val) without duplicates (e.g. '__doc__' duplicates)
def get_dir(val):
    temp_dict = {}
#    for attr in inspect.getmembers(val):
#        temp_dict[attr[0]] = True
    for attr in dir(val):
        temp_dict[attr] = True
    return temp_dict.keys()

# filter out values that do not have __doc__, and empty __doc__, then return clean doc
def get_relevant_doc(value):
    if value != None and not isinstance(value, (bool, dict, float, int, list, set, str, tuple, mathutils.Color,
        mathutils.Euler, mathutils.Matrix, mathutils.Quaternion, mathutils.Vector) ):
        return inspect.getdoc(value)
    return None

# split 'input_str' into separate lines, and add each line to 'lines_coll'
def string_to_lines_collection(input_str, lines_coll):
    if input_str is None or lines_coll is None:
        return
    for str_line in input_str.splitlines():
        new_item = lines_coll.add()
        new_item.name = str_line

def get_pre_exec_str(ic_panel):
    if ic_panel.pre_inspect_type == "single_line":
        return ic_panel.pre_inspect_single_line + "\n"
    elif ic_panel.pre_inspect_type == "textblock":
        if ic_panel.pre_inspect_text != None:
            return ic_panel.pre_inspect_text.as_string() + "\n"
    return ""

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
    if context is None or context.space_data is None:
        return [ (" ", "", "") ]
    # add 'Inspect Active' item(s) available in all contexts
    active_items.append( ("ACTIVE_SPACE_DATA", "Space Data", "") )
    active_items.append( ("CONTEXT", "Context", "") )
    active_items.append( ("SCENE", "Scene", "") )
    # add active_items based on context type, and available active things
    if context.space_data.type == "DOPESHEET_EDITOR":
        if context.active_action != None and context.space_data.ui_mode == "ACTION":
            active_items.append( ("ACTIVE_ACTION", "Action", "") )
    elif context.space_data.type == "GRAPH_EDITOR":
        if context.active_action != None:
            active_items.append( ("ACTIVE_ACTION", "Action", "") )
            if context.active_editable_fcurve != None:
                fcurve_index = get_action_fcurve_index(context.active_action.fcurves,
                                                       context.active_editable_fcurve.data_path,
                                                       context.active_editable_fcurve.array_index)
                if fcurve_index != None:
                    active_items.append( ("ACTIVE_EDITABLE_FCURVE", "Editable F-Curve", "") )
    elif context.space_data.type == "IMAGE_EDITOR":
        if context.space_data.image != None:
            active_items.append( ("IMAGE", "Image", "") )
        if context.space_data.mask != None:
            active_items.append( ("MASK", "Mask", "") )
    elif context.space_data.type == "NLA_EDITOR":
        if context.active_object != None:
            active_items.append( ("ACTIVE_OBJECT", "Object", "") )
            if context.active_nla_track != None:
                active_items.append( ("ACTIVE_NLA_TRACK", "NLA Track", "") )
                if context.active_nla_strip != None:
                    active_items.append( ("ACTIVE_NLA_STRIP", "NLA Strip", "") )
    elif context.space_data.type == "NODE_EDITOR":
        if context.space_data.edit_tree != None:
            active_items.append( ("NODE_TREE", "Node Tree", "") )
            if context.active_node != None:
                active_items.append( ("ACTIVE_NODE", "Node", "") )
        if isinstance(context.space_data.id, bpy.types.FreestyleLineStyle):
            active_items.append( ("LINE_STYLE", "Line Style", "") )
        elif isinstance(context.space_data.id, bpy.types.Material):
            active_items.append( ("MATERIAL", "Material", "") )
        elif isinstance(context.space_data.id, bpy.types.Texture):
            active_items.append( ("TEXTURE", "Texture", "") )
        elif isinstance(context.space_data.id, bpy.types.World):
            active_items.append( ("WORLD", "World", "") )
    elif context.space_data.type == "TEXT_EDITOR":
        if context.space_data.text != None:
            active_items.append( ("TEXT", "Text", "") )
    elif context.space_data.type == "VIEW_3D":
        if context.view_layer.active_layer_collection != None:
            active_items.append( ("COLLECTION", "Collection", "") )
        if context.active_object != None:
            active_items.append( ("ACTIVE_OBJECT", "Object", "") )
            if context.active_object.type == "ARMATURE":
                active_items.append( ("ARMATURE", "Armature", "") )
            elif context.active_object.type == "CAMERA":
                active_items.append( ("CAMERA", "Camera", "") )
            elif context.active_object.type in ["CURVE", "FONT"]:
                active_items.append( ("CURVE", "Curve", "") )
            elif context.active_object.type == "LATTICE":
                active_items.append( ("LATTICE", "Lattice", "") )
            elif context.active_object.type == "LIGHT":
                active_items.append( ("LIGHT", "Light", "") )
            elif context.active_object.type == "LIGHT_PROBE":
                active_items.append( ("LIGHT_PROBE", "Light Probe", "") )
            elif context.active_object.type == "MESH":
                active_items.append( ("MESH", "Mesh", "") )
                if context.active_object.vertex_groups.active_index != -1:
                    active_items.append( ("VERTEX_GROUP", "Vertex Group", "") )
                if context.active_object.data.uv_layers.active_index != -1:
                    active_items.append( ("UV_LAYER", "UV Map", "") )
                if context.active_object.active_shape_key != None:
                    active_items.append( ("SHAPE_KEY", "Shape Key", "") )
            elif context.active_object.type == "META":
                active_items.append( ("METABALL", "Metaball", "") )
            elif context.active_object.type == "SPEAKER":
                active_items.append( ("SPEAKER", "Speaker", "") )
            elif context.active_object.type == "VOLUME":
                active_items.append( ("VOLUME", "Volume", "") )
            if context.active_bone != None:
                active_items.append( ("ACTIVE_BONE", "Bone", "") )
            if context.active_pose_bone != None:
                active_items.append( ("ACTIVE_POSE_BONE", "Pose Bone", "") )
    elif context.space_data.type == "SEQUENCE_EDITOR":
        if context.active_sequence_strip != None:
            active_items.append( ("ACTIVE_SEQUENCE_STRIP", "Sequence Strip", "") )
    # if active_items is empty then return empty list (list needs at least one item or exception will occur)
    if len(active_items) < 1:
        return [ (" ", "", "") ]
    # sort items alphabetically, by 'display name', and return sorted array
    active_items.sort(key = lambda x: x[1])
    return active_items

def get_active_thing_inspect_str(context, active_type):
    # check for empty (single space is checked because enum is used for active_type, and enum needs at least one item)
    if active_type == "" or active_type == " ":
        return ""
    # check active type and return active thing if available
    if active_type == "CONTEXT":
        return "bpy.context"
    elif active_type == "ACTIVE_OBJECT" and context.active_object != None:
        return "bpy.data.objects[\"%s\"]" % context.active_object.name
    elif active_type == "ARMATURE" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.armatures[\"%s\"]" % context.active_object.data.name
    elif active_type == "CAMERA" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.cameras[\"%s\"]" % context.active_object.data.name
    elif active_type in [ "CURVE", "FONT" ] and context.active_object != None and context.active_object.data != None:
        return "bpy.data.curves[\"%s\"]" % context.active_object.data.name
    elif active_type == "LATTICE" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.lattices[\"%s\"]" % context.active_object.data.name
    elif active_type == "LIGHT" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.lights[\"%s\"]" % context.active_object.data.name
    elif active_type == "LIGHT_PROBE" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.lightprobes[\"%s\"]" % context.active_object.data.name
    elif active_type == "MESH" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.meshes[\"%s\"]" % context.active_object.data.name
    elif active_type == "METABALL" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.metaballs[\"%s\"]" % context.active_object.data.name
    elif active_type == "SCENE" and context.scene != None:
        return "bpy.data.scenes[\"%s\"]" % context.scene.name
    elif active_type == "SPEAKER" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.speakers[\"%s\"]" % context.active_object.data.name
    elif active_type == "VOLUME" and context.active_object != None and context.active_object.data != None:
        return "bpy.data.volumes[\"%s\"]" % context.active_object.data.name
    elif active_type in ["ACTIVE_ACTION", "ACTIVE_EDITABLE_FCURVE"]:
        if context.active_action is None:
            return ""
        if active_type == "ACTIVE_ACTION":
            return "bpy.data.actions[\"%s\"]" % context.active_action.name
        else:
            fcurve_index = get_action_fcurve_index(context.active_action.fcurves,
                                                   context.active_editable_fcurve.data_path,
                                                   context.active_editable_fcurve.array_index)
            if fcurve_index != None:
                return "bpy.data.actions[\"%s\"].fcurves[%i]" % (context.active_action.name, fcurve_index)
    elif active_type in ["ACTIVE_NLA_TRACK", "ACTIVE_NLA_STRIP"]:
        if context.active_object is None or context.active_nla_track is None:
            return ""
        inspect_str = "bpy.data.objects[\"%s\"].animation_data.nla_tracks[\"%s\"]" % (context.active_object.name,
                                                                                      context.active_nla_track.name)
        if active_type == "ACTIVE_NLA_TRACK":
            return inspect_str
        if context.active_nla_strip != None:
            return inspect_str + (".strips[\"%s\"]" % context.active_nla_strip.name)
    elif active_type in ["NODE_TREE", "ACTIVE_NODE"]:
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
        if active_type == "NODE_TREE":
            return inspect_str
        if context.active_node != None:
            return inspect_str + (".nodes[\"%s\"]" % context.active_node.name)
    elif active_type in ["ACTIVE_BONE", "ACTIVE_POSE_BONE"]:
        if context.active_object is None:
            return ""
        elif active_type == "ACTIVE_BONE":
            if context.active_bone != None and context.active_object.data != None:
                return "bpy.data.armatures[\"%s\"].bones[\"%s\"]" % (context.active_object.data.name,
                                                                     context.active_bone.name)
        elif active_type == "ACTIVE_POSE_BONE":
            if context.active_pose_bone != None:
                return "bpy.data.objects[\"%s\"].pose.bones[\"%s\"]" % (context.active_object.name,
                                                                        context.active_pose_bone.name)
    elif active_type == "COLLECTION":
        if context.view_layer.active_layer_collection != None:
            coll_name = context.view_layer.active_layer_collection.name
            coll = bpy.data.collections.get(coll_name)
            # check for 'Scene Collection', which is not in bpy.data.collections, rather it is part of Scene class
            if coll is None or coll == context.scene.collection:
                return "bpy.data.scenes[\"%s\"].collection" % context.scene.name
            return "bpy.data.collections[\"%s\"]" % coll_name
    elif active_type == "IMAGE":
        if context.space_data.image != None:
            return "bpy.data.images[\"%s\"]" % context.space_data.image.name
    elif active_type == "LINE_STYLE":
        if hasattr(context.space_data, "id") and isinstance(context.space_data.id, bpy.types.FreestyleLineStyle):
            return "bpy.data.linestyles[\"%s\"]" % context.space_data.id.name
    elif active_type == "MASK":
        if context.space_data.mask != None:
            return "bpy.data.masks[\"%s\"]" % context.space_data.mask.name
    elif active_type == "MATERIAL":
        if hasattr(context.space_data, "id") and isinstance(context.space_data.id, bpy.types.Material):
            return "bpy.data.materials[\"%s\"]" % context.space_data.id.name
    elif active_type == "SHAPE_KEY":
        if context.active_object != None and context.active_object.data != None and \
            context.active_object.active_shape_key != None:
            return "bpy.data.shape_keys[\"%s\"].key_blocks[\"%s\"]" % (context.active_object.data.shape_keys.name,
                context.active_object.active_shape_key.name)
    elif active_type == "TEXTURE":
        if hasattr(context.space_data, "id") and isinstance(context.space_data.id, bpy.types.Texture):
            return "bpy.data.textures[\"%s\"]" % context.space_data.id.name
    elif active_type == "TEXT":
        if context.space_data.text != None:
            return "bpy.data.texts[\"%s\"]" % context.space_data.text.name
    elif active_type == "UV_LAYER":
        if context.active_object != None and context.active_object.data != None and \
            context.active_object.data.uv_layers.active_index != -1:
            return "bpy.data.meshes[\"%s\"].uv_layers[\"%s\"]" % (context.active_object.data.name,
                context.active_object.data.uv_layers[context.active_object.data.uv_layers.active_index].name)
    elif active_type == "VERTEX_GROUP":
        if context.active_object != None and context.active_object.vertex_groups.active_index != -1:
            return "bpy.data.objects[\"%s\"].vertex_groups[\"%s\"]" % (context.active_object.name,
                context.active_object.vertex_groups[context.active_object.vertex_groups.active_index].name)
    elif active_type == "WORLD":
        if isinstance(context.space_data.id, bpy.types.World):
            return "bpy.data.worlds[\"%s\"]" % context.space_data.id.name
    elif active_type == "ACTIVE_SEQUENCE_STRIP":
        if context.active_sequence_strip != None:
            return "bpy.data.scenes[\"%s\"].sequence_editor.sequences_all[\"%s\"]" % \
                (context.scene.name, context.active_sequence_strip.name)
    elif active_type == "ACTIVE_SPACE_DATA":
        if context.space_data != None:
            return "bpy.context.space_data"
    return ""
