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
from mathutils import Euler, Quaternion, Vector
import traceback

from bpy.types import bpy_prop_array

from ..bl_util import get_next_name
from ..log_text import log_text_append
from .func import (DUP_COLL_ACTION_RENAME, DUP_COLL_ACTION_REPLACE)

PRESETS_COLLECTIONS_CUSTOM_PROP_NAME = "py_presets_collections"

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
        # Euler
        elif isinstance(p.value, Euler):
            value_str = "(%f, %f, %f, '%s')" % (p.value[0], p.value[1], p.value[2], p.order)
        # tuple/list/etc. parentheses
        elif isinstance(p.value, (bpy_prop_array, list, Quaternion, tuple, Vector)):
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
                out_str_vector_euler_props = props_export_str(preset.vector_euler_props)
                out_str_vector_float3_props = props_export_str(preset.vector_float3_props)
                out_str_vector_float4_props = props_export_str(preset.vector_float4_props)
                if out_str_bool_props == "" and out_str_float_props == "" and out_str_int_props == "" \
                    and out_str_string_props == "" and out_str_vector_euler_props == "" \
                    and out_str_vector_float3_props == "" and out_str_vector_float4_props == "":
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
                if out_str_vector_euler_props != "":
                    presets_str +=  "                        'vector_euler_props': [\n"
                    presets_str += out_str_vector_euler_props
                    presets_str +=  "                            ],\n"
                if out_str_vector_float3_props != "":
                    presets_str +=  "                        'vector_float3_props': [\n"
                    presets_str += out_str_vector_float3_props
                    presets_str +=  "                            ],\n"
                if out_str_vector_float4_props != "":
                    presets_str +=  "                        'vector_float4_props': [\n"
                    presets_str += out_str_vector_float4_props
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
    ob[PRESETS_COLLECTIONS_CUSTOM_PROP_NAME] = presets_str
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

def is_imp_euler_type(v):
    if not isinstance(v, tuple) or len(v) != 4:
        return False
    return isinstance(v[0], float) and isinstance(v[1], float) and isinstance(v[2], float) and isinstance(v[3], str)

def is_imp_vec_float_type(v):
    if isinstance(v, (bpy_prop_array, list, Quaternion, tuple, Vector)):
        if len(v) == 3:
            return isinstance(v[0], float) and isinstance(v[1], float) and isinstance(v[2], float)
        elif len(v) == 4:
            return isinstance(v[0], float) and isinstance(v[1], float) and isinstance(v[2], float) \
                and isinstance(v[3], float)
    return False

def convert_import_props(raw_props, value_type):
    if not isinstance(raw_props, list):
        return None
    new_prop_list = []
    for p in raw_props:
        if not isinstance(p, dict):
            continue
        p_name = p.get("name")
        p_val = p.get("value")
        if not isinstance(p_name, str):
            continue
        if isinstance(p_val, value_type) or (value_type == Euler and is_imp_euler_type(p_val) ) \
            or (value_type in [ bpy_prop_array, list, Quaternion, tuple, Vector ] and is_imp_vec_float_type(p_val) ):
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
                vector_euler_props = convert_import_props(imp_preset.get("vector_euler_props"), Euler)
                vector_float3_props = convert_import_props(imp_preset.get("vector_float3_props"), Quaternion)
                vector_float4_props = convert_import_props(imp_preset.get("vector_float4_props"), Quaternion)
                temp_preset = {}
                if bool_props != None:
                    temp_preset["bool_props"] = bool_props
                if float_props != None:
                    temp_preset["float_props"] = float_props
                if int_props != None:
                    temp_preset["int_props"] = int_props
                if string_props != None:
                    temp_preset["string_props"] = string_props
                if vector_euler_props != None:
                    temp_preset["vector_euler_props"] = vector_euler_props
                if vector_float3_props != None:
                    temp_preset["vector_float3_props"] = vector_float3_props
                if vector_float4_props != None:
                    temp_preset["vector_float4_props"] = vector_float4_props
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
        if value_type == "VectorEuler":
            temp_val = (imp_prop["value"][0], imp_prop["value"][1], imp_prop["value"][2])
            new_prop.value = Euler(temp_val, imp_prop["value"][3])
            new_prop.order = imp_prop["value"][3]
        else:
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
            if dup_coll_action == DUP_COLL_ACTION_RENAME:
                next_name = get_next_name(imp_coll["name"], p_collections)
                new_coll = p_collections.add()
                new_coll.name = next_name
            elif dup_coll_action == DUP_COLL_ACTION_REPLACE:
                p_collections.remove( p_collections.find(imp_coll["name"]) )
                new_coll = p_collections.add()
                new_coll.name = imp_coll["name"]
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
                vector_euler_props = imp_preset.get("vector_euler_props")
                if vector_euler_props != None:
                    add_conv_props_to_preset(vector_euler_props, new_preset.vector_euler_props,
                                             new_preset.prop_details, "VectorEuler")
                vector_float3_props = imp_preset.get("vector_float3_props")
                if vector_float3_props != None:
                    add_conv_props_to_preset(vector_float3_props, new_preset.vector_float3_props,
                                             new_preset.prop_details, "VectorFloat3")
                vector_float4_props = imp_preset.get("vector_float4_props")
                if vector_float4_props != None:
                    add_conv_props_to_preset(vector_float4_props, new_preset.vector_float4_props,
                                             new_preset.prop_details, "VectorFloat4")
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
    import_presets_str = ob.get(PRESETS_COLLECTIONS_CUSTOM_PROP_NAME)
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

def transfer_object_presets(src_ob, dest_ob_list):
    pc_str = src_ob.get(PRESETS_COLLECTIONS_CUSTOM_PROP_NAME)
    if not isinstance(pc_str, str):
        return "source Object does not have custom property named: " + PRESETS_COLLECTIONS_CUSTOM_PROP_NAME
    elif len(pc_str) == 0:
        return "source Object's custom property for Presets Collections data is zero length"
    for dest_ob in dest_ob_list:
        dest_ob[PRESETS_COLLECTIONS_CUSTOM_PROP_NAME] = pc_str
    return None
