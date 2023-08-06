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

from ..py_code_utils import (trim_datapath, is_valid_full_datapath)
from .func import (digest_full_datapath, get_preset_prop_value_str, get_source_preset_collections)

def paste_full_datapath_to_apply_preset(full_datapath, preset_options):
    # remove leading/trailing whitesapce
    full_datapath = full_datapath.strip()
    available_base_types = preset_options.apply_options.available_types
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

def set_apply_full_datapath(self, value):
    if self.get("apply_input_full_datapath") is None:
        self["apply_input_full_datapath"] = value
        return
    self["apply_input_full_datapath"] = value
    # remove leading/trailing whitespace before testing/setting active full data path
    paste_full_datapath_to_apply_preset(value, bpy.context.window_manager.py_rec.preset_options)

def get_apply_full_datapath(self):
    return self.get("apply_input_full_datapath", "")

def apply_base_type_items(self, context):
    preset_options = context.window_manager.py_rec.preset_options
    items = [ (t.name, t.name, "") for t in preset_options.apply_options.available_types ]
    # sort items alphabetically, by 'display name', and return sorted array
    items.sort(key = lambda x: x[1])
    return items if len(items) > 0 else [ (" ", "", "") ]

def apply_collection_items(self, context):
    # include all preset collections in list
    items = [ (pc.name, pc.name, "") for pc in get_source_preset_collections(context) ]
    # sort items alphabetically, by 'display name', and return sorted array
    items.sort(key = lambda x: x[1])
    return items if len(items) > 0 else [ (" ", "", "") ]

def apply_preset_items(self, context):
    preset_collections = get_source_preset_collections(context)
    preset_options = context.window_manager.py_rec.preset_options
    apply_collection = preset_options.apply_options.collection
    apply_base_type = preset_options.apply_options.base_type
    # exit if base type is blank
    if apply_base_type == " ":
        return [ (" ", "", "", 0) ]
    # remove ': datapath' from end of base type name, to get base type only
    apply_base_type = apply_base_type[:apply_base_type.find(":")]
    if apply_collection in preset_collections:
        base_types = preset_collections[apply_collection].base_types
        if apply_base_type in base_types:
            presets = base_types[apply_base_type].presets
            # include all presets in list, because base type of all presets match given base type
            items = [ (p.name, p.name, "") for p in presets ]
            if len(items) > 0:
                # sort items alphabetically, by 'display name', and return sorted array
                items.sort(key = lambda x: x[1])
                return items
    return [ (" ", "", "", 0) ]

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
    combined_err_msg = ""
    for p_d in preset.prop_details:
        # get 'apply base value', and set value of named Python 'attribute' (Blender 'property'), recursing
        # through datapath hierarchy if needed
        apply_base_val, attr_name = get_apply_base_val(base_val, p_d.name)
        # ignore this preset property if the apply base value is not available
        if apply_base_val is None or attr_name is None:
            continue
        pvs_result = get_preset_prop_value_str(preset, p_d.name)
        if pvs_result is None:
            continue
        if p_d.value_type == "Euler":
            try:
                sub_val = getattr(apply_base_val, attr_name)
                sub_val[0]= pvs_result[0][0][0]
                sub_val[1]= pvs_result[0][0][1]
                sub_val[2]= pvs_result[0][0][2]
                sub_val.order = pvs_result[0][1]
            except:
                # add error message with base value type, attribute name, and attribute value
                combined_err_msg += "Cannot apply Preset to type %s with property %s and value %s\n" % \
                    (str(type(apply_base_val)), attr_name, pvs_result[1])
        else:
            try:
                setattr(apply_base_val, attr_name, pvs_result[0])
            except:
                # add error message with base value type, attribute name, and attribute value
                combined_err_msg += "Cannot apply Preset to type %s with property %s and value %s\n" % \
                    (str(type(apply_base_val)), attr_name, pvs_result[1])
    return combined_err_msg[:-1]

# get result of digest of given full datapath,
# get result by given base type,
# get value of result by eval(),
# try to apply Preset to value, copying prop values by datapath from Preset to given full datapath / base type
def preset_apply_preset(preset_options, preset_collections):
    apply_full_datapath = trim_datapath(preset_options.apply_options.full_datapath)
    apply_base_type = preset_options.apply_options.base_type
    apply_collection = preset_options.apply_options.collection
    apply_preset = preset_options.apply_options.preset
    if apply_full_datapath == "":
        return "full datapath is zero length"
    if apply_base_type == " ":
        return "Apply Base Type is unknown"
    if apply_collection == " ":
        return "Apply Collection is unknown"
    if apply_preset == " ":
        return "Apply Preset is unknown"
    # remove ': datapath' from end of base type name, to get base type only
    apply_base_type = apply_base_type[:apply_base_type.find(":")]
    try:
        preset = preset_collections[apply_collection].base_types[apply_base_type].presets[apply_preset]
    except:
        return None
    # if zero property details available then exit, because zero properties to set
    if len(preset.prop_details) == 0:
        return None
    path_type_paths, _ = digest_full_datapath(apply_full_datapath, all_bpy_types=True)
    # exit if no data for next steps
    if path_type_paths is None:
        return "zero available types found"
    combined_err_msg = ""
    # find full base type path, by given base type, and apply preset to value from eval() of full data path
    for bt_path, bt_name, _ in path_type_paths:
        # filter by base type
        if bt_name == apply_base_type:
            err_msg = apply_preset_to_base_value(eval(bt_path), preset)
            if err_msg != "":
                combined_err_msg += err_msg
                combined_err_msg += "\n"
            break
    return combined_err_msg[:-1] if combined_err_msg != "" else None
