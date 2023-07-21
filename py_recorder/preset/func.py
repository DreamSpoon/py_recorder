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

import ast
import traceback

import bpy
from mathutils import Vector

from ..log_text import log_text_append
from ..py_code_utils import (enumerate_datapath_hierarchy, trim_datapath)

PREFS_ADDONS_NAME = "py_recorder"

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
#PRESET_VIEW_EXPLORE = "PV_EXPLORE"
PRESET_VIEW_TYPES = [
    (PRESET_VIEW_APPLY, "Apply", "Apply Preset"),
    (PRESET_VIEW_MODIFY, "Modify", "Modify Presets and Preset Collections"),
    (PRESET_VIEW_CLIPBOARD, "Clipboard", "Add Property datapath(s) to Property Clipboard, then create Preset"),
    (PRESET_VIEW_IMPORT_EXPORT, "Import/Export", "Import Presets Collections from .py files, and export Presets " \
     "Collections to .py files")
#    (PRESET_VIEW_EXPLORE, "Explore", ""),
    ]

MODIFY_COLL_FUNC_RENAME = "MCF_RENAME"
MODIFY_COLL_FUNC = [
    (MODIFY_COLL_FUNC_RENAME, "Rename", "Rename Preset Collection"),
#    (),
    ]

MODIFY_PRESET_FUNC_RENAME = "MPF_RENAME"
MODIFY_PRESET_FUNC_COPY_TO_CLIPBOARD = "MPF_COPY_TO_CLIPBOARD"
MODIFY_PRESET_FUNC = [
    (MODIFY_PRESET_FUNC_RENAME, "Rename", "Rename Preset"),
    (MODIFY_PRESET_FUNC_COPY_TO_CLIPBOARD, "Copy to Clipboard", "Copy Preset data to Preset Clipboard, e.g. " \
     "combine multiple Presets"),
    ]

IMPEXP_DUP_COLL_MERGE = "IMPEXP_DUP_COLL_MERGE"
IMPEXP_DUP_COLL_RENAME = "IMPEXP_DUP_COLL_RENAME"
IMPEXP_DUP_COLL_REPLACE = "IMPEXP_DUP_COLL_REPLACE"
IMPEXP_DUP_COLL_ITEMS = [
    (IMPEXP_DUP_COLL_MERGE, "Merge", "Collections with duplicate names will be merged"),
    (IMPEXP_DUP_COLL_RENAME, "Rename", "Collections with duplicate names will be renamed (new Collections " \
     "renamed), e.g. append .001"),
    (IMPEXP_DUP_COLL_REPLACE, "Replace", "Collections with duplicate names will be replaced (old Collections " \
     "replaced with new Collections)"),
    ]

# returns true if test_str starts with 'bpy.data.' (Blender data collection test) and 'test_str' can be evaluated in
# Python (try to use eval() )
def is_valid_full_datapath(test_str):
    try:
        if test_str.startswith("bpy.data."):
            # trim_datapath will remove '=' assignment, if needed, from 'test_str', before using eval()
            #   - do this to prevent assigning values to properties during test for valid full data path
            eval(trim_datapath(test_str))
            return True
        return False
    except:
        return False

# get name of class of value
def get_value_type_name(value):
    raw_name = str(type(value))
    if raw_name.startswith("<class '") and raw_name.endswith("'>"):
        return raw_name[8:-2]
    return ""

# test if value's type name begins with "bpy_types.", because this indicates that value's type is in 'bpy.types'
def is_bpy_type_name(t_name):
    return t_name.startswith("bpy.types.") or t_name.startswith("bpy_types.")

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

