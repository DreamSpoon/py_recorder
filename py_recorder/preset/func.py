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

from mathutils import Vector

import bpy

from ..bl_util import get_addon_module_name
from ..py_code_utils import (enumerate_datapath_hierarchy, trim_datapath, get_value_type_name, is_bpy_type_name)

# Data related to Presets and Preset Collections can be stored in one of two places:
#  - .blend File
#  - Blender Addon Preferences (Py Recorder Addon Preferences)
PRESET_SOURCE_BLEND_FILE = "PS_BLEND_FILE"
PRESET_SOURCE_ADDON_PREFS = "PS_ADDON_PREFS"
PRESET_SOURCE_TYPES = [
    (PRESET_SOURCE_BLEND_FILE, ".blend file", "Presets saved in current .blend file"),
    (PRESET_SOURCE_ADDON_PREFS, "Blender Preferences", "Presets saved in Blender Addon Preferences (Py Recorder " \
        "Addon Preferences)")
    ]

# Preset View ideas:
#   Explore - Simplified 'Py Inspect', to allow adding properties 'sideways' from a given property:
#              i.e. use dir() with parent attribute of property, and compare attribute value types to
#              (bool, float, int, str, etc.), to get more known attributes for Preset
#   Create - Clipboard for 'Copy Full Data Path', with multiple entries, to allow for easy creation of Preset
#   Modify - Manage Preset Presets and Presets Collections, each Collection contains zero or more Presets.
#                Delete Preset / Delete Preset Collection here, and only here - with optional pop-up for
#                confirmation of delete operation.
#   Apply - Past a copied full datapath, select the base type, and apply a preset (copy values) to the
#           properties of the base type value.
PRESET_VIEW_APPLY = "PV_APPLY"
PRESET_VIEW_MODIFY = "PV_PRESET_MODIFY"
PRESET_VIEW_CLIPBOARD = "PV_CLIPBOARD"
PRESET_VIEW_IMPORT_EXPORT = "PV_IMPORT_EXPORT"
PRESET_VIEW_TYPES = [
    (PRESET_VIEW_APPLY, "Apply", "Apply Preset"),
    (PRESET_VIEW_MODIFY, "Modify", "Modify Presets and Preset Collections"),
    (PRESET_VIEW_CLIPBOARD, "Clipboard", "Add Property datapath(s) to Property Clipboard, then create Preset"),
    (PRESET_VIEW_IMPORT_EXPORT, "Import/Export", "Import Presets Collections from .py files, and export Presets " \
     "Collections to .py files")
    ]

DUP_COLL_ACTION_MERGE = "DUP_COLL_ACTION_MERGE"
DUP_COLL_ACTION_RENAME = "DUP_COLL_ACTION_RENAME"
DUP_COLL_ACTION_REPLACE = "DUP_COLL_ACTION_REPLACE"
DUP_COLL_ACTION_ITEMS = [
    (DUP_COLL_ACTION_MERGE, "Merge", "Collections with duplicate names will be merged"),
    (DUP_COLL_ACTION_RENAME, "Rename", "Collections with duplicate names will be renamed (new Collections " \
     "renamed), e.g. append .001"),
    (DUP_COLL_ACTION_REPLACE, "Replace", "Collections with duplicate names will be replaced (old Collections " \
     "replaced with new Collections)"),
    ]

