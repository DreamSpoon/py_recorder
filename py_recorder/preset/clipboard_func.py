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

from mathutils import Euler, Quaternion, Vector

import bpy
from bpy.types import bpy_prop_array

from ..py_code_utils import is_valid_full_datapath
from ..bl_util import get_next_name
from .func import (digest_full_datapath, get_modify_active_single_preset)

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
    elif isinstance(prop_value, Euler):
        p = clipboard.euler_props.add()
        prop_detail.value_type = "Euler"
    elif isinstance(prop_value, float):
        p = clipboard.float_props.add()
        prop_detail.value_type = "float"
    elif isinstance(prop_value, int):
        p = clipboard.int_props.add()
        prop_detail.value_type = "int"
    elif isinstance(prop_value, str):
        p = clipboard.string_props.add()
        prop_detail.value_type = "str"
    elif isinstance(prop_value, (bpy_prop_array, list, Quaternion, tuple, Vector)):
        num_elements = len(prop_value)
        # all floats?
        if len([ d for d in prop_value if isinstance(d, float) ]) == num_elements:
            if num_elements == 3:
                p = clipboard.float_vector3_props.add()
                prop_detail.value_type = "FloatVector3"
            elif num_elements == 4:
                p = clipboard.float_vector4_props.add()
                prop_detail.value_type = "FloatVector4"
        # all bools?
        elif len([ d for d in prop_value if isinstance(d, bool) ]) == num_elements:
            if num_elements == 32:
                p = clipboard.layer32_props.add()
                prop_detail.value_type = "Layer32"
    if p is None:
        return
    # link type-specific property to prop_detail with 'full_datapath'
    p.name = full_datapath
    # set value of new property in Preset
    p.value = prop_value
    if isinstance(prop_value, Euler):
        p.order = prop_value.order

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

def preset_clipboard_clear(cb_options, clipboard):
    # reset Preset Clipboard properties
    cb_options.active_prop_detail = 0
    clipboard.prop_details.clear()
    clipboard.bool_props.clear()
    clipboard.int_props.clear()
    clipboard.euler_props.clear()
    clipboard.float_props.clear()
    clipboard.string_props.clear()
    clipboard.float_vector3_props.clear()
    clipboard.float_vector4_props.clear()
    clipboard.layer32_props.clear()

def preset_clipboard_remove_item(cb_options, clipboard):
    clipboard.prop_details.remove(cb_options.active_prop_detail)
    cb_options.active_prop_detail -= 1
    if cb_options.active_prop_detail < 0:
        cb_options.active_prop_detail = 0

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
            elif prop_detail.value_type == "Euler":
                new_preset_prop = new_preset.euler_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.euler_props[prop_detail.name].value
                new_preset_prop.order = clipboard.euler_props[prop_detail.name].order
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
            elif prop_detail.value_type == "FloatVector3":
                new_preset_prop = new_preset.float_vector3_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.float_vector3_props[prop_detail.name].value
            elif prop_detail.value_type == "FloatVector4":
                new_preset_prop = new_preset.float_vector4_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.float_vector4_props[prop_detail.name].value
            elif prop_detail.value_type == "Layer32":
                new_preset_prop = new_preset.layer32_props.add()
                new_preset_prop.name = prop_path
                new_preset_prop.value = clipboard.layer32_props[prop_detail.name].value
    return new_preset.name

def copy_active_preset_to_clipboard(context, p_options, p_collections):
    preset = get_modify_active_single_preset(p_options, p_collections)
    clipboard = context.window_manager.py_rec.preset_options.clipboard
    props_count = 0
    for prop in preset.bool_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_options.base_type, prop.name) ],
                              prop.value)
    for prop in preset.euler_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_options.base_type, prop.name) ],
                              prop.value)
    for prop in preset.float_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_options.base_type, prop.name) ],
                              prop.value)
    for prop in preset.int_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_options.base_type, prop.name) ],
                              prop.value)
    for prop in preset.string_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_options.base_type, prop.name) ],
                              prop.value)
    for prop in preset.float_vector3_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_options.base_type, prop.name) ],
                              prop.value)
    for prop in preset.float_vector4_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_options.base_type, prop.name) ],
                              prop.value)
    for prop in preset.layer32_props:
        props_count += 1
        create_clipboard_line(clipboard, prop.name, [ ("", p_options.modify_options.base_type, prop.name) ],
                              prop.value)
    return props_count

def text_to_preset_clipboard(text):
    for line in text.lines:
        body = line.body
        print("text line body =", body)
        print("  body len =", len(body))
        if body != "":
            paste_full_datapath_to_clipboard(body)
