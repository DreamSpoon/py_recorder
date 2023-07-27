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

from ..bl_util import (get_addon_module_name, get_next_name)
from ..py_code_utils import is_valid_full_datapath
from .func import (PRESET_SOURCE_ADDON_PREFS, DUP_COLL_ACTION_RENAME, DUP_COLL_ACTION_REPLACE, digest_full_datapath,
    update_preset_prop_value, get_modify_active_preset_collection, get_modify_active_presets,
    get_modify_active_single_preset, get_source_preset_collections)

MODIFY_COLL_FUNC_MOVE = "MCF_MOVE"
MODIFY_COLL_FUNC_RENAME = "MCF_RENAME"
MODIFY_COLL_FUNC = [
    (MODIFY_COLL_FUNC_MOVE, "Move", "Move Preset Collection from one Data Source to another"),
    (MODIFY_COLL_FUNC_RENAME, "Rename", "Rename Preset Collection"),
    ]

MODIFY_PRESET_FUNC_COPY_TO_CLIPBOARD = "MPF_COPY_TO_CLIPBOARD"
MODIFY_PRESET_FUNC_MOVE = "MPF_MOVE"
MODIFY_PRESET_FUNC_RENAME = "MPF_RENAME"
MODIFY_PRESET_FUNC_UPDATE = "MPF_UPDATE"
MODIFY_PRESET_FUNC = [
    (MODIFY_PRESET_FUNC_COPY_TO_CLIPBOARD, "Copy to Clipboard", "Copy Preset data to Preset Clipboard, e.g. " \
     "combine multiple Presets"),
    (MODIFY_PRESET_FUNC_MOVE, "Move", "Move Preset to another Presets Collection"),
    (MODIFY_PRESET_FUNC_RENAME, "Rename", "Rename Preset"),
    (MODIFY_PRESET_FUNC_UPDATE, "Update", "Update Preset from data path"),
    ]

def modify_base_type_items(self, context):
    preset_collections = get_source_preset_collections(context)
    try:
        tps = preset_collections[context.window_manager.py_rec.preset_options.modify_options.active_collection].base_types
        # get list of type names ('bpy.types.' name)
        items = [ (t.name, t.name, "") for t in tps ]
        if len(items) > 0:
            return items
    except:
        pass
    return [ (" ", "", "") ]

def preset_collection_modify_rename(preset_options, preset_collections):
    new_name = preset_options.modify_options.collection_rename
    # quit if new_name is blank
    if new_name == "":
        return
    if len(preset_collections) > preset_options.modify_options.active_collection:
        # if name is already taken, then rename same named collection by appending '.001', etc.
        if new_name in preset_collections:
            old_p_coll = preset_collections[new_name]
            old_p_coll.name = get_next_name(new_name, preset_collections)
        # rename active collection
        p_coll = preset_collections[preset_options.modify_options.active_collection]
        p_coll.name = new_name

def preset_modify_rename(preset_options, preset_collections):
    new_name = preset_options.modify_options.preset_rename
    # quit if new_name is blank
    if new_name == "":
        return
    presets = get_modify_active_presets(preset_options, preset_collections)
    if presets != None:
        # if name is already taken, then rename same named Preset by appending '.001', etc.
        if new_name in presets:
            old_preset = presets[new_name]
            old_preset.name = get_next_name(new_name, presets)
        # rename active Preset
        preset = presets[preset_options.modify_options.active_preset]
        preset.name = new_name

def preset_remove_prop(preset_options, preset_collections):
    preset = get_modify_active_single_preset(preset_options, preset_collections)
    if preset is None:
        return
    prop_detail_name = preset.prop_details[preset_options.modify_options.active_detail].name
    prop_detail_type = preset.prop_details[preset_options.modify_options.active_detail].value_type
    # check value type to remove preset property value from correct collection
    if prop_detail_type == "bool":
        preset.bool_props.remove(preset.bool_props.find(prop_detail_name))
    elif prop_detail_type == "float":
        preset.float_props.remove(preset.float_props.find(prop_detail_name))
    elif prop_detail_type == "int":
        preset.int_props.remove(preset.int_props.find(prop_detail_name))
    elif prop_detail_type == "str":
        preset.string_props.remove(preset.string_props.find(prop_detail_name))
    elif prop_detail_type == "VectorEuler":
        preset.vector_euler_props.remove(preset.vector_euler_props.find(prop_detail_name))
    elif prop_detail_type == "VectorFloat3":
        preset.vector_float3_props.remove(preset.vector_float3_props.find(prop_detail_name))
    elif prop_detail_type == "VectorFloat4":
        preset.vector_float4_props.remove(preset.vector_float4_props.find(prop_detail_name))
    # remove preset property detail
    preset.prop_details.remove(preset_options.modify_options.active_detail)