# get available base type path, and base type name, and the property path that extends from bast type path to
# full property datapath:
#   -base type must be from 'bpy.types.*' (also known as 'bpy_types.*')
#   -property must not be from 'bpy.types.*', and property must be in list of known types/sub-types, and
#    property attribute must be preceded by 'bpy.types.*' attribute
def digest_full_datapath(full_datapath, all_bpy_types=False):
    # get full datapath hierarchy
    path_hierarchy = enumerate_datapath_hierarchy(full_datapath)
    # check values at different levels of full datapath hierarchy for type, to determine which base types (nested
    # types allowed) are available and property paths that would go along with each base type (nested types allowed)
    prev_attr_bpy_type = False
    used_bpy_type_names = { '' }
    base_type_chain = []
    prop_path = ""
    prop_value = None
    for prog_datapath in path_hierarchy:
        val = eval(prog_datapath)
        val_type_name = get_value_type_name(val)
        # if 'bpy.types.*' type is found then add to base_type_chain
        if is_bpy_type_name(val_type_name) and val_type_name[10:] != "BlendData":
            prev_attr_bpy_type = True
            # if over-ride (allow all 'bpy.types.*') then add to base type chain
            if all_bpy_types:
                base_type_chain.append( (prog_datapath, val_type_name[10:]) )
            # - if this type has been used previously in hierarchy, then reset base_type_chain and used_bpy_type_names
            #   - this prevents a kind of circular base_type_chain:
            #     e.g.
            #       bpy.data.meshes['Cube'].vertices[0].id_data.vertices[0].co
            #     because 'id_data' references:
            #       bpy.data.meshes['Cube']
            #   - in Blender, 'id_data' attribute of certain value types will point to a parent in the 'bpy.data.*'
            #     hierarchy
            elif val_type_name in used_bpy_type_names:
                # hard reset
                base_type_chain = []
                used_bpy_type_names = { '' }
            # - also, if datapath item ends with "]" then it is an indexed variable, so reset base_type_chain to
            #   current prog_datapath
            elif prog_datapath[:-1] == "]":
                # soft reset
                base_type_chain = [ (prog_datapath, val_type_name[10:]) ]
                used_bpy_type_names = { val_type_name }
            else:
                # add
                base_type_chain.append( (prog_datapath, val_type_name[10:]) )
                used_bpy_type_names |= { val_type_name }
            prop_path = ""
            prop_value = None
        # if known property value type is found then exit for loop
        elif isinstance(val, (bool, float, int, str)) or ( isinstance(val, Vector) and len(val) == 3 ):
            if prev_attr_bpy_type:
                prop_path = prog_datapath
                prop_value = val
            break
        # unknown value type, so reset all except used_bpy_type_names, no reset if 'all bpy. types' enabled
        elif not all_bpy_types:
            prev_attr_bpy_type = False
            base_type_chain = []
            prop_path = ""
            prop_value = None
    # exit if property not available or base type not available
    if (prop_path == "" and not all_bpy_types) or len(base_type_chain) == 0:
        return None, None
    result = []
    for bt_path, bt_name in base_type_chain:
        # start from second character to remove '.' at start of string
        if prop_path == "":
            result.append( (bt_path, bt_name, "" ) )
        elif prop_path[len(bt_path)] == ".":
            result.append( (bt_path, bt_name, prop_path[len(bt_path)+1:] ) )
        else:
            result.append( (bt_path, bt_name, prop_path[len(bt_path):] ) )
    return result, prop_value

# on error: returns None
# on success: returns tuple of (prop_value, prop_value_string)
def get_preset_prop_value_str(preset, prop_name):
    prop_detail = preset.prop_details.get(prop_name)
    if prop_detail is None:
        return None
    if prop_detail.value_type == "bool":
        prop_value = preset.bool_props[prop_detail.name].value
        return ( prop_value, str(prop_value) )
    elif prop_detail.value_type == "float":
        prop_value = preset.float_props[prop_detail.name].value
        return ( prop_value, str(prop_value) )
    elif prop_detail.value_type == "int":
        prop_value = preset.int_props[prop_detail.name].value
        return ( prop_value, str(prop_value) )
    elif prop_detail.value_type == "str":
        prop_value = preset.string_props[prop_detail.name].value
        return ( prop_value, '"' + prop_value + '"' )
    elif prop_detail.value_type == "VectorXYZ":
        prop_value = preset.vector_xyz_props[prop_detail.name].value
        return ( prop_value, "(%f, %f, %f)" % prop_value )
    else:
        return None

# on success: returns True
# on error: returns False
def update_preset_prop_value(preset, prop_name, new_value):
    prop_detail = preset.prop_details.get(prop_name)
    if prop_detail is None:
        return False
    if prop_detail.value_type == "bool" and isinstance(new_value, bool):
        preset.bool_props[prop_detail.name].value = new_value
    elif prop_detail.value_type == "float" and isinstance(new_value, float):
        preset.float_props[prop_detail.name].value = new_value
    elif prop_detail.value_type == "int" and isinstance(new_value, int):
        preset.int_props[prop_detail.name].value = new_value
    elif prop_detail.value_type == "str" and isinstance(new_value, str):
        preset.string_props[prop_detail.name].value = new_value
    elif prop_detail.value_type == "VectorXYZ" and isinstance(new_value, Vector):
        preset.vector_xyz_props[prop_detail.name].value = new_value
    else:
        return False
    return True

def get_source_preset_collections(context):
    p_r = context.window_manager.py_rec
    if p_r.preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
        return context.preferences.addons[get_addon_module_name()].preferences.preset_collections
    else:
        return p_r.preset_collections

def get_modify_active_preset_collection(preset_options, preset_collections):
    if len(preset_collections) <= preset_options.modify_options.active_collection:
        return None
    return preset_collections[preset_options.modify_options.active_collection]

def get_modify_active_presets(preset_options, preset_collections):
    p_coll = get_modify_active_preset_collection(preset_options, preset_collections)
    if p_coll is None:
        return None
    base_type = p_coll.base_types.get(preset_options.modify_options.base_type)
    if base_type is None:
        return None
    return base_type.presets

def get_modify_active_single_preset(preset_options, preset_collections):
    presets = get_modify_active_presets(preset_options, preset_collections)
    if presets is None or len(presets) <= preset_options.modify_options.active_preset:
        return None
    return presets[preset_options.modify_options.active_preset]
