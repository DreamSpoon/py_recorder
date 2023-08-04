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

from inspect import getdoc
import mathutils

from .bpy_value_string import bpy_value_to_string
from .lex_py_attributes import lex_py_attributes

def strip_line_comment(src_line):
    dest_line = ""
    state_vars = { "backslash": False, "quote": False, "double_quote": False }
    for c in src_line:
        if c == "#":
            # ignore '#' symbols in quotes
            if state_vars["quote"]:
                pass
            # comment found
            else:
                dest_line += "\n"
                break
        elif c == "'":
            if state_vars["backslash"]:
                if state_vars["quote"]:
                    state_vars["backslash"] = False
                else:
                    if not state_vars["double_quote"]:
                        state_vars["quote"] = True
            else:
                if not state_vars["double_quote"]:
                    state_vars["quote"] = not state_vars["quote"]
        elif c == '"':
            if state_vars["backslash"]:
                if state_vars["double_quote"]:
                    state_vars["backslash"] = False
                else:
                    if not state_vars["quote"]:
                        state_vars["double_quote"] = True
            else:
                if not state_vars["quote"]:
                    state_vars["double_quote"] = not state_vars["double_quote"]
        elif c == "\\":
            state_vars["backslash"] = not state_vars["backslash"]
        elif c == "\n":
            dest_line += c
            break
        else:
            state_vars["backslash"] = False
        dest_line += c
    return dest_line

def get_commented_splitlines(input_str):
    if input_str is None or input_str == "":
        return ""
    out_str = ""
    for l in input_str.splitlines():
        out_str = out_str + "#  " + l + "\n"
    return out_str

# returns 2-tuple of (input_str less last attribute, last attribute)
def remove_last_py_attribute(input_str):
    output, _ = lex_py_attributes(input_str)
    # cannot remove last attribute if too few output attributes
    if len(output) < 2:
        return None, None
    # use end_position of last output item to return input_str up to, and including, end of second last attribute
    return input_str[ : output[-2][1] ], input_str[ output[-1][0] : output[-1][1] ]

# returns list of strings, each string is a name 'token' representing an attribute in full datapath given by
# 'input_str' - order of strings is same as it appears in full datapath 'input_str'
def enumerate_datapath(input_str):
    output, _ = lex_py_attributes(input_str)
    return [ input_str[s:e] for s, e in output ]

# progressive full datapath, each entry longer than the last, finishing with 'input_str', '[]' indexes included
def enumerate_datapath_hierarchy(input_str, remove_bpy_data=False):
    path_list = []
    path = ""
    c = 0
    for t in enumerate_datapath(input_str):
        # if t is not an index token then add a '.' character
        if path != "" and t[0] != "[":
            path += "."
        path += t
        c += 1
        # do not add 'bpy' and 'bpy.data' if 'remove_bpy_data'
        if remove_bpy_data and (c == 1 or c == 2):
            continue
        path_list.append(path)
    return path_list

def trim_datapath(input_str):
    attr_list, _ = lex_py_attributes(input_str)
    if attr_list is None or len(attr_list) < 1:
        return ""
    # return 'input_str' from start to end of attributes (includes '[]' indexes),
    # which removes any trailing spaces / equals signs / etc.
    return input_str[ :attr_list[-1][1] ]

# returns true if test_str starts with 'bpy.data.' (Blender data collection test) and 'test_str' can be evaluated in
# Python (try to use exec() )
def is_valid_full_datapath(test_str):
    if not test_str.startswith("bpy.data."):
        return False
    # trim_datapath will remove '=' assignment, if needed, from 'test_str', before using exec()
    #   - do this to prevent assigning values to properties during test for valid full data path
    exec_str = "import bpy\n" + trim_datapath(test_str)
    try:
        exec(exec_str)
        return True
    except:
        return False

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
        return getdoc(value)
    return None

# get name of class of value
def get_value_type_name(value):
    raw_name = str(type(value))
    if raw_name.startswith("<class '") and raw_name.endswith("'>"):
        return raw_name[8:-2]
    return ""

# test if value's type name begins with "bpy_types.", because this indicates that value's type is in 'bpy.types'
def is_bpy_type_name(t_name):
    return t_name.startswith("bpy.types.") or t_name.startswith("bpy_types.")