def preset_collection_remove_collection(preset_options, preset_collections):
    modify_options = preset_options.modify_options
    if len(preset_collections) <= modify_options.active_collection:
        return
    preset_collections.remove(modify_options.active_collection)
    modify_options.active_collection -= 1
    if modify_options.active_collection < 0:
        modify_options.active_collection = 0

def preset_collection_remove_preset(preset_options, preset_collections):
    presets = get_modify_active_presets(preset_options, preset_collections)
    if presets is None:
        return
    modify_options = preset_options.modify_options
    presets.remove(modify_options.active_preset)
    modify_options.active_preset -= 1
    if modify_options.active_preset < 0:
        modify_options.active_preset = 0

def copy_preset_props(src_props, dest_props, dest_prop_details, value_type):
    for prop in src_props:
        new_prop = dest_props.add()
        new_prop.name = prop.name
        new_prop.value = prop.value
        new_detail = dest_prop_details.add()
        new_detail.name = prop.name
        new_detail.value_type = value_type

def copy_preset_to_base_type(src_preset, base_type, replace_preset):
    new_preset = base_type.presets.get(src_preset.name)
    if new_preset is None:
        new_preset = base_type.presets.add()
        new_preset.name = src_preset.name
    else:
        if replace_preset:
            base_type.presets.remove(src_preset.name)
            new_preset = base_type.presets.add()
            new_preset.name = src_preset.name
        # rename Preset, e.g. add .001
        else:
            next_name = get_next_name(src_preset.name, base_type.presets)
            new_preset = base_type.presets.add()
            new_preset.name = next_name
    copy_preset_props(src_preset.bool_props, new_preset.bool_props, new_preset.prop_details, "bool")
    copy_preset_props(src_preset.float_props, new_preset.float_props, new_preset.prop_details, "float")
    copy_preset_props(src_preset.int_props, new_preset.int_props, new_preset.prop_details, "int")
    copy_preset_props(src_preset.string_props, new_preset.string_props, new_preset.prop_details, "str")
    copy_preset_props(src_preset.vector_euler_props, new_preset.vector_euler_props, new_preset.prop_details,
                      "VectorEuler")
    copy_preset_props(src_preset.vector_float3_props, new_preset.vector_float3_props, new_preset.prop_details,
                      "VectorFloat3")
    copy_preset_props(src_preset.vector_float4_props, new_preset.vector_float4_props, new_preset.prop_details,
                      "VectorFloat4")

def preset_collection_modify_move(context, preset_options, dup_coll_action, replace_preset):
    if preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
        preset_collections = context.preferences.addons[get_addon_module_name()].preferences.preset_collections
        other_p_collections = context.window_manager.py_rec.preset_collections
    else:
        preset_collections = context.window_manager.py_rec.preset_collections
        other_p_collections = context.preferences.addons[get_addon_module_name()].preferences.preset_collections
    move_coll = get_modify_active_preset_collection(preset_options, preset_collections)
    if move_coll is None:
        return
    # get / create receiving Presets Collection in other Data Source
    new_coll = other_p_collections.get(move_coll.name)
    if new_coll is None:
        new_coll = other_p_collections.add()
        new_coll.name = move_coll.name
    else:
        if dup_coll_action == DUP_COLL_ACTION_RENAME:
            next_name = get_next_name(move_coll.name, new_coll)
            new_coll = other_p_collections.add()
            new_coll.name = next_name
        elif dup_coll_action == DUP_COLL_ACTION_REPLACE:
            other_p_collections.remove(other_p_collections.find(new_coll.name))
            new_coll = other_p_collections.add()
            new_coll.name = move_coll.name
        # else: Merge Collection
    # loop through base types, and their Presets, adding to / modifying 'new_coll' as needed
    for move_bt in move_coll.base_types:
        new_bt = new_coll.base_types.get(move_bt.name)
        if new_bt is None:
            new_bt = new_coll.base_types.add()
            new_bt.name = move_bt.name
        for move_preset in move_bt.presets:
            copy_preset_to_base_type(move_preset, new_bt, replace_preset)
    # remove original Presets Collection
    preset_collections.remove(preset_collections.find(move_coll.name))