def create_clipboard_line(clipboard, full_datapath, path_type_paths, prop_value):
    # create new detail
    prop_detail = clipboard.prop_details.add()
    prop_detail.name = full_datapath
    first_bt_name = ""
    for _, bt_name, prop_path in path_type_paths:
        if first_bt_name == "":
            first_bt_name = bt_name
        abt = prop_detail.available_base_types.add()
        abt.name = bt_name
        abt.value = prop_path
    prop_detail.base_type = first_bt_name
    # create new property in type-specific property collection
    if isinstance(prop_value, bool):
        p = clipboard.bool_props.add()
        prop_detail.value_type = "bool"
    elif isinstance(prop_value, float):
        p = clipboard.float_props.add()
        prop_detail.value_type = "float"
    elif isinstance(prop_value, int):
        p = clipboard.int_props.add()
        prop_detail.value_type = "int"
    elif isinstance(prop_value, str):
        p = clipboard.string_props.add()
        prop_detail.value_type = "str"
    elif isinstance(prop_value, Vector) and len(prop_value) == 3:
        p = clipboard.vector_xyz_props.add()
        prop_detail.value_type = "VectorXYZ"
    else:
        return
    # link type-specific property to prop_detail with 'full_datapath'
    p.name = full_datapath
    # set value of new property in Preset
    p.value = prop_value

def paste_full_datapath_to_clipboard(full_datapath):
    # remove leading/trailing whitespace
    full_datapath = full_datapath.strip()
    if not is_valid_full_datapath(full_datapath):
        return
    clipboard = bpy.context.window_manager.py_rec.preset_options.clipboard
    # if same datapath is already in clipboard, then exit to prevent adding duplicates
    if full_datapath in clipboard.prop_details:
        return
    path_type_paths, prop_value = digest_full_datapath(full_datapath)
    # exit if no data for next steps
    if path_type_paths is None:
        return
    create_clipboard_line(clipboard, full_datapath, path_type_paths, prop_value)

def set_input_full_datapath(self, value):
    if self.get("input_full_datapath") is None:
        self["input_full_datapath"] = value
        return

    self["input_full_datapath"] = value
    # remove leading/trailing whitespace before testing/setting active full data path
    paste_full_datapath_to_clipboard(value)

def get_input_full_datapath(self):
    return self.get("input_full_datapath", "")

def create_base_type_items(self, context):
    available_base_types = {}
    clipboard = context.window_manager.py_rec.preset_options.clipboard
    for p_detail in clipboard.prop_details:
        for abt in p_detail.available_base_types:
            available_base_types[abt.name] = True
    items = [ (bt_name, bt_name, "") for bt_name in available_base_types.keys() ]
    return items if len(items) > 0 else [ (" ", "", "") ]

def paste_full_datapath_to_apply_preset(full_datapath, preset_options):
    # remove leading/trailing whitesapce
    full_datapath = full_datapath.strip()
    available_base_types = preset_options.apply_available_types
    available_base_types.clear()
    if not is_valid_full_datapath(full_datapath):
        return
    path_type_paths, _ = digest_full_datapath(full_datapath, all_bpy_types=True)
    # exit if no data for next steps
    if path_type_paths is None:
        return
    for bt_path, bt_name, _ in path_type_paths:
        abt = available_base_types.add()
        abt.name = bt_name + ": " + bt_path[9:]

def set_apply_input_full_datapath(self, value):
    if self.get("apply_input_full_datapath") is None:
        self["apply_input_full_datapath"] = value
        return
    self["apply_input_full_datapath"] = value
    # remove leading/trailing whitespace before testing/setting active full data path
    paste_full_datapath_to_apply_preset(value, bpy.context.window_manager.py_rec.preset_options)

def get_apply_input_full_datapath(self):
    return self.get("apply_input_full_datapath", "")

def apply_base_type_items(self, context):
    preset_options = context.window_manager.py_rec.preset_options
    items = [ (t.name, t.name, "") for t in preset_options.apply_available_types ]
    return items if len(items) > 0 else [ (" ", "", "") ]

def apply_collection_items(self, context):
    p_r = context.window_manager.py_rec
    # use Blender Addon Preferences or .blend file as Preset save data source
    if p_r.preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
        preset_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
    else:
        preset_collections = p_r.preset_collections
    # include all preset collections in list
    items = [ (pc.name, pc.name, "") for pc in preset_collections ]
    return items if len(items) > 0 else [ (" ", "", "") ]

