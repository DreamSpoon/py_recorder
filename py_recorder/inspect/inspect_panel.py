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

import inspect
import re
import traceback

import mathutils
import bpy
from bpy.types import (Operator, PropertyGroup, UIList)
from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, IntProperty, PointerProperty, StringProperty)
from bpy.utils import unregister_class

from .inspect_options import PYREC_OT_InspectOptions
from .inspect_func import (get_dir, get_pre_exec_str, get_inspect_context_panel, remove_last_py_attribute,
    match_inspect_panel_name, get_active_thing_inspect_str, get_inspect_active_type_items)
from .inspect_exec import (get_inspect_exec_result, refresh_inspect_exec_result, register_inspect_panel,
    unregister_inspect_panel)
from ..bpy_value_string import (BPY_DATA_TYPE_ITEMS, bpy_value_to_string)
from ..log_text import (LOG_TEXT_NAME, log_text_append)

RECORD_ATTRIBUTE_TEXT_NAME = "pyrec_attribute.py"

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

def get_dir_attribute_exec_str(base, attr_name):
    # if exec str is '.', which means 'self' is selected, then do not append attribute name
    if attr_name == ".":
        return base
    return base + "." + attr_name

# filter out values that do not have __doc__, and empty __doc__, then return clean doc
def get_relevant_doc(value):
    if value != None and not isinstance(value, (bool, dict, float, int, list, set, str, tuple, mathutils.Color,
        mathutils.Euler, mathutils.Matrix, mathutils.Quaternion, mathutils.Vector) ):
        return inspect.getdoc(value)
    return None

# split 'input_str' into separate lines, and add each line to 'lines_coll'
def string_to_lines_collection(input_str, lines_coll):
    if input_str is None or lines_coll is None:
        return
    for str_line in input_str.splitlines():
        new_item = lines_coll.add()
        new_item.name = str_line

def set_array_index(self, value):
    if value < 0 or value > self.array_index_max:
        return
    self["array_index"] = value
    return

def get_array_index(self):
    return self.get("array_index", 0)

def populate_index_strings(self, context):
    # if index string collection is not empty then create array for use with EnumProperty
    if len(self.array_key_set) > 0:
        output = []
        for index_str in self.array_key_set:
            output.append( (index_str.name, index_str.name, "") )
        return output
    # return empty
    return [ (" ", "", "") ]

def update_dir_attributes(self, value):
    panel_props = self
    panel_props.dir_item_value_str = ""
    panel_props.dir_item_value_typename_str = ""
    panel_props.dir_item_doc_lines.clear()
    # quit if dir() listing is empty
    if len(panel_props.dir_attributes) < 1:
        return
    attr_name = panel_props.dir_attributes[panel_props.dir_attributes_index].name
    # get the current result value
    result_value = get_inspect_exec_result()
    # get the current result attribute's value
    if attr_name == ".":
        attr_value = result_value
    elif result_value != None and hasattr(result_value, attr_name):
        attr_value = getattr(result_value, attr_name)
    else:
        attr_value = None
    panel_props.dir_item_value_str = str(attr_value)
    # set 'type name' label
    panel_props.dir_item_value_typename_str = type(attr_value).__name__
    # set '__doc__' label, if available as string type
    string_to_lines_collection(get_relevant_doc(attr_value), panel_props.dir_item_doc_lines)

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

    dir_item_value_str: StringProperty()
    dir_item_value_typename_str: StringProperty()

    dir_item_doc_lines: CollectionProperty(type=PropertyGroup)
    dir_item_doc_lines_index: IntProperty()

class PYREC_PG_InspectPanelCollection(PropertyGroup):
    inspect_context_panels: CollectionProperty(type=PYREC_PG_InspectPanel)
    inspect_context_panel_next_num: IntProperty()

