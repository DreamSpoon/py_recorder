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
    "description": "Record Info lines to Texts / Text Objects so that any Blender data can be " \
        "recreated later by running a script. Inspect any Python object with dir() list and more.",
    "author": "Dave",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "3DView -> Tools -> Py Rec, Object -> Py Rec",
    "category": "Python",
}

import bpy
from bpy.types import (Collection, Object, Panel, PropertyGroup, Text)
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, IntProperty, PointerProperty, StringProperty)
from bpy.utils import (register_class, unregister_class)

from .object_custom_prop import (PYREC_OT_OBJ_AddCP_Data, PYREC_OT_OBJ_ModifyInit)
from .view3d_tools import (CP_DATA_TYPE_ITEMS, CPROP_NAME_INIT_PY, MODIFY_DATA_TYPE_ITEMS,
    PYREC_OT_VIEW3D_CopyInfoToObjectText, PYREC_OT_VIEW3D_StartRecordInfoLine, PYREC_OT_VIEW3D_StopRecordInfoLine,
    PYREC_OT_VIEW3D_RunObjectScript, get_datablock_for_type)
from .inspect import (PYREC_OT_AddInspectPanel, PYREC_OT_RemoveInspectPanel,
    PYREC_OT_InspectExecRefresh, PYREC_OT_InspectDatablockRefresh, PYREC_UL_InspectDirList,
    PYREC_PG_InspectDirItem, update_inspect_dir_list, PYREC_OT_InspectOptions, PYREC_OT_InspectPanelZoomIn,
    PYREC_OT_InspectPanelZoomOut)

class PYREC_PT_OBJ_AdjustCustomProp(Panel):
    bl_label = "Py Rec"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def draw(self, context):
        pr_ir = context.scene.py_rec.info_report
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

class PYREC_PT_VIEW3D_Record(Panel):
    bl_category = "Py Rec"
    bl_label = "Record"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        pr_ir = context.scene.py_rec.info_report
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
        sub_box.prop(pr_ir, "create_root_object")
        sub_box.prop(pr_ir, "root_init")
        sub_box.prop(pr_ir, "root_collection")
        sub_box.prop(pr_ir, "use_text_object")
        if pr_ir.use_text_object:
            sub_box.prop(pr_ir, "output_text_object")
            sub_box.prop(pr_ir, "text_object_collection")
        else:
            sub_box.prop(pr_ir, "output_text")

class PYREC_PT_VIEW3D_Play(Panel):
    bl_category = "Py Rec"
    bl_label = "Play"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pr_ir = context.scene.py_rec.info_report
        layout = self.layout
        box = layout.box()
        box.label(text="Play")
        box.operator(PYREC_OT_VIEW3D_RunObjectScript.bl_idname)
        box.prop(pr_ir, "use_temp_text")
        box.prop(pr_ir, "run_auto_import_bpy")

########################

class PYREC_PG_InspectPanelOptions(PropertyGroup):
    display_attr_doc: BoolProperty(name="__doc__", description="Display '__doc__' attribute, which may contain " +
        "relevant information about current value", default=True)
    display_attr_bl_description: BoolProperty(name="bl_description", description="Display 'bl_description' " +
        "attribute, which may contain relevant information about current value", default=True)
    display_attr_type_only: BoolProperty(name="Display only", description="Display only selected types of " +
        "attributes in Value Attributes area", default=False)
    display_attr_type_function: BoolProperty(name="Function", description="Display 'function' type attributes in " +
        "Value Attributes area", default=False)
    display_attr_type_builtin: BoolProperty(name="Builtin", description="Display 'builtin' type attributes in " +
        "Value Attributes area ('builtin' types have names beginning, and ending, with '__' , e.g. '__doc__')",
        default=True)
    display_attr_type_bl: BoolProperty(name="bl_", description="Display 'Blender builtin' type attributes in " +
        "Value Attributes area. 'Blender builtin' type attributes have names beginning with 'bl_' ", default=True)
    display_datablock_refresh: BoolProperty(name="Datablock Refresh", description="Display 'Datablock Refresh' " +
        "area, to inspect by Datablock (e.g. by Camera, Image, Object)", default=True)
    display_exec_refresh: BoolProperty(name="Exec Refresh", description="Display 'Exec Refresh' area, to inspect " +
        "by custom string exec() result", default=True)
    display_value_attributes: BoolProperty(name="Value Attributes", description="Display 'Value Attributes' area, " +
        "to inspect attributes of current Inspect value. i.e. view result of dir() in list format", default=True)
    display_value_selector: BoolProperty(name="Try value entry", description="Try to display attribute value entry " +
        "box, to allow real-time editing of attribute value. Display value as string if try fails", default=True)
    display_dir_attribute_type: BoolProperty(name="Type", description="Display Type column in Attribute list",
        default=True)
    display_dir_attribute_value: BoolProperty(name="Value", description="Display Value column in Attribute list",
        default=True)