def apply_preset_items(self, context):
    p_r = context.window_manager.py_rec
    # use Blender Addon Preferences or .blend file as Preset save data source
    if p_r.preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
        preset_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
    else:
        preset_collections = p_r.preset_collections
    preset_options = context.window_manager.py_rec.preset_options
    apply_collection = preset_options.apply_collection
    apply_base_type = preset_options.apply_base_type
    # exit if base type is blank
    if apply_base_type == " ":
        return [ (" ", "", "") ]
    # remove ': datapath' from end of base type name, to get base type only
    apply_base_type = apply_base_type[:apply_base_type.find(":")]
    if apply_collection in preset_collections:
        base_types = preset_collections[apply_collection].base_types
        if apply_base_type in base_types:
            presets = base_types[apply_base_type].presets
            # include all presets in list, because base type of all presets match given base type
            items = [ (p.name, p.name, "") for p in presets ]
            if len(items) > 0:
                return items
    return [ (" ", "", "") ]

def modify_base_type_items(self, context):
    preset_options = context.window_manager.py_rec.preset_options
    p_r = context.window_manager.py_rec
    # use Blender Addon Preferences or .blend file as Preset save data source
    if p_r.preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
        preset_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
    else:
        preset_collections = p_r.preset_collections
    try:
        tps = preset_collections[preset_options.modify_active_collection].base_types
        # get list of type names ('bpy.types.' name)
        items = [ (t.name, t.name, "") for t in tps ]
        if len(items) > 0:
            return items
    except:
        pass
    return [ (" ", "", "") ]

def preset_clipboard_clear(cb_options, clipboard):
    # reset Preset Clipboard properties
    cb_options.active_prop_detail = 0
    clipboard.prop_details.clear()
    clipboard.bool_props.clear()
    clipboard.int_props.clear()
    clipboard.float_props.clear()
    clipboard.string_props.clear()
    clipboard.vector_xyz_props.clear()

def preset_clipboard_remove_item(cb_options, clipboard):
    clipboard.prop_details.remove(cb_options.active_prop_detail)

def get_next_name(name, collection):
    if name not in collection:
        return name
    # check if '.001' (and '.002', etc.) decimal ending should be removed before searching for unused 'next name'
    r = name.rfind(".")
    if r != -1 and r != len(name)-1:
        if name[r+1:].isdecimal():
            name = name[:r]
    # search for unused 'next name' in 999 possible names
    for n in range(1, 999):
        next_name = "%s.%s" % (name, str(n).zfill(3))
        if next_name not in collection:
            return next_name
    return None

def preset_clipboard_create_preset(p_collections, clipboard, cb_options):
    base_type_name = cb_options.create_base_type
    preset_name = cb_options.create_preset_name
    # if Preset name is empty then use default name
    if preset_name == "":
        preset_name = "Preset"
    coll_name = cb_options.create_preset_coll_name
    # if Preset Collection name is empty then use default name
    if coll_name == "":
        coll_name = "Collection"
    # create Preset Collection if necessary
    if coll_name in p_collections:
        preset_coll = p_collections[coll_name]
    else:
        # check if Preset Collection name is used, and append '.001', etc. if name is already used
        next_coll_name = get_next_name(coll_name, p_collections)
        preset_coll = p_collections.add()
        preset_coll.name = next_coll_name
    # create TypePresets collection if necessary
    if base_type_name in preset_coll.base_types:
        preset_type = preset_coll.base_types[base_type_name]
    else:
        preset_type = preset_coll.base_types.add()
        preset_type.name = base_type_name
    # create Preset from data in Property Clipboard
    # check if Preset name is used, and append '.001', etc. if name is already used
    next_preset_name = get_next_name(preset_name, preset_type.presets)
    new_preset = preset_type.presets.add()
    new_preset.name = next_preset_name
    for prop_detail in clipboard.prop_details:
        if prop_detail.base_type == base_type_name:
            try:
                prop_path = prop_detail.available_base_types[prop_detail.base_type].value
            except:
                continue
            # do not add duplicate 'prop_path', if found
            if prop_path in new_preset.prop_details:
                continue
            preset_prop_detail = new_preset.prop_details.add()
            preset_prop_detail.name = prop_path
            preset_prop_detail.value_type = prop_detail.value_type
            if prop_detail.value_type == "bool":
                new_preset_prop = new_preset.bool_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.bool_props[prop_detail.name].value
            elif prop_detail.value_type == "float":
                new_preset_prop = new_preset.float_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.float_props[prop_detail.name].value
            elif prop_detail.value_type == "int":
                new_preset_prop = new_preset.int_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.int_props[prop_detail.name].value
            elif prop_detail.value_type == "str":
                new_preset_prop = new_preset.string_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.string_props[prop_detail.name].value
            elif prop_detail.value_type == "VectorXYZ":
                new_preset_prop = new_preset.vector_xyz_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.vector_xyz_props[prop_detail.name].value
    return new_preset.name