def draw_panel_dir_attribute_value(layout, panel_props, panel_options):
    # display value selector, if enabled and value is available
    result_value = None
    attr_name = panel_props.dir_attributes[panel_props.dir_attributes_index].name
    attr_val = None
    if panel_options.display_value_selector:
        if attr_name == ".":
            first_part, last_part = remove_last_py_attribute(panel_props.dir_inspect_exec_str)
            if first_part != None and last_part != None:
                result_value = get_inspect_exec_result()
                # if last part is indexed then force value to be displayed as label
                if (last_part[0]+last_part[-1]) == "[]":
                    result_value = None
                else:
                    attr_name = last_part
        else:
            result_value = get_inspect_exec_result()
    # try to use a real-time entry field (selector), and display label string if real-time entry field fails
    if result_value != None and attr_name != "bl_rna" and not attr_name.startswith("__") and \
        hasattr(result_value, attr_name):
        attr_val = getattr(result_value, attr_name)
        # do not display if attribute value is None or if it is a zero-length list/tuple
        if attr_val != None and not (isinstance(attr_val, (list, tuple)) and len(attr_val) == 0) and \
            not callable(attr_val):
            try:
                layout.prop(result_value, attr_name, text="Value")
                return
            except:
                pass
    layout.label(text="Value: " + panel_props.dir_item_value_str)

