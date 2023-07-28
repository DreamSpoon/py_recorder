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
from bpy.types import PropertyGroup
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty,
     StringProperty)
from ..version_bpy_data import BPY_DATA_TYPE_ITEMS

from .func import (get_array_index, set_array_index, get_inspect_active_type_items, populate_index_strings,
    update_dir_attributes)

class PYREC_PG_AttributeRecordOptions(PropertyGroup):
    copy_from: EnumProperty(name = "From", description="Record Python code of Single Attribute or All Attributes of " +
        "current inspect value", items=[ ("single_attribute", "Single Attribute", ""),
                                         ("all_attributes", "All Attributes", "") ], default="single_attribute")
    copy_to: EnumProperty(name="To", description="Record attribute(s) as Python code to this", items=[
            ("clipboard", "Clipboard", "Record Python code to clipboard. Paste with 'Ctrl-V'"),
            ("new_text", "New Text", "Record Python code to new Text"),
            ("text", "Text", "Record Python code to existing Text"), ], default="clipboard")
    copy_to_text: PointerProperty(description="Text (in Text Editor) to receive output", type=bpy.types.Text)
    include_value: BoolProperty(name="Value", description="Include attribute value in recorded Python output " +
        "(with '=')", default=True)
    comment_type: BoolProperty(name="Type Comment", description="Include Python code with attribute value's type",
        default=True)
    comment_doc: BoolProperty(name="__doc__ Comment", description="Include Python code with attribute value's " +
        "'__doc__' attribute value (if it exists)", default=True)

class PYREC_PG_DirAttributeItem(PropertyGroup):
    type_name: StringProperty()
    value_str: StringProperty()

class PYREC_PG_InspectPanelOptions(PropertyGroup):
    panel_option_label: StringProperty(name="Panel Label", description="Modify Py Inspect panel label")
    display_attr_doc: BoolProperty(name="__doc__", description="Display '__doc__' attribute, which may contain " +
        "relevant information about current value", default=True, options={'HIDDEN'})
    display_attr_type_only: BoolProperty(name="Display only", description="Display only selected types of " +
        "attributes in Inspect Attributes area", default=False, options={'HIDDEN'})
    display_attr_type_function: BoolProperty(name="Function", description="Display 'function' type attributes in " +
        "Inspect Attributes area", default=True, options={'HIDDEN'})
    display_attr_type_builtin: BoolProperty(name="Builtin", description="Display 'builtin' type attributes in " +
        "Inspect Attributes area ('builtin' types have names beginning, and ending, with '__' , e.g. '__doc__')",
        default=True, options={'HIDDEN'})
    display_attr_type_bl: BoolProperty(name="bl_", description="Display 'Blender builtin' type attributes in " +
        "Inspect Attributes area. 'Blender builtin' type attributes have names beginning with 'bl_' ", default=True,
        options={'HIDDEN'})
    display_value_selector: BoolProperty(name="Try value entry", description="Try to display attribute value entry " +
        "box, to allow real-time editing of attribute value. Display value as string if try fails", default=True,
        options={'HIDDEN'})
    display_dir_attribute_type: BoolProperty(name="Type", description="Display Type column in Attribute list",
        default=False, options={'HIDDEN'})
    display_dir_attribute_value: BoolProperty(name="Value", description="Display Value column in Attribute list",
        default=True, options={'HIDDEN'})

class PYREC_PG_InspectPanel(PropertyGroup):
    panel_label: StringProperty()
    panel_options: PointerProperty(type=PYREC_PG_InspectPanelOptions)

    pre_inspect_type: EnumProperty(name="Pre-Inspect Exec Type", items=[
        ("none", "None", "Only inspect value Python code will be run to get inspect value"),
        ("single_line", "One Line", "Single line of Python code will be run before inspect value code is run"),
        ("textblock", "Text", "Text (in Text-Editor) with one or more lines of Python code to run before " \
         "inspect value code is run") ], default="none")
    pre_inspect_single_line: StringProperty(name="Pre-Inspect Exec", description="Single line of Python code to run " +
        "before running inspect value code")
    pre_inspect_text: PointerProperty(name="Pre-Inspect Text", description="Text (in Text Editor) with line(s) of " +
        "Python code to run before running inspect value code", type=bpy.types.Text)

    inspect_py_type: EnumProperty(name="Py Type", items=[
        ("active", "Active", "Active thing will be inspected (e.g. active Object in View3D context). Not yet " +
         "available in all contexts"),
        ("custom", "Custom", "Custom string of code will be run, and run result will be inspected"),
        ("datablock", "Datablock", "Datablock includes all data collections under 'bpy.data'") ],
        description="Type of Python object to inspect", default="custom")
    inspect_active_type: EnumProperty(name="Active Type", items=get_inspect_active_type_items)
    inspect_datablock_type: EnumProperty(name="Type", items=BPY_DATA_TYPE_ITEMS, default="objects",
        description="Type of data to inspect. Includes 'bpy.data' sources")
    inspect_datablock_name: StringProperty(name="Inspect datablock Name", description="Name of datablock instance " +
        "to inspect. Includes 'bpy.data' sources", default="")
    inspect_exec_str: StringProperty(name="Inspect Exec", description="Python string that will be run and result " +
        "returned when 'Inspect Exec' is used", default="bpy.data.objects")

    array_index_max: IntProperty()
    array_index: IntProperty(set=set_array_index, get=get_array_index, description="Array index integer for Zoom " +
        "In. Uses zero-based indexing, i.e. first item is number 0 ")
    array_key_set: CollectionProperty(type=PropertyGroup)
    array_key: EnumProperty(items=populate_index_strings, description="Array key string for Zoom In. Uses 'key()' " +
        "function to get available key names for array")
    array_index_key_type: EnumProperty(items=[("none", "None", "", 1),
        ("int", "Integer", "", 2),
        ("str", "String", "", 3),
        ("int_str", "Integer and String", "", 4) ], default="none")

    dir_inspect_exec_str: StringProperty()
    dir_attributes: CollectionProperty(type=PYREC_PG_DirAttributeItem)
    dir_attributes_index: IntProperty(update=update_dir_attributes)

    dir_col_size1: FloatProperty(name="List Column Size Factor 1", description="Adjust column width",
        default=0.5, min=0.1, max=0.9)
    dir_col_size2: FloatProperty(name="List Column Size Factor 2", description="Adjust column width",
        default=0.5, min=0.1, max=0.9)

    dir_item_doc_lines: CollectionProperty(type=PropertyGroup)
    dir_item_doc_lines_index: IntProperty()

    inspect_exec_state = {}

class PYREC_PG_InspectPanelCollection(PropertyGroup):
    inspect_context_panels: CollectionProperty(type=PYREC_PG_InspectPanel)
    inspect_context_panel_next_num: IntProperty()