def preset_remove_prop(preset_options, preset_collections):
    preset = preset_collections[preset_options.modify_active_collection].\
        base_types[preset_options.modify_base_type].presets[preset_options.modify_active_preset]
    prop_detail_name = preset.prop_details[preset_options.modify_detail].name
    prop_detail_type = preset.prop_details[preset_options.modify_detail].value_type
    # check value type to remove preset property value from correct collection
    if prop_detail_type == "bool":
        preset.bool_props.remove(preset.bool_props.find(prop_detail_name))
    elif prop_detail_type == "float":
        preset.float_props.remove(preset.float_props.find(prop_detail_name))
    elif prop_detail_type == "int":
        preset.int_props.remove(preset.int_props.find(prop_detail_name))
    elif prop_detail_type == "str":
        preset.string_props.remove(preset.string_props.find(prop_detail_name))
    elif prop_detail_type == "VectorXYZ":
        preset.vector_xyz_props.remove(preset.vector_xyz_props.find(prop_detail_name))
    # remove preset property detail
    preset.prop_details.remove(preset_options.modify_detail)

# recurse through datapath hierarchy, starting at base_val and using getattr(), to get to value prior to property
# being preset
def get_apply_base_val(base_val, datapath):
    s = 0
    current_val = base_val
    while True:
        e = datapath.find(".", s)
        if e == -1:
            return current_val, datapath[s:]
        attr_name = datapath[s:e]
        current_val = getattr(current_val, attr_name)
        if current_val is None:
            break
        s = e + 1
    return None, None

def apply_preset_to_base_value(base_val, preset):
    for p_d in preset.prop_details:
        # get 'apply base value', and set value of named Python 'attribute' (Blender 'property'), recursing
        # through datapath hierarchy if needed
        apply_base_val, attr_name = get_apply_base_val(base_val, p_d.name)
        # ignore this preset property if the apply base value is not available
        if apply_base_val is None or attr_name is None:
            continue
        if p_d.value_type == "bool":
            preset_val = preset.bool_props[p_d.name].value
        elif p_d.value_type == "float":
            preset_val = preset.float_props[p_d.name].value
        elif p_d.value_type == "int":
            preset_val = preset.int_props[p_d.name].value
        elif p_d.value_type == "str":
            preset_val = preset.string_props[p_d.name].value
        elif p_d.value_type == "VectorXYZ":
            preset_val = preset.vector_xyz_props[p_d.name].value
        setattr(apply_base_val, attr_name, preset_val)