class PYREC_PG_InspectPanelProps(PropertyGroup):
    inspect_data_type: EnumProperty(name="Type", description="Datablock type", items=CP_DATA_TYPE_ITEMS,
        default="objects")
    inspect_datablock: StringProperty(name="Inspect datablock Name", description="Inspect datablock name", default="")
    inspect_exec_str: StringProperty(name="Inspect Exec", description="Python string that will be run and result " +
        "returned when Refresh is used", default="bpy.data")

    dir_listing_exec_str: StringProperty()
    dir_listing: CollectionProperty(type=PYREC_PG_InspectDirItem)
    dir_listing_index: IntProperty(update=update_inspect_dir_list)

    dir_item_exec_str: StringProperty()
    dir_item_value_str: StringProperty()
    dir_item_value_typename_str: StringProperty()
    dir_item_doc_str: StringProperty()
    dir_item_bl_description_str: StringProperty()

    panel_options: PointerProperty(type=PYREC_PG_InspectPanelOptions)

class PYREC_PG_InspectPanel(PropertyGroup):
    # inspect_panel_number uniquely identifies this PropertyGroup, to match with an Inspect panel in context
    inspect_panel_number: IntProperty()
    panel_props: PointerProperty(type=PYREC_PG_InspectPanelProps)

class PYREC_PG_InspectPanelCollection(PropertyGroup):
    inspect_context_panels: CollectionProperty(type=PYREC_PG_InspectPanel)
    inspect_context_panel_next_num: IntProperty()

def text_object_poll(self, object):
    return object.type == 'FONT'

class PYREC_PG_InfoReport(PropertyGroup):
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
        "Recorder operation or state change (lines beginning with \"bpy.ops.view3d_tools\" or " +
        "\"bpy.context.scene.view3d_tools\")", default=False)
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
        "Recorder operations or state changes (lines beginning with \"bpy.ops.view3d_tools\" or " +
        "\"bpy.context.scene.view3d_tools\")", default=True)
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

class PYREC_PG_PyRec(PropertyGroup):
    info_report: PointerProperty(type=PYREC_PG_InfoReport)
    inspect_context_collections: CollectionProperty(type=PYREC_PG_InspectPanelCollection)

classes = [
    PYREC_PT_OBJ_AdjustCustomProp,
    PYREC_OT_OBJ_ModifyInit,
    PYREC_OT_OBJ_AddCP_Data,
    PYREC_PT_VIEW3D_Record,
    PYREC_OT_VIEW3D_StartRecordInfoLine,
    PYREC_OT_VIEW3D_StopRecordInfoLine,
    PYREC_OT_VIEW3D_CopyInfoToObjectText,
    PYREC_PT_VIEW3D_Play,
    PYREC_OT_VIEW3D_RunObjectScript,
    PYREC_OT_AddInspectPanel,
    PYREC_OT_RemoveInspectPanel,
    PYREC_OT_InspectOptions,
    PYREC_OT_InspectExecRefresh,
    PYREC_OT_InspectDatablockRefresh,
    PYREC_OT_InspectPanelZoomIn,
    PYREC_OT_InspectPanelZoomOut,
    PYREC_PG_InspectDirItem,
    PYREC_UL_InspectDirList,
    PYREC_PG_InspectPanelOptions,
    PYREC_PG_InspectPanelProps,
    PYREC_PG_InspectPanel,
    PYREC_PG_InspectPanelCollection,
    PYREC_PG_InfoReport,
    PYREC_PG_PyRec,
]

def draw_inspect_context_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(PYREC_OT_AddInspectPanel.bl_idname)

def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.py_rec = PointerProperty(type=PYREC_PG_PyRec)
    bpy.types.VIEW3D_MT_object_context_menu.append(draw_inspect_context_menu)

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.py_rec
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_inspect_context_menu)

if __name__ == "__main__":
    register()
