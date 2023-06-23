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
from bpy.types import UIList    # used in 'exec()'
from bpy.utils import (register_class, unregister_class)

from ..bpy_value_string import bpy_value_to_string
from ..exec_func import exec_get_result
from ..log_text import log_text_append
from ..py_code_utils import (get_commented_splitlines, get_dir, get_relevant_doc, remove_last_py_attribute)

INSPECT_PANEL_CLASS_MATCH_STR = "^PYREC_PT_[A-Za-z0-9_]+_Inspect[0-9]+$"

def set_array_index(self, value):
    if value < 0 or value > self.array_index_max:
        return
    self["array_index"] = value

def get_array_index(self):
    return self.get("array_index", 0)

def populate_index_strings(self, context):
    # if index string collection is not empty then create array for use with EnumProperty
    if len(self.array_key_set) > 0:
        output = []
        for index_str in self.array_key_set:
            output.append( (index_str.name, index_str.name, "") )
        return output
    # return empty
    return [ (" ", "", "") ]

def update_dir_attributes(self, value):
    panel_props = self
    panel_props.dir_item_doc_lines.clear()
    # quit if dir() listing is empty
    if len(panel_props.dir_attributes) < 1:
        return
    attr_name = panel_props.dir_attributes[panel_props.dir_attributes_index].name
    # get the current result value
    pre_exec_str = get_pre_exec_str(self)
    post_exec_str = self.dir_inspect_exec_str
    result_value, inspect_error = refresh_exec_inspect_value(pre_exec_str, post_exec_str)
    if inspect_error != None:
        return
    # get the current result attribute's value
    if attr_name == ".":
        attr_value = result_value
    elif result_value != None and hasattr(result_value, attr_name):
        attr_value = getattr(result_value, attr_name)
    else:
        attr_value = None
    # set '__doc__' label, if available as string type
    string_to_lines_collection(get_relevant_doc(attr_value), panel_props.dir_item_doc_lines)

def create_context_inspect_panel(context, context_name, inspect_context_collections, begin_exec_str=None):
    # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
    if context_name == "PROPERTIES":
        context_name = "VIEW_3D"
    panel_label = "Py Inspect"
    ic_coll = inspect_context_collections.get(context_name)
    if ic_coll is None:
        count = 0
    else:
        count = ic_coll.inspect_context_panel_next_num
        if count > 0:
            panel_label += "." + str(count).zfill(3)
    # create and register class for panel, to add panel to UI
    if not register_inspect_panel(context_name, count, panel_label):
        return False
    # if context does not have a panel collection yet, then create new panel collection and name it with context_name
    # (Py Inspect panels are grouped by context type/name, because panel classes are registered to context type)
    if ic_coll is None:
        ic_coll = inspect_context_collections.add()
        ic_coll.name = context_name
    # create new panel in collection
    i_panel = ic_coll.inspect_context_panels.add()
    i_panel.name = str(ic_coll.inspect_context_panel_next_num)
    ic_coll.inspect_context_panel_next_num = ic_coll.inspect_context_panel_next_num + 1
    i_panel.panel_label = panel_label
    i_panel.panel_options.panel_option_label = panel_label
    if begin_exec_str is None or begin_exec_str == "":
        return True
    i_panel.inspect_exec_str = begin_exec_str
    # do refresh using modified 'inspect_exec_str'
    ret_val, _ = inspect_exec_refresh(context, ic_coll.inspect_context_panel_next_num - 1)
    if ret_val == "FINISHED":
        return True
    return False

def inspect_datablock_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.window_manager.py_rec.inspect_context_collections)
    if ic_panel is None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because cannot get Inspect Panel"
    if ic_panel.inspect_datablock_name == "":
        return 'CANCELLED', "Unable to refresh Inspect Value, because Datablock is empty"
    ic_panel.inspect_exec_str = "bpy.data.%s[\"%s\"]" % (ic_panel.inspect_datablock_type,
                                                            ic_panel.inspect_datablock_name)
    return inspect_exec_refresh(context, panel_num)

def inspect_active_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.window_manager.py_rec.inspect_context_collections)
    if ic_panel is None:
        return 'CANCELLED', "Unable to refresh Inspect Active, because cannot get Inspect Panel"
    inspect_str = get_active_thing_inspect_str(context, ic_panel.inspect_active_type)
    if inspect_str == "":
        return 'CANCELLED', "Unable to refresh Inspect Active, because active thing not found in context type '%s'" % \
            context.space_data.type
    ic_panel.inspect_exec_str = inspect_str
    return inspect_exec_refresh(context, panel_num)

def inspect_attr_zoom_in(context, ic_panel, panel_num):
    attr_item = ic_panel.dir_attributes[ic_panel.dir_attributes_index]
    if attr_item is None:
        return
    attr_name = attr_item.name
    if attr_name == "" or attr_name == ".":
        return
    # zoom in to attribute
    ic_panel.inspect_exec_str = ic_panel.dir_inspect_exec_str + "." + attr_name
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