# get result of digest of given full datapath,
# get result by given base type,
# get value of result by eval(),
# try to apply Preset to value, copying prop values by datapath from Preset to given full datapath / base type
def preset_apply_preset(preset_options, preset_collections):
    apply_full_datapath = trim_datapath(preset_options.apply_input_full_datapath)
    apply_base_type = preset_options.apply_base_type
    apply_collection = preset_options.apply_collection
    apply_preset = preset_options.apply_preset
    if apply_full_datapath == "":
        return
    if apply_base_type == " ":
        return
    if apply_collection == " ":
        return
    if apply_preset == " ":
        return
    # remove ': datapath' from end of base type name, to get base type only
    apply_base_type = apply_base_type[:apply_base_type.find(":")]
    preset = preset_collections[apply_collection].base_types[apply_base_type].presets[apply_preset]
    # if zero property details available then exit, because zero properties to set
    if len(preset.prop_details) == 0:
        return
    path_type_paths, _ = digest_full_datapath(apply_full_datapath, all_bpy_types=True)
    # exit if no data for next steps
    if path_type_paths is None:
        return
    # find full base type path, by given base type, and apply preset to value from eval() of full data path
    for bt_path, bt_name, _ in path_type_paths:
        # filter by base type
        if bt_name == apply_base_type:
            apply_preset_to_base_value(eval(bt_path), preset)
            break

def preset_collection_remove_collection(preset_options, preset_collections):
    preset_collections.remove(preset_options.modify_active_collection)

def preset_collection_remove_preset(preset_options, preset_collections):
    preset_collections[preset_options.modify_active_collection].\
        base_types[preset_options.modify_base_type].presets.remove(preset_options.modify_active_preset)

# force screen to redraw, known to work in Blender 3.3+
def do_tag_redraw():
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D' or a.type == 'TEXT_EDITOR':
            for r in a.regions:
                r.tag_redraw()

def preset_collection_modify_rename(p_options, p_collections):
    new_name = p_options.modify_collection_rename
    # quit if new_name is blank
    if new_name == "":
        return
    f = p_options.modify_collection_function
    if f == MODIFY_COLL_FUNC_RENAME:
        if len(p_collections) > p_options.modify_active_collection:
            # if name is already taken, then rename same named collection by appending '.001', etc.
            if new_name in p_collections:
                old_p_coll = p_collections[new_name]
                old_p_coll.name = get_next_name(new_name, p_collections)
            # rename active collection
            p_coll = p_collections[p_options.modify_active_collection]
            p_coll.name = new_name
            # redraw screen to show new_name
            do_tag_redraw()

def preset_modify_rename(p_options, p_collections):
    new_name = p_options.modify_preset_rename
    # quit if new_name is blank
    if new_name == "":
        return
    presets = None
    if len(p_collections) > p_options.modify_active_collection:
        active_coll = p_collections[p_options.modify_active_collection]
        if p_options.modify_base_type in active_coll.base_types:
            presets = active_coll.base_types[p_options.modify_base_type].presets
    if presets != None:
        # if name is already taken, then rename same named Preset by appending '.001', etc.
        if new_name in presets:
            old_preset = presets[new_name]
            old_preset.name = get_next_name(new_name, presets)
        # rename active Preset
        preset = presets[p_options.modify_active_preset]
        preset.name = new_name
        # redraw screen to show new_name
        do_tag_redraw()

def escape_str(in_str):
    if isinstance(in_str, str):
        return in_str.translate(str.maketrans( { "\\": r"\\", "'": r"\'" } ))

def props_export_str(props):
    prop_str = ""
    for p in props:
        escaped_name = escape_str(p.name)
        # string quotes
        if isinstance(p.value, str):
            value_str = "'" + escape_str(p.value) + "'"
        # Vector parentheses
        elif isinstance(p.value, Vector):
            value_str = "(" + str(p.value[0])
            for i in range(1, len(p.value)):
                value_str += ", " + str(p.value[i])
            value_str += ")"
        # generic
        else:
            value_str = str(p.value)
        prop_str += "                            { 'name': '%s', 'value': %s },\n" % (escaped_name, value_str)
    return prop_str