def draw_inspect_panel(self, context):
    context_name = context.space_data.type
    # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
    if context_name == "PROPERTIES":
        context_name = "VIEW_3D"
    ic_panel = get_inspect_context_panel(self.panel_num, context_name,
                                         context.window_manager.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_options = ic_panel.panel_options
    if panel_options is None:
        return
    layout = self.layout
    box = layout.box()
    # top row of Py Inspect panel buttons, always visible
    row = box.row()
    row.operator(PYREC_OT_RemoveInspectPanel.bl_idname, icon='REMOVE', text="").panel_num = self.panel_num
    row.separator()
    row.operator(PYREC_OT_InspectOptions.bl_idname, icon='OPTIONS', text="").panel_num = self.panel_num
    row.separator()
    row.operator(PYREC_OT_InspectChoosePy.bl_idname, icon='HIDE_OFF', text="").panel_num = self.panel_num
    row.separator()
    row.operator(PYREC_OT_InspectPanelAttrZoomOut.bl_idname, icon='ZOOM_OUT', text="").panel_num = self.panel_num
    # array index / key
    if panel_options.display_value_attributes:
        box = layout.box()
        array_index_key_type = ic_panel.array_index_key_type
        if array_index_key_type == "int" or array_index_key_type == "str" or array_index_key_type == "int_str":
            sub_box = box.box()
            sub_box.label(text="Index Item Count: "+str(max(len(ic_panel.array_key_set),
                                                            ic_panel.array_index_max+1)))
        if array_index_key_type == "int" or array_index_key_type == "int_str":
            row = sub_box.row()
            row.prop(ic_panel, "array_index", text="")
            row.operator(PYREC_OT_InspectPanelArrayIndexZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
                self.panel_num
        if array_index_key_type == "str" or array_index_key_type == "int_str":
            row = sub_box.row()
            row.prop(ic_panel, "array_key", text="")
            row.operator(PYREC_OT_InspectPanelArrayKeyZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
                self.panel_num
    # current inspect exec string
    sub_box = box.box()
    sub_box.label(text="Exec: " + ic_panel.dir_inspect_exec_str)
    # attributes of inspect exec value
    if panel_options.display_value_attributes:
        # subtract 1 to account for the '.' list item (which represents 'self' value)
        sub_box.label(text="Inspect Attributes ( %i )" % ( 0 if len(ic_panel.dir_attributes)-1 < 0 else \
                                                           len(ic_panel.dir_attributes)-1 ))
        row = sub_box.row()
        # calculate split factor
        split_denominator = 1
        if panel_options.display_dir_attribute_type:
            split_denominator = split_denominator + 1
        if panel_options.display_dir_attribute_value:
            split_denominator = split_denominator + 1
        split = row.split(factor=1/split_denominator)
        # add attribute list labels to split
        split.label(text="Name")
        if panel_options.display_dir_attribute_type:
            split.label(text="Type")
        if panel_options.display_dir_attribute_value:
            split.label(text="Value")
        # attributes list
        row = sub_box.row()
        list_classname = "PYREC_UL_%s_DirAttributeList%s" % (context_name, ic_panel.name)
        row.template_list(list_classname, "", ic_panel, "dir_attributes", ic_panel, "dir_attributes_index", rows=5)
        col = row.column()
        sub_col = col.column(align=True)
        sub_col.operator(PYREC_OT_InspectPanelAttrZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = self.panel_num
        col.operator(PYREC_OT_InspectRecordAttribute.bl_idname, icon='DOCUMENTS', text="").panel_num = self.panel_num
        col.operator(PYREC_OT_InspectCopyAttribute.bl_idname, icon='COPY_ID', text="").panel_num = self.panel_num
        col.operator(PYREC_OT_InspectPasteAttribute.bl_idname, icon='PASTEDOWN', text="").panel_num = self.panel_num
    # current inspect value, type, doc
    box = layout.box()
    if ic_panel.dir_inspect_exec_str != "":
        box.label(text="Type: " + ic_panel.dir_item_value_typename_str)
        draw_panel_dir_attribute_value(box, ic_panel, panel_options)
        # display documentation / description
        if panel_options.display_attr_doc:
            box.label(text="__doc__:")
            split = box.split(factor=0.95)
            list_classname = "PYREC_UL_%s_DocLineList%s" % (context_name, ic_panel.name)
            split.template_list(list_classname, "", ic_panel, "dir_item_doc_lines", ic_panel,
                              "dir_item_doc_lines_index", rows=2)

def create_context_inspect_panel(context, context_name, inspect_context_collections, begin_exec_str=None):
    # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
    if context_name == "PROPERTIES":
        context_name = "VIEW_3D"
    panel_label = "Py Inspect"
    ic_coll = inspect_context_collections.get(context_name)
    if ic_coll is None:
        count = 0
    else:
        count = ic_coll.inspect_context_panel_next_num
        if count > 0:
            panel_label += "." + str(count).zfill(3)
    # create and register class for panel, to add panel to UI
    if not register_inspect_panel(context_name, count, panel_label):
        return False
    # if context does not have a panel collection yet, then create new panel collection and name it with context_name
    # (Py Inspect panels are grouped by context type/name, because panel classes are registered to context type)
    if ic_coll is None:
        ic_coll = inspect_context_collections.add()
        ic_coll.name = context_name
    # create new panel in collection
    i_panel = ic_coll.inspect_context_panels.add()
    i_panel.name = str(ic_coll.inspect_context_panel_next_num)
    ic_coll.inspect_context_panel_next_num = ic_coll.inspect_context_panel_next_num + 1
    i_panel.panel_label = panel_label
    i_panel.panel_options.panel_option_label = panel_label
    if begin_exec_str is None or begin_exec_str == "":
        return True
    i_panel.inspect_exec_str = begin_exec_str
    # do refresh using modified 'inspect_exec_str'
    ret_val, _ = inspect_exec_refresh(context, ic_coll.inspect_context_panel_next_num - 1)
    if ret_val == "FINISHED":
        return True
    return False

class PYREC_OT_AddInspectPanel(Operator):
    bl_idname = "py_rec.add_py_inspect_panel"
    bl_label = "Add Py Inspect Panel"
    bl_description = "Add Py Inspect panel to active context Tools menu. e.g. If View 3D context, then " \
        "Py Inspect panel is in Tools -> Tool menu"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if not create_context_inspect_panel(context, context.space_data.type,
                                            context.window_manager.py_rec.inspect_context_collections):
            self.report({'ERROR'}, "Unable to add Py Inspect panel to context type '%s'" % context.space_data.type)
            return {'CANCELLED'}
        return {'FINISHED'}

class PYREC_OT_RemoveInspectPanel(Operator):
    bl_idname = "py_rec.remove_inspect_panel"
    bl_label = "Remove Inspect panel?"
    bl_description = "Remove this Inspect panel"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            self.report({'ERROR'}, "Unable to Remove Inspect Panel because panel_num is less than zero")
            return {'CANCELLED'}
        context_name = context.space_data.type
        # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
        if context_name == "PROPERTIES":
            context_name = "VIEW_3D"
        unregister_inspect_panel(context_name, self.panel_num)
        panels = context.window_manager.py_rec.inspect_context_collections[context_name].inspect_context_panels
        # remove panel by finding its index first, then passing index to '.remove()' function
        panels.remove(panels.find(str(self.panel_num)))
        return {'FINISHED'}

    def draw(self, context):
        self.layout.label(text="Click outside window to cancel, or")
        self.layout.label(text="press Esc key to cancel.")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

def inspect_exec_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.window_manager.py_rec.inspect_context_collections)
    if ic_panel is None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because cannot get Inspect Panel"
    panel_options = ic_panel.panel_options
    if panel_options is None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because cannot get Inspect Panel Options"
    # clear index, and dir() attribute listing
    ic_panel.array_index_key_type = "none"
    ic_panel.array_index = 0
    ic_panel.array_index_max = 0
    ic_panel.array_key_set.clear()
    ic_panel.dir_inspect_exec_str = ""
    ic_panel.dir_attributes.clear()
    # clear label strings
    ic_panel.dir_item_value_str = ""
    ic_panel.dir_item_value_typename_str = ""
    ic_panel.dir_item_doc_lines.clear()

    # if Inspect Exec string is empty then quit
    if ic_panel.inspect_exec_str == "":
        return 'CANCELLED', "Unable to refresh Inspect Value, because Inspect Exec string is empty"

    # get total_exec_str, which includes pre-exec lines of code, if any
    post_exec_str = ic_panel.inspect_exec_str
    pre_exec_str = get_pre_exec_str(ic_panel)
    # get 'Inspect Exec' result value, and update label strings based on result
    inspect_value, inspect_error = refresh_inspect_exec_result(pre_exec_str, post_exec_str, True)
    if inspect_error != None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because exception raised during exec, see " \
            "details in log Text named '%s'" % LOG_TEXT_NAME

    # update index props
    if inspect_value != None and hasattr(inspect_value, "__len__") and len(inspect_value) > 0:
        # check for string type keys (for string type index)
        has_index_str = False
        if hasattr(inspect_value, "keys") and callable(inspect_value.keys):
            has_index_str = True
            # create list of strings (key names) for index string enum
            for key_name in inspect_value.keys():
                if not isinstance(key_name, str):
                    continue
                index_str_item = ic_panel.array_key_set.add()
                index_str_item.name = key_name
        # check for integer type index
        has_array_index = False
        try:
            _ = inspect_value[0]    # this line will raise exception if inspect_value cannot be indexed with integer
            # the following lines in the 'try' block will be run only if inspect_value can be indexed with integer
            has_array_index = True
            ic_panel.array_index_max = len(inspect_value)-1
            ic_panel.array_index = 0
        except:
            pass
        # set prop to indicate available index types
        if has_array_index and has_index_str:
            ic_panel.array_index_key_type = "int_str"
        elif has_array_index:
            ic_panel.array_index_key_type = "int"
        elif has_index_str:
            ic_panel.array_index_key_type = "str"

    # dir listing can only be performed if 'inspect_value' is not None, because None does not have attributes
    if inspect_value is None:
        dir_array = []
    else:
        # get current dir() array, and quit if array is empty
        dir_array = get_dir(inspect_value)
    # update dir() listing
    ic_panel.dir_inspect_exec_str = ic_panel.inspect_exec_str
    ic_panel.dir_attributes_index = 0

    # prepend two items in dir_attributes, to include self value and indexed value, so these values are in same format
    # as dir() attributes, because self is attribute of its parent object, and indexed values are dynamic attributes
    dir_item = ic_panel.dir_attributes.add()
    dir_item.name = "."
    dir_item.type_name = ". Self value"
    for attr_name in dir_array:
        # check that inspect_value has attribute, to avoid errors in case 'inspect_value' is indexed
        # (e.g. array, dictionary)
        if not hasattr(inspect_value, attr_name):
            continue
        if panel_options.display_attr_type_only:
            if not (
                (panel_options.display_attr_type_function and callable(getattr(inspect_value, attr_name))) or \
                (panel_options.display_attr_type_builtin and attr_name.startswith("__")) or \
                (panel_options.display_attr_type_bl and attr_name.startswith("bl_")) ):
                continue
        else:
            if not panel_options.display_attr_type_function and callable(getattr(inspect_value, attr_name)):
                continue
            if not panel_options.display_attr_type_builtin and attr_name.startswith("__"):
                continue
            if not panel_options.display_attr_type_bl and attr_name.startswith("bl_"):
                continue
        # create item and set item info
        dir_item = ic_panel.dir_attributes.add()
        dir_item.name = attr_name
        item_value = getattr(inspect_value, attr_name)
        if item_value is None:
            dir_item.type_name = "None"
        else:
            dir_item.type_name = type(item_value).__name__
        dir_item.value_str = str(item_value)

    inspect_value = get_inspect_exec_result()
    ic_panel.dir_item_value_str = str(inspect_value)
    # set 'type name' label
    ic_panel.dir_item_value_typename_str = type(inspect_value).__name__
    # set '__doc__' lines
    string_to_lines_collection(get_relevant_doc(inspect_value), ic_panel.dir_item_doc_lines)
    return 'FINISHED', ""

def inspect_datablock_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.window_manager.py_rec.inspect_context_collections)
    if ic_panel is None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because cannot get Inspect Panel"
    if ic_panel.inspect_datablock_name == "":
        return 'CANCELLED', "Unable to refresh Inspect Value, because Datablock is empty"
    ic_panel.inspect_exec_str = "bpy.data.%s[\"%s\"]" % (ic_panel.inspect_datablock_type,
                                                            ic_panel.inspect_datablock_name)
    return inspect_exec_refresh(context, panel_num)

def inspect_active_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.window_manager.py_rec.inspect_context_collections)
    if ic_panel is None:
        return 'CANCELLED', "Unable to refresh Inspect Active, because cannot get Inspect Panel"
    inspect_str = get_active_thing_inspect_str(context, ic_panel.inspect_active_type)
    if inspect_str == "":
        return 'CANCELLED', "Unable to refresh Inspect Active, because active thing not found in context type '%s'" % \
            context.space_data.type
    ic_panel.inspect_exec_str = inspect_str
    return inspect_exec_refresh(context, panel_num)

def inspect_attr_zoom_in(context, ic_panel, panel_num):
    attr_item = ic_panel.dir_attributes[ic_panel.dir_attributes_index]
    if attr_item is None:
        return
    attr_name = attr_item.name
    if attr_name == "" or attr_name == ".":
        return
    # zoom in to attribute
    ic_panel.inspect_exec_str = ic_panel.dir_inspect_exec_str + "." + attr_name
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelAttrZoomIn(Operator):
    bl_idname = "py_rec.inspect_attr_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected attribute to make it current Inspect object, and refresh Inspect " \
        "Attributes list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Unable to Zoom In to Attribute because Attributes List is empty")
            return {'CANCELLED'}
        inspect_attr_zoom_in(context, ic_panel, self.panel_num)
        return {'FINISHED'}

