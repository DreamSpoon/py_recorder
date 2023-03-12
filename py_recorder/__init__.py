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

bl_info = {
    "name": "Python Recorder",
    "description": "Inspect Python object attributes. Record Blender data to Python code. Record Info lines to " \
        "Text / Text Object script so that user actions in Blender can be recreated later by running the script",
    "author": "Dave",
    "version": (0, 4, 1),
    "blender": (2, 80, 0),
    "location": "3DView -> Tools -> Tool -> Py Record Info, Py Exec Object. Right-click Context menu -> " \
        "Add Inspect Panel. Context -> Tool -> Py Inspect",
    "category": "Python",
    "wiki_url": "https://github.com/DreamSpoon/py_recorder#readme",
}

import re
import numpy

import bpy
from bpy.app.handlers import persistent
from bpy.types import (Collection, Object, Panel, PropertyGroup, Text)
from bpy.props import (BoolProperty, BoolVectorProperty, CollectionProperty, EnumProperty, IntProperty,
    PointerProperty, StringProperty)
from bpy.utils import (register_class, unregister_class)

from .inspect import (PYREC_OT_AddInspectPanel, PYREC_OT_RemoveInspectPanel, PYREC_UL_DirAttributeList,
    PYREC_PG_DirAttributeItem, PYREC_OT_InspectOptions, PYREC_OT_InspectPanelAttrZoomIn,
    PYREC_OT_InspectPanelAttrZoomOut, PYREC_OT_InspectPanelArrayIndexZoomIn, PYREC_OT_InspectPanelArrayKeyZoomIn,
    PYREC_UL_StringList, PYREC_OT_RestoreInspectContextPanels, PYREC_OT_InspectRecordAttribute,
    PYREC_OT_InspectCopyAttribute, PYREC_OT_InspectPasteAttribute, PYREC_OT_InspectChoosePy, draw_inspect_panel,
    update_dir_attributes)
from .inspect_exec import (register_inspect_exec_panel_draw_func, unregister_all_inspect_panel_classes)
from .inspect_func import get_inspect_active_type_items
from .object_custom_prop import (CPROP_NAME_INIT_PY, PYREC_OT_OBJ_AddCP_Data, PYREC_OT_OBJ_ModifyInit)
from .driver_editor_ops import (PYREC_OT_DriversToPython, PYREC_OT_SelectAnimdataSrcAll,
    PYREC_OT_SelectAnimdataSrcNone, get_animdata_bool_names)
from .node_editor_ops import PYREC_OT_RecordNodetree
from .view3d_ops import (CP_DATA_TYPE_ITEMS, MODIFY_DATA_TYPE_ITEMS, PYREC_OT_VIEW3D_CopyInfoToObjectText,
    PYREC_OT_VIEW3D_StartRecordInfoLine, PYREC_OT_VIEW3D_StopRecordInfoLine, PYREC_OT_VIEW3D_RunObjectScript,
    get_datablock_for_type)

ANIMDATA_BOOL_NAMES = get_animdata_bool_names()