def get_export_presets_data(p_collections):
    colls_str = ""
    presets_count = 0
    for coll in p_collections:
        base_types_str = ""
        for bt in coll.base_types:
            presets_str = ""
            for preset in bt.presets:
                presets_count += 1
                out_str_bool_props = props_export_str(preset.bool_props)
                out_str_float_props = props_export_str(preset.float_props)
                out_str_int_props = props_export_str(preset.int_props)
                out_str_string_props = props_export_str(preset.string_props)
                out_str_vector_xyz_props = props_export_str(preset.vector_xyz_props)
                if out_str_bool_props == "" and out_str_float_props == "" and out_str_int_props == "" \
                    and out_str_string_props == "" and out_str_vector_xyz_props == "":
                    continue
                esc_p_name = escape_str(preset.name)
                presets_str += "                    {   'name': '%s',\n" % esc_p_name
                if out_str_bool_props != "":
                    presets_str +=  "                        'bool_props': [\n"
                    presets_str += out_str_bool_props
                    presets_str +=  "                            ],\n"
                if out_str_float_props != "":
                    presets_str +=  "                        'float_props': [\n"
                    presets_str += out_str_float_props
                    presets_str +=  "                            ],\n"
                if out_str_int_props != "":
                    presets_str +=  "                        'int_props': [\n"
                    presets_str += out_str_int_props
                    presets_str +=  "                            ],\n"
                if out_str_string_props != "":
                    presets_str +=  "                        'string_props': [\n"
                    presets_str += out_str_string_props
                    presets_str +=  "                            ],\n"
                if out_str_vector_xyz_props != "":
                    presets_str +=  "                        'vector_xyz_props': [\n"
                    presets_str += out_str_vector_xyz_props
                    presets_str +=  "                            ],\n"
                presets_str += "                        },\n"
            if presets_str == "":
                continue
            esc_bt_name = escape_str(bt.name)
            base_types_str += "            {   'type': '%s',\n" % esc_bt_name
            base_types_str += "                'presets': [\n"
            base_types_str += presets_str
            base_types_str += "                    ],\n                },\n"
        if base_types_str == "":
            continue
        esc_coll_name = escape_str(coll.name)
        colls_str += "    {   'name': '%s',\n" % esc_coll_name
        colls_str += "        'base_types': [\n"
        colls_str += base_types_str
        colls_str += "            ],\n        },\n"
    if colls_str == "":
        return 0, 0, ""
    return len(p_collections), presets_count, "[\n" + colls_str + "    ]\n"

def export_presets_file(p_collections, filepath):
    colls_count, presets_count, presets_str = get_export_presets_data(p_collections)
    try:
        with open(filepath, "w") as p_file:
            p_file.write(presets_str)
    except:
        return traceback.format_exc()
    return colls_count, presets_count

def export_presets_object(p_collections, ob):
    colls_count, presets_count, presets_str = get_export_presets_data(p_collections)
    ob["py_presets_collections"] = presets_str
    return colls_count, presets_count

# given 'f' is an iterable set of strings (e.g. open file, or list of strings),
# returns dict() {
#     "result": < result of ast.literal_eval() with file string >,
#     "error": "< True / False >,
# }
def ast_literal_eval_lines(f):
    full_str = ""
    for line in f:
        # remove comments without modifying file line structure
        find_comment = line.find("#")
        if find_comment != -1:
            line = line[:find_comment] + "\n"
        full_str += line
    try:
        eval_result = ast.literal_eval(full_str)
    except:
        return { "error": traceback.format_exc() }
    return { "result": eval_result }

def convert_import_props(raw_props, value_type):
    if not isinstance(raw_props, list):
        return None
    new_prop_list = []
    for p in raw_props:
        if not isinstance(p, dict):
            continue
        p_name = p.get("name")
        p_val = p.get("value")
        if isinstance(p_name, str) and isinstance(p_val, value_type):
            new_prop_list.append( { "name": p_name, "value": p_val } )
    return new_prop_list if len(new_prop_list) > 0 else None