def inspect_zoom_out(context, ic_panel, panel_num):
    # try remove last attribute of inspect object, and if success, then update exec string and refresh attribute list
    first_part, _ = remove_last_py_attribute(ic_panel.dir_inspect_exec_str)
    if first_part is None:
        return
    ic_panel.inspect_exec_str = first_part
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelAttrZoomOut(Operator):
    bl_idname = "py_rec.inspect_attr_zoom_out"
    bl_label = "Zoom Out"
    bl_description = "Zoom out of current Inspect object to inspect parent object, and refresh Inspect Attributes list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Unable to Zoom Out from Attribute because Attributes List is empty")
            return {'CANCELLED'}
        inspect_zoom_out(context, ic_panel, self.panel_num)
        return {'FINISHED'}

def inspect_array_index_zoom_in(context, ic_panel, panel_num):
    ic_panel.inspect_exec_str = "%s[%i]" % (ic_panel.dir_inspect_exec_str, ic_panel.array_index)
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelArrayIndexZoomIn(Operator):
    bl_idname = "py_rec.inspect_array_index_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected Integer Index by appending Integer Index to current exec string, and " \
        "refresh Inspect Attributes list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None:
            self.report({'ERROR'}, "Unable to Zoom In to Integer Index because Inspect Panel reference is missing")
            return {'CANCELLED'}
        inspect_array_index_zoom_in(context, ic_panel, self.panel_num)
        return {'FINISHED'}