def inspect_zoom_out(context, ic_panel, panel_num):
    # try remove last attribute of inspect object, and if success, then update exec string and refresh attribute list
    first_part, _ = remove_last_py_attribute(ic_panel.dir_inspect_exec_str)
    if first_part is None:
        return
    ic_panel.inspect_exec_str = first_part
    inspect_exec_refresh(context, panel_num)

def inspect_array_index_zoom_in(context, ic_panel, panel_num):
    ic_panel.inspect_exec_str = "%s[%i]" % (ic_panel.dir_inspect_exec_str, ic_panel.array_index)
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

def inspect_array_key_zoom_in(context, ic_panel, panel_num):
    ic_panel.inspect_exec_str = "%s[\"%s\"]" % (ic_panel.dir_inspect_exec_str, ic_panel.array_key)
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

def restore_inspect_context_panels(inspect_context_collections):
    # unregister existing classes before restoring classes
    # i.e. in case previous .blend file had Inspect Panel classes registered, before next .blend file is loaded
    for attr_name in dir(bpy.types):
        if match_inspect_panel_name(attr_name):
            unregister_class(getattr(bpy.types, attr_name))
    # loop through stored contexts, and panels in each context, to ensure that each panel's class is registered,
    # because panel needs to be registered to be visible
    for icc in inspect_context_collections:
        context_name = icc.name
        # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
        if context_name == "PROPERTIES":
            context_name = "VIEW_3D"
        for icc_panel in icc.inspect_context_panels:
            # check if Py Inspect panel class has been registered
            if hasattr(bpy.types, "PYREC_PT_%s_Inspect%s" % (context_name, icc_panel.name)):
                continue
            # create and register class for panel, to add panel to UI
            register_inspect_panel(context_name, int(icc_panel.name), icc_panel.panel_label)

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

def match_inspect_panel_name(input_str):
    return re.match(INSPECT_PANEL_CLASS_MATCH_STR, input_str)

def get_action_fcurve_index(fcurves, data_path, array_index):
    for index in range(len(fcurves)):
        if fcurves[index].array_index == array_index and fcurves[index].data_path == data_path:
            return index
    return None

def get_inspect_active_type_items(self, context):
    if context is None or context.space_data is None:
        return [ (" ", "", "") ]
    # add 'Inspect Active' item(s) available in all contexts
    active_items = []
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

#### inspect_exec.py ####

# region_type = 'UI'
inspect_panel_classes = {}
INSPECT_PANEL_REGISTER = "class PYREC_PT_%s_Inspect%i(bpy.types.Panel):\n" \
    "    bl_space_type = '%s'\n" \
    "    bl_region_type = '%s'\n" \
    "    bl_category = \"Tool\"\n" \
    "    bl_label = \"%s\"\n" \
    "    panel_num = %i\n" \
    "    def draw(self, context):\n" \
    "        if len(inspect_panel_draw_func) > 0:\n" \
    "            inspect_panel_draw_func[0](self, context)\n" \
    "register_class(PYREC_PT_%s_Inspect%i)\n" \
    "global inspect_panel_classes\n" \
    "inspect_panel_classes['PYREC_PT_%s_Inspect%i'] = PYREC_PT_%s_Inspect%i\n"

inspect_panel_draw_func = []

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
    split = layout.split(factor=data.dir_col_size1)
    split.label(text=item.name)
    if panel_options.display_dir_attribute_type:
        if panel_options.display_dir_attribute_value:
            split = split.split(factor=data.dir_col_size2)
        split.label(text=item.type_name)
    if panel_options.display_dir_attribute_value:
        row = split.row()
        # display value selector, if possible
        if panel_options.display_value_selector and data.dir_inspect_exec_str != "" and item.name != "." and \
            not item.name.startswith("__") and item.name != "bl_rna":
            # get current inspect_value
            result_value = data.inspect_exec_state.get("exec_value")
            try:
                if result_value != None and hasattr(result_value, item.name):
                    attr_val = getattr(result_value, item.name)
                    # do not display if attribute value is None or if it is a zero-length list/tuple
                    if attr_val != None and not ( isinstance(attr_val, (list, tuple)) and len(attr_val) == 0) and \
                        not callable(attr_val):
                            row.prop(result_value, item.name, text="")
                            return
            except:
                pass
        # show value str if value selector not available
        row.label(text=item.value_str)

def register_inspect_panel_draw_func(draw_func):
    # replace previous draw function, if any
    inspect_panel_draw_func.clear()
    inspect_panel_draw_func.append(draw_func)

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
def refresh_exec_inspect_value(pre_exec_str, inspect_exec_str):
    if inspect_exec_str == "":
        return None, "Empty Inspect Exec string"
    result, is_exc, exc_msg = exec_get_result(pre_exec_str, inspect_exec_str)
    if is_exc:
        return None, "Exception raised by Inspect Exec of string:\n%s\n%s\n%s" % (pre_exec_str, inspect_exec_str,
                                                                                  exc_msg)
    else:
        return result, None

