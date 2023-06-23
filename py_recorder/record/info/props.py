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
from bpy.props import (BoolProperty, EnumProperty, IntProperty, PointerProperty, StringProperty)
from bpy.types import PropertyGroup

from .func import text_object_poll
from ...bpy_value_string import BPY_DATA_TYPE_ITEMS
from ...object_custom_prop import CPROP_NAME_INIT_PY

class PYREC_PG_InfoRecordOptions(PropertyGroup):
    create_root_object: BoolProperty(name="Create Root", description="New root Object will be created, instead of " +
        "using active Object as root (Text / Text Object will be linked to root Object)",
        default=False)
    root_init: BoolProperty(name="Root " + CPROP_NAME_INIT_PY, description="Create Custom Property '" +
        CPROP_NAME_INIT_PY + "' on root Object, so root Object can be 'run' by running its '" + CPROP_NAME_INIT_PY +
        "' script", default=True)
    use_text_object: BoolProperty(name="Use Text Object", description="Text Object will be used for output, " +
        "instead of Text (in Text Editor)", default=False)
    output_text_object: PointerProperty(name="Output Text Object", description="Text Object to receive output. " +
        "If empty then new Text Object will be created", type=bpy.types.Object, poll=text_object_poll)
    output_text: PointerProperty(name="Output Text", description="Text (in Text Editor) to receive " +
        "output. If empty then new Text is created with name 'InfoText'", type=bpy.types.Text)
    filter_line_count: IntProperty(name="Line Count", description="Filter Line Count: Number of filtered lines to " +
        "copy from Info", default=20, min=1)
    include_line_type_context: BoolProperty(name="Context", description="Copy Context type Info lines (lines " +
        "beginning with \"bpy.context\")", default=True)
    include_line_type_info: BoolProperty(name="Info", description="Copy general information type Info lines " +
        "(example: console error output)", default=False)
    include_line_type_macro: BoolProperty(name="Macro", description="Copy Info lines that cannot be run",
        default=False)
    include_line_type_operation: BoolProperty(name="Operation", description="Copy Operation type Info lines (lines " +
        "beginning with \"bpy.ops\")", default=True)
    include_line_type_prev_dup: BoolProperty(name="Prev Duplicate", description="Copy Info lines that have " +
        "previous duplicates (i.e. the same \"bpy.ops\" operation repeated, or the same \"bpy.context\" value set). " +
        "If set to False, then only most recent operation / context change is copied", default=True)
    include_line_type_py_rec: BoolProperty(name="Py Recorder", description="Copy Info lines related to Py " +
        "Recorder operation or state change (lines beginning with \"bpy.ops.py_rec\" or " +
        "\"bpy.context.scene.py_rec\")", default=False)
    comment_line_type_context: BoolProperty(name="Context", description="Comment out Context type Info " +
        "lines (lines beginning with \"bpy.context\")", default=False)
    comment_line_type_info: BoolProperty(name="Info", description="Comment out general information type Info " +
        "lines (example: console error output)", default=True)
    comment_line_type_macro: BoolProperty(name="Macro", description="Comment out Macro type Info " +
        "lines", default=True)
    comment_line_type_operation: BoolProperty(name="Operation", description="Comment out Operation type Info lines " +
        "(lines beginning with \"bpy.ops\"", default=False)
    comment_line_type_prev_dup: BoolProperty(name="Prev Duplicate", description="Comment out previous duplicate " +
        "lines from Info", default=True)
    comment_line_type_py_rec: BoolProperty(name="Py Recorder", description="Comment out Info lines related to Py " +
        "Recorder operations or state changes (lines beginning with \"bpy.ops.py_rec\" or " +
        "\"bpy.context.scene.py_rec\")", default=True)
    add_cp_data_name: StringProperty(name="Name", description="Custom Property name", default="")
    add_cp_data_type: EnumProperty(name="Type", description="Data type", items=BPY_DATA_TYPE_ITEMS, default="objects")
    add_cp_datablock: StringProperty(name="Data", description="Custom Property value", default="")
    modify_data_type: EnumProperty(name="Type", description="Type of data, either Text or Text Object",
        items=[ ("texts", "Text", "", 1), ("objects", "Text Object", "", 2), ("None", "None", "", 3) ] )
    modify_data_text: PointerProperty(name="Data", description="Text (see Blender's builtin Text Editor) to " +
        "use for active Object's '"+CPROP_NAME_INIT_PY+"' script", type=bpy.types.Text)
    modify_data_obj: PointerProperty(name="Data", description="Text Object to use for active Object's '" +
        CPROP_NAME_INIT_PY+"' script", type=bpy.types.Object, poll=text_object_poll)
    record_info_line: BoolProperty(name="Record Info line", description="", default=False)
    record_info_start_line_offset: IntProperty(name="Start Record Info line count", description="", default=0)
    record_auto_import_bpy: BoolProperty(name="Auto 'import bpy'", description="Automatically prepend line to " +
        "recorded / copied script, to prevent run script error: \"NameError: name 'bpy' is not defined\"",
        default=False)