def inspect_array_key_zoom_in(context, ic_panel, panel_num):
    ic_panel.inspect_exec_str = "%s[\"%s\"]" % (ic_panel.dir_inspect_exec_str, ic_panel.array_key)
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelArrayKeyZoomIn(Operator):
    bl_idname = "py_rec.inspect_array_key_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected String Index by appending String Index to current exec string, and " \
        "refresh Inspect Attributes list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None:
            self.report({'ERROR'}, "Unable to Zoom In to String Index because Inspect Panel reference is missing")
            return {'CANCELLED'}
        inspect_array_key_zoom_in(context, ic_panel, self.panel_num)
        return {'FINISHED'}

def restore_inspect_context_panels(inspect_context_collections):
    # unregister existing classes before restoring classes
    # i.e. in case previous .blend file had Inspect Panel classes registered, before next .blend file is loaded
    for attr_name in dir(bpy.types):
        if match_inspect_panel_name(attr_name):
            unregister_class(getattr(bpy.types, attr_name))
    # loop through stored contexts, and panels in each context, to ensure that each panel's class is registered,
    # because panel needs to be registered to be visible
    for icc in inspect_context_collections:
        context_name = icc.name
        # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
        if context_name == "PROPERTIES":
            context_name = "VIEW_3D"
        for icc_panel in icc.inspect_context_panels:
            # check if Py Inspect panel class has been registered
            if hasattr(bpy.types, "PYREC_PT_%s_Inspect%s" % (context_name, icc_panel.name)):
                continue
            # create and register class for panel, to add panel to UI
            register_inspect_panel(context_name, int(icc_panel.name), icc_panel.panel_label)