update_preset_valid_datapath = []

def paste_full_datapath_to_update_preset(full_datapath, expected_type):
    update_preset_valid_datapath.clear()
    # remove leading/trailing whitespace
    full_datapath = full_datapath.strip()
    if not is_valid_full_datapath(full_datapath):
        return
    path_type_paths, _ = digest_full_datapath(full_datapath)
    # exit if no data for next steps
    if path_type_paths is None:
        return
    # get first available value that matches type and add to global result variable
    for base_path, type_name, _ in path_type_paths:
        if type_name == expected_type:
            update_preset_valid_datapath.append(base_path)
            return

def set_update_full_datapath(self, value):
    if self.get("update_full_datapath") is None:
        self["update_full_datapath"] = value
        return
    self["update_full_datapath"] = value
    paste_full_datapath_to_update_preset(value, bpy.context.window_manager.py_rec.preset_options.modify_options.base_type)

def get_update_full_datapath(self):
    return self.get("update_full_datapath", "")

def is_valid_update_datapath():
    return len(update_preset_valid_datapath) > 0

def update_preset(preset_options, preset_collections):
    if len(update_preset_valid_datapath) != 1:
        return
    preset = get_modify_active_single_preset(preset_options, preset_collections)
    if preset is None:
        return
    for prop_detail in preset.prop_details:
        # get base value for attribute searching
        exec_str = "import bpy\ndatapath_value = " + update_preset_valid_datapath[0]
        locals_dict = {}
        exec(exec_str, globals(), locals_dict)
        if locals_dict["datapath_value"] is None:
            continue
        # get ordered attribute list and recurse to get property value
        current_val = locals_dict["datapath_value"]
        attr_name_list = prop_detail.name.split(".")
        for attr_name in attr_name_list:
            if current_val is None:
                break
            if not hasattr(current_val, attr_name):
                current_val = None
                break
            current_val = getattr(current_val, attr_name)
        if current_val != None:
            update_preset_prop_value(preset, prop_detail.name, current_val)

def preset_move_to_collection_items(self, context):
    p_r = context.window_manager.py_rec
    if p_r.preset_options.modify_options.move_to_data_source == PRESET_SOURCE_ADDON_PREFS:
        source_collections = context.preferences.addons[get_addon_module_name()].preferences.preset_collections
    else:
        source_collections = p_r.preset_collections
    item_list = [ (p_coll.name, p_coll.name, "") for p_coll in source_collections ]
    return item_list if len(item_list) > 0 else [ (" ", "", "") ]

def move_active_preset(context, preset_options, preset_collections, replace_preset):
    move_preset = get_modify_active_single_preset(preset_options, preset_collections)
    if preset_options.modify_options.move_to_data_source == PRESET_SOURCE_ADDON_PREFS:
        move_to_collections = context.preferences.addons[get_addon_module_name()].preferences.preset_collections
    else:
        move_to_collections = context.window_manager.py_rec.preset_collections
    if not preset_options.modify_options.move_to_collection in move_to_collections:
        return
    move_to_coll = move_to_collections[preset_options.modify_options.move_to_collection]
    move_base_type_name = preset_options.modify_options.base_type
    # get or create base type as needed
    if move_base_type_name in move_to_coll.base_types:
        base_type = move_to_coll.base_types[move_base_type_name]
    else:
        base_type = move_to_coll.base_types.add()
        base_type.name = move_base_type_name
    copy_preset_to_base_type(move_preset, base_type, replace_preset)
    # remove original Preset after copying
    active_presets = get_modify_active_presets(preset_options, preset_collections)
    active_presets.remove(active_presets.find(move_preset.name))
    # remove empty base_types, i.e. when last Preset is removed from base_type
    active_coll = get_modify_active_preset_collection(preset_options, preset_collections)
    if len(active_coll.base_types[move_base_type_name].presets) == 0:
        active_coll.base_types.remove(active_coll.base_types.find(move_base_type_name))