def convert_import_presets_collections(import_eval):
    new_collections = []
    for imp_presets_coll in import_eval:
        if not isinstance(imp_presets_coll, dict):
            continue
        coll_name = imp_presets_coll.get("name")
        imp_base_types = imp_presets_coll.get("base_types")
        if not isinstance(coll_name, str) or not isinstance(imp_base_types, list):
            continue
        new_base_types = []
        for imp_bt in imp_base_types:
            if not isinstance(imp_bt, dict):
                continue
            imp_bt_name = imp_bt.get("type")
            imp_bt_presets = imp_bt.get("presets")
            if not isinstance(imp_bt_name, str) or not isinstance(imp_bt_presets, list):
                continue
            new_presets = []
            for imp_preset in imp_bt_presets:
                if not isinstance(imp_preset, dict):
                    continue
                preset_name = imp_preset.get("name")
                if preset_name is None:
                    continue
                bool_props = convert_import_props(imp_preset.get("bool_props"), bool)
                float_props = convert_import_props(imp_preset.get("float_props"), float)
                int_props = convert_import_props(imp_preset.get("int_props"), int)
                string_props = convert_import_props(imp_preset.get("string_props"), str)
                vector_xyz_props = convert_import_props(imp_preset.get("vector_xyz_props"), Vector)
                temp_preset = {}
                if bool_props != None:
                    temp_preset["bool_props"] = bool_props
                if float_props != None:
                    temp_preset["float_props"] = float_props
                if int_props != None:
                    temp_preset["int_props"] = int_props
                if string_props != None:
                    temp_preset["string_props"] = string_props
                if vector_xyz_props != None:
                    temp_preset["vector_xyz_props"] = vector_xyz_props
                if len(temp_preset) > 0:
                    temp_preset["name"] = preset_name
                    new_presets.append(temp_preset)
            if len(new_presets) > 0:
                new_base_types.append( { "type": imp_bt_name, "presets": new_presets } )
        new_collections.append( { "name": coll_name, "base_types": new_base_types } )
    return new_collections if len(new_collections) > 0 else None

def add_conv_props_to_preset(src_props, dest_props, dest_prop_details, value_type):
    for imp_prop in src_props:
        new_prop = dest_props.add()
        new_prop.name = imp_prop["name"]
        new_prop.value = imp_prop["value"]
        new_detail = dest_prop_details.add()
        new_detail.name = imp_prop["name"]
        new_detail.value_type = value_type

def import_presets_collections_eval(p_collections, pc_eval, dup_coll_action, replace_preset):
    imp_presets_collections = convert_import_presets_collections(pc_eval)
    if imp_presets_collections is None:
        return 0, 0
    presets_count = 0
    for imp_coll in imp_presets_collections:
        new_coll = p_collections.get(imp_coll["name"])
        if new_coll is None:
            new_coll = p_collections.add()
            new_coll.name = imp_coll["name"]
        else:
            if dup_coll_action == IMPEXP_DUP_COLL_REPLACE:
                p_collections.remove( p_collections.find(imp_coll["name"]) )
                new_coll = p_collections.add()
                new_coll.name = imp_coll["name"]
            elif dup_coll_action == IMPEXP_DUP_COLL_RENAME:
                next_name = get_next_name(imp_coll["name"], p_collections)
                new_coll = p_collections.add()
                new_coll.name = next_name
            # else: Merge Collection
        for imp_bt in imp_coll["base_types"]:
            new_bt = new_coll.base_types.get(imp_bt["type"])
            if new_bt is None:
                new_bt = new_coll.base_types.add()
                new_bt.name = imp_bt["type"]
            for imp_preset in imp_bt["presets"]:
                presets_count += 1
                new_preset = new_bt.presets.get(imp_preset["name"])
                if new_preset is None:
                    new_preset = new_bt.presets.add()
                    new_preset.name = imp_preset["name"]
                else:
                    if replace_preset:
                        new_bt.presets.remove( new_bt.presets.find(imp_preset["name"]) )
                        new_preset = new_bt.presets.add()
                        new_preset.name = imp_preset["name"]
                    # rename new Preset, e.g. append .001
                    else:
                        next_name = get_next_name(imp_preset["name"], new_bt.presets)
                        new_preset = new_bt.presets.add()
                        new_preset.name = next_name
                bool_props = imp_preset.get("bool_props")
                if bool_props != None:
                    add_conv_props_to_preset(bool_props, new_preset.bool_props, new_preset.prop_details, "bool")
                float_props = imp_preset.get("float_props")
                if float_props != None:
                    add_conv_props_to_preset(float_props, new_preset.float_props, new_preset.prop_details, "float")
                int_props = imp_preset.get("int_props")
                if int_props != None:
                    add_conv_props_to_preset(int_props, new_preset.int_props, new_preset.prop_details, "int")
                string_props = imp_preset.get("string_props")
                if string_props != None:
                    add_conv_props_to_preset(string_props, new_preset.string_props, new_preset.prop_details, "str")
                vector_xyz_props = imp_preset.get("vector_xyz_props")
                if vector_xyz_props != None:
                    add_conv_props_to_preset(vector_xyz_props, new_preset.vector_xyz_props, new_preset.prop_details,
                                             "VectorXYZ")
    return len(imp_presets_collections), presets_count