def inspect_refresh_attribute_list(ic_panel, inspect_value):
    panel_options = ic_panel.panel_options
    if panel_options is None:
        return
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
    dir_item.type_name = type(inspect_value).__name__
    dir_item.value_str = str(inspect_value)
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
    # clear '__doc__' lines
    ic_panel.dir_item_doc_lines.clear()

    ic_panel.inspect_exec_state.clear()

    # if Inspect Exec string is empty then quit
    if ic_panel.inspect_exec_str == "":
        return 'CANCELLED', "Unable to refresh Inspect Value, because Inspect Exec string is empty"

    # get pre-exec lines of code, if any
    pre_exec_str = get_pre_exec_str(ic_panel)
    post_exec_str = ic_panel.inspect_exec_str
    # get 'Inspect Exec' result value, and update label strings based on result
    inspect_value, inspect_error = refresh_exec_inspect_value(pre_exec_str, post_exec_str)
    if inspect_error != None:
        log_text = log_text_append(inspect_error)
        return 'CANCELLED', "Unable to refresh Inspect Value, because exception raised by exec, see details in " \
            "log Text named '%s'" % log_text.name
    ic_panel.dir_inspect_exec_str = ic_panel.inspect_exec_str

    ic_panel.inspect_exec_state["exec_value"] = inspect_value
    ic_panel.inspect_exec_state["exec_value_str"] = str(inspect_value)
    ic_panel.inspect_exec_state["exec_value_type"] = str(type(inspect_value))
    attr_names = set(get_dir(inspect_value))
    ic_panel.inspect_exec_state["exec_value_attr_names"] = attr_names
    ic_panel.inspect_exec_state["exec_value_attr_name_count"] = len(attr_names)

    # update index props
    if inspect_value != None and hasattr(inspect_value, "__len__"):
        # check for string type keys (for string type index)
        has_index_str = False
        if hasattr(inspect_value, "keys") and callable(inspect_value.keys):
            try:
                # create list of strings (key names) for index string enum
                for key_name in inspect_value.keys():
                    if not isinstance(key_name, str):
                        continue
                    index_str_item = ic_panel.array_key_set.add()
                    index_str_item.name = key_name
                    # locating following line of code in this 'for' loop ensures at least one key is added before
                    # setting this boolean to True
                    has_index_str = True
            except:
                pass
        # check for integer type index
        has_array_index = False
        try:
            _ = inspect_value[0]    # this line will raise exception if inspect_value cannot be indexed with integer
            # the following lines in the 'try' block will be run only if inspect_value can be indexed with integer
            ic_panel.array_index = 0
            ic_panel.array_index_max = len(inspect_value)-1
            has_array_index = True
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
    inspect_refresh_attribute_list(ic_panel, inspect_value)
    # set '__doc__' lines
    string_to_lines_collection(get_relevant_doc(inspect_value), ic_panel.dir_item_doc_lines)
    return 'FINISHED', ""

def apply_inspect_options(context, panel_num, ic_panel, panel_options, context_name):
    # check for change of panel name
    old_label = ic_panel.panel_label
    new_label = panel_options.panel_option_label
    if new_label != old_label:
        # unregister old panel
        unregister_inspect_panel(context_name, panel_num)
        # change prop to new label
        ic_panel.panel_label = panel_options.panel_option_label
        # register again with new label
        if not register_inspect_panel(context_name, panel_num, new_label):
            return 'CANCELLED', "Unable to change label of Py Inspect panel previously with label '%s'" % \
                        old_label
    # refresh the Attributes List
    inspect_exec_refresh(context, panel_num)
    return 'FINISHED', ""

def get_attribute_python_str(context, ic_panel, inspect_str, attr_name, attr_record_options):
    out_first_str = ""
    out_last_str = inspect_str if attr_name == "." else inspect_str + "." + attr_name
    pre_exec_str = get_pre_exec_str(ic_panel)
    post_exec_str = ic_panel.dir_inspect_exec_str
    result_value, inspect_error = refresh_exec_inspect_value(pre_exec_str, post_exec_str)
    if inspect_error != None:
        log_text = log_text_append(inspect_error)
        return 'CANCELLED', "Unable to refresh Inspect Value, because exception raised by exec, see details in " \
            "log Text named '%s'" % log_text.name
    if attr_name == ".":
        attr_value = result_value
    elif result_value != None and hasattr(result_value, attr_name):
        attr_value = getattr(result_value, attr_name)
    else:
        attr_value = None
    # append attribute value to output, if needed
    if attr_record_options.include_value:
        if attr_value is None:
            out_last_str += " = None\n"
        elif callable(attr_value):
            out_last_str += " # = %s\n" % str(attr_value)
        else:
            py_val_str = bpy_value_to_string(attr_value)
            if py_val_str is None:
                out_last_str += "  # = %s\n" % str(attr_value)
            else:
                out_last_str += " = %s\n" % py_val_str
    if attr_record_options.comment_type:
        out_first_str += "# Type: " + type(attr_value).__name__ + "\n"
    if attr_record_options.comment_doc:
        doc = get_relevant_doc(attr_value)
        if doc != None and doc != "":
            out_first_str += "# __doc__:\n" + get_commented_splitlines(doc)
    return 'FINISHED', out_first_str + out_last_str