class PYREC_OT_RestoreInspectContextPanels(Operator):
    bl_idname = "py_rec.restore_inspect_context_panels"
    bl_label = "Restore Context Inspect Panels"
    bl_description = "Restore 'Py Inspect' panels in current .blend file. Use this if context 'Py Inspect' panels " \
        "are missing, e.g. after .blend file is loaded"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        restore_inspect_context_panels(context.window_manager.py_rec.inspect_context_collections)
        return {'FINISHED'}

def get_commented_splitlines(input_str):
    if input_str is None or input_str == "":
        return ""
    out_str = ""
    for l in input_str.splitlines():
        out_str = out_str + "#  " + l + "\n"
    return out_str

def get_attribute_python_str(inspect_str, attr_name, ic_panel, attr_record_options):
    out_first_str = ""
    out_last_str = inspect_str if attr_name == "." else inspect_str + "." + attr_name
    result_value = get_inspect_exec_result()
    if attr_name == ".":
        attr_value = result_value
    elif result_value != None and hasattr(result_value, attr_name):
        attr_value = getattr(result_value, attr_name)
    else:
        attr_value = None
    # append attribute value to output, if needed
    if attr_record_options.include_value:
        if attr_value is None:
            out_last_str += " = None\n"
        elif callable(attr_value):
            out_last_str += " # = %s\n" % str(attr_value)
        else:
            py_val_str = bpy_value_to_string(attr_value)
            if py_val_str is None:
                out_last_str += "  # = %s\n" % str(attr_value)
            else:
                out_last_str += " = %s\n" % py_val_str
    if attr_record_options.comment_type:
        out_first_str += "# Type: " + type(attr_value).__name__ + "\n"
    if attr_record_options.comment_doc:
        doc = get_relevant_doc(attr_value)
        if doc != None and doc != "":
            out_first_str += "# __doc__:\n" + get_commented_splitlines(doc)
    return out_first_str + out_last_str

class PYREC_OT_InspectRecordAttribute(Operator):
    bl_description = "Record single/all attributes to Python code with from/to/output options"
    bl_idname = "py_rec.inspect_record_attribute"
    bl_label = "Record Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        p_r = context.window_manager.py_rec
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type, p_r.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Error: Unable to Record Attribute because Attributes list is empty")
            return {'CANCELLED'}
        return self.inspect_record_attribute(context, ic_panel, p_r.record_options.attribute)

    def draw(self, context):
        attr_record_options = context.window_manager.py_rec.record_options.attribute
        layout = self.layout
        box = layout.box()
        box.prop(attr_record_options, "copy_from")
        row = box.row()
        row.prop(attr_record_options, "copy_to")
        if attr_record_options.copy_to == "text":
            row.prop(attr_record_options, "copy_to_text", text="")
        box.prop(attr_record_options, "comment_type")
        box.prop(attr_record_options, "comment_doc")

    def invoke(self, context, event):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        # do not invoke if zero attributes available to record
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Error: Unable to Record Attribute because Attributes list is empty")
            return {'CANCELLED'}
        # open window to set options before operator execute
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def inspect_record_attribute(self, context, ic_panel, attr_record_options):
        if len(ic_panel.dir_attributes) == 0:
            return
        out_str = ""
        # get single inspect value Python attribute
        if attr_record_options.copy_from == "single_attribute":
            attr_name = ic_panel.dir_attributes[ic_panel.dir_attributes_index].name
            out_str = get_attribute_python_str(ic_panel.dir_inspect_exec_str, attr_name, ic_panel, attr_record_options)
        # get all inspect value Python attributes
        else:
            for attr_item in ic_panel.dir_attributes:
                if attr_item.name == ".":
                    continue
                out_str = out_str + get_attribute_python_str(ic_panel.dir_inspect_exec_str, attr_item.name,
                                                             ic_panel, attr_record_options)
                out_str = out_str + "\n"
        # append final newline to output
        out_str = out_str + "\n"
        # write output to users choice
        if attr_record_options.copy_to == "new_text":
            new_text = bpy.data.texts.new(name=RECORD_ATTRIBUTE_TEXT_NAME)
            new_text.write(out_str)
            self.report({'INFO'}, "Attribute(s) recorded new text named '%s'" % new_text.name)
            return {'FINISHED'}
        elif attr_record_options.copy_to == "text":
            if attr_record_options.copy_to_text != None:
                attr_record_options.copy_to_text.write(out_str)
                self.report({'INFO'}, "Attribute(s) recorded existing text named '%s'" % \
                            attr_record_options.copy_to_text.name)
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Error: Unable to write to existing Text")
                return {'CANCELLED'}
        else: # attr_record_options.copy_to == "clipboard":
            context.window_manager.clipboard = out_str
            self.report({'INFO'}, "Attribute(s) recorded to clipboard")
            return {'FINISHED'}