def import_presets_file(p_collections, filepath, dup_coll_action, replace_preset):
    file_eval = None
    try:
        with open(filepath, "r") as f:
            eval_result = ast_literal_eval_lines(f)
            file_eval = eval_result.get("result")
            err_msg = eval_result.get("error")
            if err_msg != None:
                log_text_append("Unable to import Presets Collections from file with path %s\n%s" %
                                (filepath, err_msg))
                return "Unable to import Presets from file with path %s\nSee Py Recorder log Text " \
                    "for full error message" % filepath
    except:
        return "Unable to open Presets Collections file with path " + filepath
    if not isinstance(file_eval, list):
        return "Error during Import Presets from file, unable to get Presets Collections list"
    return import_presets_collections_eval(p_collections, file_eval, dup_coll_action, replace_preset)

def import_presets_object(p_collections, ob, dup_coll_action, replace_preset):
#    ob["py_presets_collections"] = get_export_presets_str(p_collections)
    import_presets_str = ob.get("py_presets_collections")
    if not isinstance(import_presets_str, str):
        return "Cannot import Presets Collections, unable to get .py string attached to Object named " + ob.name
    eval_result = ast_literal_eval_lines(import_presets_str.splitlines())
    object_eval = eval_result.get("result")
    err_msg = eval_result.get("error")
    if object_eval is None or err_msg != None:
        log_text_append("Unable to import Presets Collections from Object named %s\n%s" % (ob.name, err_msg))
        return "Unable to import Presets Collections from Object named %s\nSee Py Recorder log Text for full " \
            "error message" % ob.name
    return import_presets_collections_eval(p_collections, object_eval, dup_coll_action, replace_preset)

def copy_active_preset_to_clipboard(context, p_options, p_collections):
    presets = None
    if len(p_collections) > p_options.modify_active_collection:
        active_coll = p_collections[p_options.modify_active_collection]
        if p_options.modify_base_type in active_coll.base_types:
            presets = active_coll.base_types[p_options.modify_base_type].presets
    if presets is None or len(presets) <= p_options.modify_active_preset:
        return None
    preset = presets[p_options.modify_active_preset]
    clipboard = context.window_manager.py_rec.preset_options.clipboard
    props_count = 0
    for prop in preset.bool_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_base_type, prop.name) ], prop.value)
    for prop in preset.float_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_base_type, prop.name) ], prop.value)
    for prop in preset.int_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_base_type, prop.name) ], prop.value)
    for prop in preset.string_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_base_type, prop.name) ], prop.value)
    for prop in preset.vector_xyz_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_base_type, prop.name) ], prop.value)
    return props_count