class PYREC_PT_OBJ_AdjustCustomProp(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = "Py Exec Custom Properties"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def draw(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        layout = self.layout
        act_ob = context.active_object

        layout.label(text="Init")
        box = layout.box()
        if act_ob.get(CPROP_NAME_INIT_PY) is None:
            box.label(text=CPROP_NAME_INIT_PY+":  None")
        else:
            box.prop_search(act_ob, '["'+CPROP_NAME_INIT_PY+'"]', bpy.data,
                            get_datablock_for_type(act_ob[CPROP_NAME_INIT_PY]))
        box.operator(PYREC_OT_OBJ_ModifyInit.bl_idname)

        layout.label(text="New Property")
        box = layout.box()
        box.prop(pr_ir, "add_cp_data_name")
        box.prop(pr_ir, "add_cp_data_type")
        box.prop_search(pr_ir, "add_cp_datablock", bpy.data, pr_ir.add_cp_data_type, text="")
        box.operator(PYREC_OT_OBJ_AddCP_Data.bl_idname)

########################

class PYREC_PT_VIEW3D_RecordInfo(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Py Record Info"

    def draw(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        layout = self.layout

        box = layout.box()
        sub_box = box.box()
        # show 'Stop Record' button if recording is on,
        if pr_ir.record_info_line:
            sub_box.operator(PYREC_OT_VIEW3D_StopRecordInfoLine.bl_idname)
        # show 'Start Record' button if recording is off
        else:
            sub_box.operator(PYREC_OT_VIEW3D_StartRecordInfoLine.bl_idname)

        rec_state = "Off"
        if pr_ir.record_info_line:
            rec_state = "On"
        sub_box.label(text="Recording: " + rec_state)
        box.operator(PYREC_OT_VIEW3D_CopyInfoToObjectText.bl_idname)

        box = layout.box()
        box.label(text="Option")
        sub_box = box.box()
        sub_box.prop(pr_ir, "record_auto_import_bpy")

        sub_box.label(text="Info Line")
        row = sub_box.row(align=True)
        row.prop(pr_ir, "filter_end_line_offset")
        row.prop(pr_ir, "filter_line_count")

        sub_sub_box = sub_box.box()
        row = sub_sub_box.row()
        row.label(text="Type")
        row.label(text="Include/Comment")
        row = sub_sub_box.row()
        row.label(text="Context")
        row.prop(pr_ir, "include_line_type_context", text="")
        row.prop(pr_ir, "comment_line_type_context", text="")
        row = sub_sub_box.row()
        row.label(text="Info")
        row.prop(pr_ir, "include_line_type_info", text="")
        row.prop(pr_ir, "comment_line_type_info", text="")
        row = sub_sub_box.row()
        row.label(text="Macro")
        row.prop(pr_ir, "include_line_type_macro", text="")
        row.prop(pr_ir, "comment_line_type_macro", text="")
        row = sub_sub_box.row()
        row.label(text="Operation")
        row.prop(pr_ir, "include_line_type_operation", text="")
        row.prop(pr_ir, "comment_line_type_operation", text="")
        row = sub_sub_box.row()
        row.label(text="Prev Duplicate")
        row.prop(pr_ir, "include_line_type_prev_dup", text="")
        row.prop(pr_ir, "comment_line_type_prev_dup", text="")
        row = sub_sub_box.row()
        row.label(text="Py Recorder")
        row.prop(pr_ir, "include_line_type_py_rec", text="")
        row.prop(pr_ir, "comment_line_type_py_rec", text="")

        sub_box.label(text="Object")
        sub_box.prop(pr_ir, "root_init")
        sub_box.prop(pr_ir, "create_root_object")
        if pr_ir.create_root_object:
            sub_box.prop(pr_ir, "root_collection")
        sub_box.prop(pr_ir, "use_text_object")
        if pr_ir.use_text_object:
            sub_box.prop(pr_ir, "output_text_object")
            sub_box.prop(pr_ir, "text_object_collection")
        else:
            sub_box.prop(pr_ir, "output_text")

class PYREC_PT_VIEW3D_ExecObject(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Py Exec Object"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        layout = self.layout
        box = layout.box()
        box.label(text="Run Object '__init__'")
        box.operator(PYREC_OT_VIEW3D_RunObjectScript.bl_idname)
        box.prop(pr_ir, "use_temp_text")
        box.prop(pr_ir, "run_auto_import_bpy")

########################

class PYREC_PT_RecordNodetree(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_label = "Py Record Nodetree"

    def draw(self, context):
        ntr = context.window_manager.py_rec.record_options.nodetree
        layout = self.layout
        box = layout.box()
        box.operator(PYREC_OT_RecordNodetree.bl_idname)
        box = layout.box()
        box.label(text="General Options")
        box.prop(ntr, "num_space_pad")
        box.prop(ntr, "keep_links")
        box.prop(ntr, "make_function")
        box.prop(ntr, "delete_existing")
        box.prop(ntr, "ng_output_min_max_def")
        box = layout.box()
        box.label(text="Node Attribute Options")
        box.prop(ntr, "write_attrib_name")
        box.prop(ntr, "write_attrib_select")
        sub_box = box.box()
        sub_box.prop(ntr, "write_attrib_width_and_height")
        sub_box.prop(ntr, "write_loc_decimal_places")
        box = layout.box()
        box.label(text="Write Defaults Options")
        box.prop(ntr, "write_default_values")
        box.prop(ntr, "write_linked_default_values")

########################

class PYREC_PT_RecordDriver(bpy.types.Panel):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_label = "Py Record Drivers"

    def draw(self, context):
        layout = self.layout
        dr = context.window_manager.py_rec.record_options.driver

        box = layout.box()
        box.label(text="Driver Data Source")
        box.operator(PYREC_OT_DriversToPython.bl_idname)
        box.prop(dr, "num_space_pad")
        box.prop(dr, "make_function")
        box.operator(PYREC_OT_SelectAnimdataSrcAll.bl_idname)
        box.operator(PYREC_OT_SelectAnimdataSrcNone.bl_idname)
        box = box.box()
        for i in range(len(ANIMDATA_BOOL_NAMES)):
            box.prop(dr, "animdata_bool_vec", index=i, text=ANIMDATA_BOOL_NAMES[i])

########################

class PYREC_PG_InspectPanelOptions(PropertyGroup):
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
    display_value_attributes: BoolProperty(name="Attributes List", description="Display Inspect Attributes area, " +
        "to inspect list of attributes of current Inspect value (i.e. view result of dir() in list format)",
        default=True, options={'HIDDEN'})
    display_value_selector: BoolProperty(name="Try value entry", description="Try to display attribute value entry " +
        "box, to allow real-time editing of attribute value. Display value as string if try fails", default=True,
        options={'HIDDEN'})
    display_dir_attribute_type: BoolProperty(name="Type", description="Display Type column in Attribute list",
        default=True, options={'HIDDEN'})
    display_dir_attribute_value: BoolProperty(name="Value", description="Display Value column in Attribute list",
        default=True, options={'HIDDEN'})

def populate_index_strings(self, context):
    # if index string collection is not empty then create array for use with EnumProperty
    if len(self.array_key_set) > 0:
        output = []
        for index_str in self.array_key_set:
            output.append( (index_str.name, index_str.name, "") )
        return output
    # return empty
    return [ (" ", "", "") ]

def set_array_index(self, value):
    if value < 0 or value > self.array_index_max:
        return
    self["array_index"] = value
    return

def get_array_index(self):
    return self.get("array_index", 0)

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
        "Python code to run before running inspect value code", type=Text)

    inspect_py_type: EnumProperty(name="Py Type", items=[
        ("active", "Active", "Active thing will be inspected (e.g. active Object in View3D context). Not yet " +
         "available in all contexts"),
        ("custom", "Custom", "Custom string of code will be run, and run result will be inspected"),
        ("datablock", "Datablock", "Datablock includes all data collections under 'bpy.data'") ],
        description="Type of Python object to inspect", default="custom")
    inspect_active_type: EnumProperty(name="Active Type", items=get_inspect_active_type_items)
    inspect_datablock_type: EnumProperty(name="Type", items=CP_DATA_TYPE_ITEMS, default="objects",
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

    dir_item_value_str: StringProperty()
    dir_item_value_typename_str: StringProperty()

    dir_item_doc_lines: CollectionProperty(type=PropertyGroup)
    dir_item_doc_lines_index: IntProperty()

class PYREC_PG_InspectPanelCollection(PropertyGroup):
    inspect_context_panels: CollectionProperty(type=PYREC_PG_InspectPanel)
    inspect_context_panel_next_num: IntProperty()

class PYREC_PG_AttributeRecordOptions(PropertyGroup):
    copy_from: EnumProperty(name = "From", description="Record Python code of Single Attribute or All Attributes of " +
        "current inspect value", items=[ ("single_attribute", "Single Attribute", ""),
                                         ("all_attributes", "All Attributes", "") ], default="single_attribute")
    copy_to: EnumProperty(name="To", description="Record attribute(s) as Python code to this", items=[
            ("clipboard", "Clipboard", "Record Python code to clipboard. Paste with 'Ctrl-V'"),
            ("new_text", "New Text", "Record Python code to new Text"),
            ("text", "Text", "Record Python code to existing Text"), ], default="clipboard")
    copy_to_text: PointerProperty(description="Text (in Text Editor) to receive output", type=Text)
    include_value: BoolProperty(name="Value", description="Include attribute value in recorded Python output " +
        "(with '=')", default=True)
    comment_type: BoolProperty(name="Type Comment", description="Include Python code with attribute value's type",
        default=True)
    comment_doc: BoolProperty(name="__doc__ Comment", description="Include Python code with attribute value's " +
        "'__doc__' attribute value (if it exists)", default=True)

class PYREC_PG_DriverRecordOptions(PropertyGroup):
    num_space_pad: IntProperty(name="Num Space Pad", description="Number of spaces to prepend to each " +
        "line of code output in text-block", default=4, min=0)
    make_function: BoolProperty(name="Make into Function", description="Add lines of Python code to " +
        "create runnable script (instead of just the bare essential code)", default=True)
    animdata_bool_vec: BoolVectorProperty(size=len(ANIMDATA_BOOL_NAMES),
                                           default=tuple(numpy.ones((len(ANIMDATA_BOOL_NAMES)), dtype=int)))

def text_object_poll(self, object):
    return object.type == 'FONT'

class PYREC_PG_InfoRecordOptions(PropertyGroup):
    create_root_object: BoolProperty(name="Create Root", description="New root Object will be created, instead of " +
        "using active Object as root (Text / Text Object will be linked to root Object)",
        default=False)
    root_init: BoolProperty(name="Root " + CPROP_NAME_INIT_PY, description="Create Custom Property '" +
        CPROP_NAME_INIT_PY + "' on root Object, so root Object can be 'run' by running its '" + CPROP_NAME_INIT_PY +
        "' script", default=True)
    use_text_object: BoolProperty(name="Use Text Object", description="Text Object will be used for output, " +
        "instead of Text (in Text Editor)", default=False)
    output_text_object: PointerProperty(name="Output Text Object", description="Text Object to receive output",
        type=Object, poll=text_object_poll)
    output_text: PointerProperty(name="Output Text", description="Text (in Text Editor) to receive " +
        "output", type=Text)
    filter_end_line_offset: IntProperty(name="Offset", description="Filter End Line Offset: When copying lines " +
        "from Info, last filtered line copied is most recent filtered line minus Filtered Line Offset",
        default=0, min=0)
    filter_line_count: IntProperty(name="Count", description="Filter Line Count: Number of filtered lines to copy " +
        "from Info", default=10, min=1)
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
        "Recorder operation or state change (lines beginning with \"bpy.ops.view3d_ops\" or " +
        "\"bpy.context.scene.view3d_ops\")", default=False)
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
        "Recorder operations or state changes (lines beginning with \"bpy.ops.view3d_ops\" or " +
        "\"bpy.context.scene.view3d_ops\")", default=True)
    root_collection: PointerProperty(name="Root", description="New root Objects will be put into this collection",
        type=Collection)
    text_object_collection: PointerProperty(name="Text", description="New Text Objects will be put into this " +
        "collection", type=Collection)
    add_cp_data_name: StringProperty(name="Name", description="Custom Property name", default="")
    add_cp_data_type: EnumProperty(name="Type", description="Data type", items=CP_DATA_TYPE_ITEMS, default="objects")
    add_cp_datablock: StringProperty(name="Data", description="Custom Property value", default="")
    modify_data_type: EnumProperty(name="Type", description="Type of data, either Text or Text Object",
        items=MODIFY_DATA_TYPE_ITEMS)
    modify_data_text: PointerProperty(name="Data", description="Text (see Blender's builtin Text Editor) to " +
        "use for active Object's '"+CPROP_NAME_INIT_PY+"' script", type=Text)
    modify_data_obj: PointerProperty(name="Data", description="Text Object to use for active Object's '" +
        CPROP_NAME_INIT_PY+"' script", type=Object, poll=text_object_poll)
    record_info_line: BoolProperty(name="Record Info line", description="", default=False)
    record_info_start_line_offset: IntProperty(name="Start Record Info line count", description="", default=0)
    record_auto_import_bpy: BoolProperty(name="Auto 'import bpy'", description="Automatically prepend line to " +
        "recorded / copied script, to prevent run script error: \"NameError: name 'bpy' is not defined\"",
        default=True)
    run_auto_import_bpy: BoolProperty(name="Auto 'import bpy'", description="If necessary, automatically prepend " +
        "line to script before run, and remove line after run, to prevent error: \"NameError: name 'bpy' is " +
        "not defined\"", default=True)
    use_temp_text: BoolProperty(name="Run Temp Text", description="Copy text from Text Object to a Text (in Text " +
        "Editor) before running script", default=True)

class PYREC_PG_NodetreeRecordOptions(PropertyGroup):
    num_space_pad: IntProperty(name="Num Space Pad", description="Number of spaces to prepend to each " +
        "line of code output in text-block", default=4, min=0)
    keep_links: BoolProperty(name="Keep Links List", description="Add created links to a list variable",
        default=False)
    make_function: BoolProperty(name="Make into Function", description="Add lines of Python code to " +
        "create runnable script (instead of just the bare essential code)", default=True)
    delete_existing: BoolProperty(name="Delete Existing Shader",
        description="Include code in the output that deletes all nodes in Shader Material / Geometry Node Setup " +
        "before creating new nodes", default=True)
    write_loc_decimal_places: IntProperty(name="Location Decimal Places", description="Number of " +
        "decimal places to use when writing location values", default=0)
    write_default_values: BoolProperty(name="Write Defaults", description="Write node attributes " +
        "that are set to default values (e.g. node attributes: label, name)", default=False)
    write_linked_default_values: BoolProperty(name="Linked Default Values", description="Write default " +
        "values, of node inputs and outputs, where the input/output is linked to another node", default=False)
    write_attrib_name: BoolProperty(name="Name", description="Include node attribute 'name'", default=False)
    write_attrib_width_and_height: BoolProperty(name="Width and Height", description="Include node " +
        "attributes for width and height", default=False)
    write_attrib_select: BoolProperty(name="Select", description="Include node " +
        "attribute for select state (e.g. selected nodes can be 'marked' for easy search later)", default=False)
    ng_output_min_max_def: BoolProperty(name="Output Min/Max/Default", description="Include Minimum, Maximum, " +
        "and Default value for each node group output", default=False)

class PYREC_PG_RecordOptions(PropertyGroup):
    attribute: PointerProperty(type=PYREC_PG_AttributeRecordOptions)
    driver: PointerProperty(type=PYREC_PG_DriverRecordOptions)
    info: PointerProperty(type=PYREC_PG_InfoRecordOptions)
    nodetree: PointerProperty(type=PYREC_PG_NodetreeRecordOptions)

class PYREC_PG_PyRec(PropertyGroup):
    inspect_context_collections: CollectionProperty(type=PYREC_PG_InspectPanelCollection)
    record_options: PointerProperty(type=PYREC_PG_RecordOptions)

classes = [
    PYREC_OT_RecordNodetree,
    PYREC_PT_RecordNodetree,
    PYREC_OT_OBJ_ModifyInit,
    PYREC_OT_OBJ_AddCP_Data,
    PYREC_PT_OBJ_AdjustCustomProp,
    PYREC_OT_VIEW3D_StartRecordInfoLine,
    PYREC_OT_VIEW3D_StopRecordInfoLine,
    PYREC_OT_VIEW3D_CopyInfoToObjectText,
    PYREC_PT_VIEW3D_RecordInfo,
    PYREC_OT_VIEW3D_RunObjectScript,
    PYREC_PT_VIEW3D_ExecObject,
    PYREC_OT_AddInspectPanel,
    PYREC_OT_RemoveInspectPanel,
    PYREC_OT_InspectOptions,
    PYREC_OT_InspectPanelAttrZoomIn,
    PYREC_OT_InspectPanelAttrZoomOut,
    PYREC_OT_InspectPanelArrayIndexZoomIn,
    PYREC_OT_InspectPanelArrayKeyZoomIn,
    PYREC_OT_DriversToPython,
    PYREC_OT_SelectAnimdataSrcAll,
    PYREC_OT_SelectAnimdataSrcNone,
    PYREC_OT_RestoreInspectContextPanels,
    PYREC_OT_InspectRecordAttribute,
    PYREC_OT_InspectCopyAttribute,
    PYREC_OT_InspectPasteAttribute,
    PYREC_OT_InspectChoosePy,
    PYREC_PT_RecordDriver,
    PYREC_PG_DirAttributeItem,
    PYREC_UL_DirAttributeList,
    PYREC_UL_StringList,
    PYREC_PG_InspectPanelOptions,
    PYREC_PG_InspectPanel,
    PYREC_PG_InspectPanelCollection,
    PYREC_PG_AttributeRecordOptions,
    PYREC_PG_DriverRecordOptions,
    PYREC_PG_InfoRecordOptions,
    PYREC_PG_NodetreeRecordOptions,
    PYREC_PG_RecordOptions,
    PYREC_PG_PyRec,
]

def draw_inspect_context_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(PYREC_OT_AddInspectPanel.bl_idname)

context_type_draw_removes = []
def append_inspect_context_menu_all():
    for type_name in dir(bpy.types):
        # e.g. 'VIEW3D_MT_object_context_menu', 'NODE_MT_context_menu'
        if not re.match("^[A-Za-z0-9_]+_MT[A-Za-z0-9_]*_context_menu$", type_name):
            continue
        attr_value = getattr(bpy.types, type_name)
        if attr_value is None:
            continue
        try:
            attr_value.append(draw_inspect_context_menu)
            context_type_draw_removes.append(attr_value)
        except:
            pass

def remove_inspect_context_menu_all():
    for d in context_type_draw_removes:
        d.remove(draw_inspect_context_menu)

def duplicate_prop(to_prop, from_prop):
    if isinstance(from_prop, bpy.types.PropertyGroup):
        for attr_name in dir(from_prop):
            attr_value = getattr(from_prop, attr_name)
            if attr_name in [ "bl_rna", "rna_type", "id_data" ] or callable(attr_value) or attr_name.startswith("__"):
                continue
            if isinstance(attr_value, bpy.types.PropertyGroup) or \
                (hasattr(attr_value, "__len__") and not isinstance(attr_value, str)):
                duplicate_prop(getattr(to_prop, attr_name), attr_value)
            else:
                setattr(to_prop, attr_name, attr_value)
    elif hasattr(from_prop, "__len__"):
        if hasattr(to_prop, "clear") and callable(getattr(to_prop, "clear")):
            to_prop.clear()
        for index, from_item in enumerate(from_prop):
            if hasattr(to_prop, "clear") and callable(getattr(to_prop, "clear")):
                to_item = to_prop.add()
                to_item.name = from_item.name
            if isinstance(from_item, bpy.types.PropertyGroup) or \
                (hasattr(from_item, "__len__") and not isinstance(from_item, str)):
                duplicate_prop(to_item, from_item)
            else:
                to_prop[index] = from_item

def load_py_rec_from_scene():
    # copy to WindowManager (singleton, only one) from first Scene (one or more, never zero)
    duplicate_prop(bpy.data.window_managers[0].py_rec, bpy.data.scenes[0].py_rec)

def save_py_rec_to_scene():
    # copy to first Scene (one or more, never zero) from WindowManager (singleton, only one)
    duplicate_prop(bpy.data.scenes[0].py_rec, bpy.data.window_managers[0].py_rec)

@persistent
def load_post_handler_func(dummy):
    # restore state of py_rec before restoring context panels, because restore requires data from py_rec
    load_py_rec_from_scene()
    # register Py Inspect panel UI classes, using data from (now) loaded .blend file
    bpy.ops.py_rec.restore_inspect_context_panels()

@persistent
def save_pre_handler_func(dummy):
    # save state of py_rec before saving .blend file, so Py Inspect panel info is saved
    save_py_rec_to_scene()

def register():
    register_inspect_exec_panel_draw_func(draw_inspect_panel)
    for cls in classes:
        register_class(cls)
    # Scene property is used so py_rec state is saved with .blend file data, because WindowManager properties are not
    # saved with .blend file.
    bpy.types.Scene.py_rec = PointerProperty(type=PYREC_PG_PyRec)
    # WindowManager property is used so the same Py Inspect panel properties are available across all Scenes in loaded
    # .blend file. Creating new Scenes, and switching active Scenes, causes difficulties linking data for Py Inspect
    # panels with UI classes for Py Inspect panels - because UI classes (Py Inspect panels) are the same across all
    # Scenes, but py_rec properties data is different for each Scene.
    bpy.types.WindowManager.py_rec = PointerProperty(type=PYREC_PG_PyRec)
    if not load_post_handler_func in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post_handler_func)
    if not save_pre_handler_func in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(save_pre_handler_func)
    # append 'Add Inspect Panel' button to all Context menus (all Context types)
    append_inspect_context_menu_all()

def unregister():
    # remove 'Add Inspect Panel' button from all Context menus (all Context types)
    remove_inspect_context_menu_all()
    # unregister Py Inspect panel UI classes
    unregister_all_inspect_panel_classes()
    if save_pre_handler_func in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(save_pre_handler_func)
    if load_post_handler_func in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post_handler_func)
    del bpy.types.WindowManager.py_rec
    del bpy.types.Scene.py_rec
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