copy_attribute_ref = {}
class PYREC_OT_InspectCopyAttribute(Operator):
    bl_description = "Create a reference copy from selected attribute"
    bl_idname = "py_rec.inspect_copy_attribute"
    bl_label = "Copy"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Unable to Copy Attribute Reference because Attributes list is empty")
            return {'CANCELLED'}
        return self.copy_attribute_ref(context, ic_panel)

    def copy_attribute_ref(self, context, ic_panel):
        out_str = ic_panel.dir_inspect_exec_str
        attr_name = ic_panel.dir_attributes[ic_panel.dir_attributes_index].name
        if attr_name != ".":
            out_str = out_str + "." + attr_name
        copy_attribute_ref["attribute_ref"] = out_str
        context.window_manager.clipboard = out_str
        return {'FINISHED'}

class PYREC_OT_InspectPasteAttribute(Operator):
    bl_description = "Paste a reference copy to selected attribute. WARNING: may cause Blender to crash! " \
        "Save your work, if needed, before using this function"
    bl_idname = "py_rec.inspect_paste_attribute"
    bl_label = "Paste"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Unable to Paste Attribute Reference because Attributes list is empty")
            return {'CANCELLED'}
        if copy_attribute_ref.get("attribute_ref") is None:
            self.report({'ERROR'}, "Unable to Paste Attribute Reference because Copy reference is empty")
            return {'CANCELLED'}
        return self.paste_attribute_ref(ic_panel)

    def paste_attribute_ref(self, ic_panel):
        set_val_str = ic_panel.dir_inspect_exec_str
        attr_name = ic_panel.dir_attributes[ic_panel.dir_attributes_index].name
        if attr_name != ".":
            set_val_str = set_val_str + "." + attr_name
        get_val_str = copy_attribute_ref["attribute_ref"]
        try:
            exec(set_val_str + " = " + get_val_str)
        except:
            log_text_append("Exception raised during Paste Attribute exec of:\n  %s\n%s" %
                            (set_val_str + " = " + get_val_str, traceback.format_exc()) )
            self.report({'ERROR'}, "Unable to Paste Attribute, exception raised during exec() with paste " \
                "reference string. See Text named '%s' for details" % LOG_TEXT_NAME)
            return {'CANCELLED'}
        return {'FINISHED'}

