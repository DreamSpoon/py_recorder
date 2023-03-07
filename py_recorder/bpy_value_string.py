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

def bpy_value_to_string(value):
    # write attribute, if it matches a known type
    if isinstance(value, str):
        return "\"%s\"" % value
    elif isinstance(value, bool):
        return "%s" % value
    elif isinstance(value, int):
        return "%d" % value
    elif isinstance(value, float):
        return "%f" % value
    # if attribute has a length then it is a Vector, Color, etc., so write elements of attribute in a tuple,
    # unless it is a set
    elif hasattr(value, '__len__'):
        vec_str = ""
        # is it a set?
        if isinstance(value, set):
            for item in value:
                if vec_str != "":
                    vec_str = vec_str + ", "
                sub_val_str = bpy_value_to_string(item)
                if sub_val_str is None:
                    vec_str = vec_str + "None"
                else:
                    vec_str = vec_str + sub_val_str
            return "{" + vec_str + "}"
        else:
            for val_index in range(len(value)):
                if vec_str != "":
                    vec_str = vec_str + ", "
                sub_val_str = bpy_value_to_string(value[val_index])
                if sub_val_str is None:
                    vec_str = vec_str + "None"
                else:
                    vec_str = vec_str + sub_val_str
            return "(" + vec_str + ")"
    # if the attribute's value has attribute 'name', then check if it is in a Blender built-in data list
    elif hasattr(value, 'name'):
        if type(value) == bpy.types.Image:
            return "bpy.data.images.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Mask:
            return "bpy.data.masks.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Scene:
            return "bpy.data.scenes.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Material:
            return "bpy.data.materials.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Object:
            return "bpy.data.objects.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Collection:
            return "bpy.data.collections.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.GeometryNodeTree or type(value) == bpy.types.ShaderNodeTree:
            return "bpy.data.node_groups.get(\"" + value.name + "\")"
        elif type(value) == bpy.types.Text:
            return "bpy.data.texts.get(\"" + value.name + "\")"
    # return None, because attribute type is unknown
    else:
        return None