class PYREC_OT_InspectChoosePy(Operator):
    bl_description = "Open window to choose Python object to inspect"
    bl_idname = "py_rec.inspect_choose_py"
    bl_label = "Inspect"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None:
            return {'CANCELLED'}
        if ic_panel.inspect_py_type == "active":
            ret_val, report_val = inspect_active_refresh(context, self.panel_num)
            if ret_val == 'FINISHED':
                return {'FINISHED'}
            self.report({'ERROR'}, report_val)
            return { ret_val }
        elif ic_panel.inspect_py_type == "datablock":
            ret_val, report_val = inspect_datablock_refresh(context, self.panel_num)
            if ret_val == 'FINISHED':
                return {'FINISHED'}
            self.report({'ERROR'}, report_val)
            return { ret_val }
        else:   # custom
            ret_val, report_val = inspect_exec_refresh(context, self.panel_num)
            if ret_val == 'FINISHED':
                return {'FINISHED'}
            self.report({'ERROR'}, report_val)
            return { ret_val }

    def draw(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None:
            return
        layout = self.layout

        box = layout.box()
        box.label(text="Pre-Inspect Exec")
        box.prop(ic_panel, "pre_inspect_type", text="")
        if ic_panel.pre_inspect_type == "single_line":
            box.prop(ic_panel, "pre_inspect_single_line", text="")
        elif ic_panel.pre_inspect_type == "textblock":
            box.prop(ic_panel, "pre_inspect_text", text="")

        box = layout.box()
        box.label(text="Inspect Exec")
        box.prop(ic_panel, "inspect_py_type", text="")
        if ic_panel.inspect_py_type == "active":
            box.prop(ic_panel, "inspect_active_type", text="")
        elif ic_panel.inspect_py_type == "custom":
            box.prop(ic_panel, "inspect_exec_str", text="")
        elif ic_panel.inspect_py_type == "datablock":
            row = box.row(align=True)
            row.prop(ic_panel, "inspect_datablock_type", text="")
            row.prop_search(ic_panel, "inspect_datablock_name", bpy.data, ic_panel.inspect_datablock_type, text="")

    def invoke(self, context, event):
        # open window to set options before operator execute
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

def draw_inspect_context_menu(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(PYREC_OT_AddInspectPanel.bl_idname)

def append_context_menu_all(draw_func, menu_list):
    for type_name in dir(bpy.types):
        # e.g. 'VIEW3D_MT_object_context_menu', 'NODE_MT_context_menu'
        if not re.match("^[A-Za-z0-9_]+_MT[A-Za-z0-9_]*_context_menu$", type_name):
            continue
        attr_value = getattr(bpy.types, type_name)
        if attr_value is None:
            continue
        try:
            attr_value.append(draw_func)
            menu_list.append(attr_value)
        except:
            pass

def remove_context_menu_all(draw_func, menu_list):
    for d in menu_list:
        d.remove(draw_func)
    menu_list.clear()

inspect_context_menu_removes = []
def append_inspect_context_menu_all():
    append_context_menu_all(draw_inspect_context_menu, inspect_context_menu_removes)

def remove_inspect_context_menu_all():
    remove_context_menu_all(draw_inspect_context_menu, inspect_context_menu_removes)

class PYREC_OT_PyInspectActiveObject(Operator):
    bl_description = "Inspect active Object with new Py Inspect panel (see context Tools menu)"
    bl_idname = "py_rec.py_inspect_active_object"
    bl_label = "Object"
    bl_options = {'REGISTER', 'UNDO'}

    inspect_type: StringProperty(default="OBJECT", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        active_types = get_inspect_active_type_items(None, context)
        return len(active_types) > 0

    def execute(self, context):
        start_string = get_active_thing_inspect_str(context, self.inspect_type)
        if not create_context_inspect_panel(context, context.space_data.type,
                                            context.window_manager.py_rec.inspect_context_collections, start_string):
            self.report({'ERROR'}, "Inspect Active Object: Unable to inspect Object")
            return {'CANCELLED'}
        return {'FINISHED'}

class PYREC_MT_InspectActive(bpy.types.Menu):
    bl_label = "Py Inspect Active"
    bl_idname = "PYREC_MT_InspectActive"

    def draw(self, context):
        layout = self.layout
        active_types = get_inspect_active_type_items(None, context)
        for type_name, nice_name, _ in active_types:
            layout.operator(PYREC_OT_PyInspectActiveObject.bl_idname, text=nice_name).inspect_type = type_name

def draw_inspect_active_context_menu(self, context):
    layout = self.layout
    layout.menu(PYREC_MT_InspectActive.bl_idname)

inspect_active_context_menu_removes = []
def append_inspect_active_context_menu_all():
    append_context_menu_all(draw_inspect_active_context_menu, inspect_active_context_menu_removes)

def remove_inspect_active_context_menu_all():
    remove_context_menu_all(draw_inspect_active_context_menu, inspect_active_context_menu_removes)
