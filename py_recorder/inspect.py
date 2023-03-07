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

import mathutils
import traceback

import bpy
from bpy.types import (Operator, PropertyGroup, UIList)
from bpy.props import (BoolProperty, IntProperty, StringProperty)

from .inspect_options import PYREC_OT_InspectOptions
from .inspect_func import (get_dir, get_inspect_context_panel, remove_last_py_attribute)
from .inspect_exec import (get_inspect_exec_result, register_inspect_panel_exec, unregister_inspect_panel_exec)
from .bpy_value_string import bpy_value_to_string
from .log_text import (LOG_TEXT_NAME, log_text_append)

RECORD_ATTRIBUTE_TEXT_NAME = "pyrec_attribute.py"

def draw_panel_dir_attribute_value(layout, panel_props, panel_options):
    # display value selector, if enabled and value is available
    result_value = None
    result_error = None
    attr_name = panel_props.dir_attributes[panel_props.dir_attributes_index].name
    attr_val = None
    if panel_options.display_value_selector:
        if attr_name == ".":
            first_part, last_part = remove_last_py_attribute(panel_props.dir_inspect_exec_str)
            if first_part != None and last_part != None:
                result_value, result_error = get_inspect_exec_result(first_part, False)
                # if last part is indexed then force value to be displayed as label
                if (last_part[0]+last_part[-1]) == "[]":
                    result_value = None
                else:
                    attr_name = last_part
        else:
            result_value, result_error = get_inspect_exec_result(panel_props.dir_inspect_exec_str, False)
    # try to use a real-time entry field (selector), and display label string if real-time entry field fails
    if result_error is None and result_value != None and attr_name != "bl_rna" and not attr_name.startswith("__") and \
        hasattr(result_value, attr_name):
        attr_val = getattr(result_value, attr_name)
        # do not display if attribute value is None or if it is a zero-length list/tuple
        if attr_val != None and not ( isinstance(attr_val, (list, tuple)) and len(attr_val) == 0) and \
            not callable(attr_val):
            try:
                layout.prop(result_value, attr_name, text="Value")
                return
            except:
                pass
    layout.label(text="Value: " + panel_props.dir_item_value_str)

def draw_inspect_panel(self, context):
    ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_options = ic_panel.panel_options
    if panel_options is None:
        return

    layout = self.layout

    box = layout.box()
    row = box.row()
    row.operator(PYREC_OT_RemoveInspectPanel.bl_idname, icon='REMOVE', text="").panel_num = self.panel_num
    row.separator()
    row.operator(PYREC_OT_InspectOptions.bl_idname, icon='OPTIONS', text="").panel_num = self.panel_num

    if panel_options.display_datablock_refresh:
        box = layout.box()
        row = box.row(align=True)
        row.prop(ic_panel, "inspect_data_type", text="")
        row.prop_search(ic_panel, "inspect_datablock", bpy.data, ic_panel.inspect_data_type, text="")
        layout.operator(PYREC_OT_InspectDatablockRefresh.bl_idname).panel_num = self.panel_num
    if panel_options.display_exec_refresh:
        box = layout.box()
        box.prop(ic_panel, "inspect_exec_str", text="")
        box.operator(PYREC_OT_InspectExecRefresh.bl_idname).panel_num = self.panel_num
    if panel_options.display_value_attributes:
        box = layout.box()

        index_type = ic_panel.index_type
        if index_type == "int" or index_type == "str" or index_type == "int_str":
            sub_box = box.box()
            sub_box.label(text="Index")
            sub_box.label(text="Item Count: "+str(max(len(ic_panel.index_str_coll), ic_panel.index_max_int+1)))
        if index_type == "int" or index_type == "int_str":
            row = sub_box.row()
            row.prop(ic_panel, "index_int", text="")
            row.operator(PYREC_OT_InspectPanelIndexIntZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
                self.panel_num
        if index_type == "str" or index_type == "int_str":
            row = sub_box.row()
            row.prop(ic_panel, "index_str_enum", text="")
            row.operator(PYREC_OT_InspectPanelIndexStrZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
                self.panel_num

        sub_box = box.box()
        sub_box.label(text="Inspect Attributes")
        row = sub_box.row()
        split_denominator = 1
        if panel_options.display_dir_attribute_type:
            split_denominator = split_denominator + 1
        if panel_options.display_dir_attribute_value:
            split_denominator = split_denominator + 1
        split = row.split(factor=1/split_denominator)
        split.label(text="Name")
        if panel_options.display_dir_attribute_type:
            split.label(text="Type")
        if panel_options.display_dir_attribute_value:
            split.label(text="Value")

        row = sub_box.row()
        row.template_list("PYREC_UL_DirAttributeList", "", ic_panel, "dir_attributes", ic_panel,
                          "dir_attributes_index", rows=5)
        col = row.column()
        sub_col = col.column(align=True)
        sub_col.operator(PYREC_OT_InspectPanelAttrZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = self.panel_num
        sub_col.operator(PYREC_OT_InspectPanelAttrZoomOut.bl_idname, icon='ZOOM_OUT', text="").panel_num = \
            self.panel_num
        col.operator(PYREC_OT_InspectRecordAttribute.bl_idname, icon='DOCUMENTS', text="").panel_num = self.panel_num
        col.operator(PYREC_OT_InspectCopyAttribute.bl_idname, icon='COPY_ID', text="").panel_num = self.panel_num
        col.operator(PYREC_OT_InspectPasteAttribute.bl_idname, icon='PASTEDOWN', text="").panel_num = self.panel_num

    box = layout.box()
    if ic_panel.dir_inspect_exec_str != "":
        box.label(text="Exec: " + ic_panel.dir_item_exec_str)
        box.label(text="Type: " + ic_panel.dir_item_value_typename_str)
        draw_panel_dir_attribute_value(box, ic_panel, panel_options)
        # display documentation / description
        if panel_options.display_attr_doc:
            box.label(text="__doc__:")
            split = box.split(factor=0.95)
            split.template_list("PYREC_UL_StringList", "", ic_panel, "dir_item_doc_lines", ic_panel,
                              "dir_item_doc_lines_index", rows=2)

def get_dir_attribute_exec_str(base, attr_name):
    # if exec str is '.', which means 'self' is selected, then do not append attribute name
    if attr_name == ".":
        return base
    return base + "." + attr_name

# split 'input_str' into separate lines, and add each line to 'lines_coll'
def string_to_lines_collection(input_str, lines_coll):
    for str_line in input_str.splitlines():
        new_item = lines_coll.add()
        new_item.name = str_line

def has_relevant_doc(value):
    return value != None and hasattr(value, "__doc__") and value.__doc__ != None and \
        not isinstance(value, (bool, dict, float, int, list, set, str, tuple, mathutils.Color, mathutils.Euler, \
                       mathutils.Matrix, mathutils.Quaternion, mathutils.Vector) )

def update_dir_attributes(self, value):
    # self, e.g.  PYREC_PG_InspectPanelProps
    # value, e.g. bpy.types.Context
    panel_props = self
    panel_props.dir_item_exec_str = ""
    panel_props.dir_item_value_str = ""
    panel_props.dir_item_value_typename_str = ""
    panel_props.dir_item_doc_lines.clear()
    # quit if dir() listing is empty
    if len(panel_props.dir_attributes) < 1:
        return
    # set dir listing attribute info label strings from attribute value information
    panel_props.dir_item_exec_str = get_dir_attribute_exec_str(panel_props.dir_inspect_exec_str,
        panel_props.dir_attributes[panel_props.dir_attributes_index].name)
    # exec the string to get the attribute's value
    result_value, result_error = get_inspect_exec_result(panel_props.dir_item_exec_str, False)
    if result_error is None:
        panel_props.dir_item_value_str = str(result_value)
    # remaining attribute info is blank if attribute value is None
    if result_value is None:
        return
    # set 'type name' label
    panel_props.dir_item_value_typename_str = type(result_value).__name__
    # set '__doc__' label, if available as string type
    if has_relevant_doc(result_value):
        doc_value = getattr(result_value, "__doc__")
        if isinstance(doc_value, str):
            string_to_lines_collection(doc_value, panel_props.dir_item_doc_lines)

def create_context_inspect_panel(context_name, inspect_context_collections, panel_label, auto_number):
    ic_coll = inspect_context_collections.get(context_name)
    if ic_coll is None:
        count = 0
    else:
        count = ic_coll.inspect_context_panel_next_num
    # exec string to add panel class, and register the new class
    if panel_label == "":
        panel_label = "Py Inspect"
    if auto_number:
        if count > 0:
            panel_label = panel_label + "." + str(count).zfill(3)
    # create and register class for panel, to add panel to UI
    if not register_inspect_panel_exec(context_name, count, panel_label):
        return False
    # if context does not have a panel collection yet, then create new panel collection and name it with context_name
    # (Py Inspect panels are grouped by context type/name, because panel classes are registered to context type)
    if ic_coll is None:
        ic_coll = inspect_context_collections.add()
        ic_coll.name = context_name
    # create new panel in collection
    i_panel = ic_coll.inspect_context_panels.add()
    i_panel.name = str(ic_coll.inspect_context_panel_next_num)
    i_panel.panel_label = panel_label
    ic_coll.inspect_context_panel_next_num = ic_coll.inspect_context_panel_next_num + 1
    return True

class PYREC_OT_AddInspectPanel(Operator):
    bl_idname = "py_rec.add_inspect_panel"
    bl_label = "Add Inspect Panel"
    bl_description = "Add Inspect panel to active context Tools menu. If View 3D context, Inspect panel is added " \
        "in Tools -> Tool menu"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})
    panel_name_default: StringProperty(name="Name", description="New Py Inspect panel name", default="Py Inspect")
    panel_name_auto_number: BoolProperty(name="Auto-number", description="Append number to Inspect panel name. " +
        "Number is incremented after new panel is created", default=True)

    def execute(self, context):
        if not create_context_inspect_panel(context.space_data.type, context.scene.py_rec.inspect_context_collections,
                                            self.panel_name_default, self.panel_name_auto_number):
            self.report({'ERROR'}, "Add Inspect Panel: Unable to add panel to context type '" +
                        context.space_data.type + "'")
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
        unregister_inspect_panel_exec(context_name, self.panel_num)
        panels = context.scene.py_rec.inspect_context_collections[context_name].inspect_context_panels
        # remove panel by finding its index first, then passing index to '.remove()' function
        panels.remove(panels.find(str(self.panel_num)))
        return {'FINISHED'}

    def draw(self, context):
        self.layout.label(text="Click outside window to cancel, or")
        self.layout.label(text="press Esc key to cancel.")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

def inspect_datablock_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    if ic_panel.inspect_datablock == "":
        return
    ic_panel.inspect_exec_str = "bpy.data.%s[\"%s\"]" % (ic_panel.inspect_data_type,
                                                            ic_panel.inspect_datablock)
    return inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectDatablockRefresh(Operator):
    bl_idname = "py_rec.inspect_datablock_refresh"
    bl_label = "Inspect Datablock"
    bl_description = "Refresh Inspect Attributes from Inspect Datablock"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            self.report({'ERROR'}, "Unable to refresh Inspect Datablock because panel_num is less than zero")
            return {'CANCELLED'}
        ret_val, report_val = inspect_datablock_refresh(context, self.panel_num)
        if ret_val == 'FINISHED':
            return {'FINISHED'}
        self.report({'ERROR'}, report_val)
        return { ret_val }

def inspect_exec_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because cannot get Inspect Panel"
    panel_options = ic_panel.panel_options
    if panel_options is None:
        return 'CANCELLED', "Unable to refresh Inspect Value, because cannot get Inspect Panel Options"
    # clear index, and dir() attribute listing
    ic_panel.index_type = "none"
    ic_panel.index_int = 0
    ic_panel.index_max_int = 0
    ic_panel.index_str_coll.clear()
    ic_panel.dir_inspect_exec_str = ""
    ic_panel.dir_attributes.clear()
    # clear label strings
    ic_panel.dir_item_exec_str = ""
    ic_panel.dir_item_value_str = ""
    ic_panel.dir_item_value_typename_str = ""
    ic_panel.dir_item_doc_lines.clear()

    # if Inspect Exec string is empty then quit
    if ic_panel.inspect_exec_str == "":
        return 'CANCELLED', "Unable to refresh Inspect Value, because Inspect Exec string is empty"
    # get 'Inspect Exec' result value, and update label strings based on result
    inspect_value, inspect_error = get_inspect_exec_result(ic_panel.inspect_exec_str, True)
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
                index_str_item = ic_panel.index_str_coll.add()
                index_str_item.name = key_name
        # check for integer type index
        has_index_int = False
        try:
            x = inspect_value[0]    # this line will raise exception if inspect_value cannot be indexed with integer
            # the following lines in the 'try' block will be run only if inspect_value can be indexed with integer
            has_index_int = True
            ic_panel.index_max_int = len(inspect_value)-1
            ic_panel.index_int = 0
        except:
            pass
        # set prop to indicate available index types
        if has_index_int and has_index_str:
            ic_panel.index_type = "int_str"
        elif has_index_int:
            ic_panel.index_type = "int"
        elif has_index_str:
            ic_panel.index_type = "str"

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

    # set dir listing attribute info label strings from attribute value information
    ic_panel.dir_item_exec_str = get_dir_attribute_exec_str(ic_panel.dir_inspect_exec_str,
                                                            ic_panel.dir_attributes[0].name)
    inspect_value, inspect_error = get_inspect_exec_result(ic_panel.dir_item_exec_str, False)
    if inspect_error != None:
        return 'FINISHED', ""
    ic_panel.dir_item_value_str = str(inspect_value)
    # remaining attribute info is blank if attribute value is None
    if inspect_value is None:
        return 'FINISHED', ""
    # set 'type name' label
    ic_panel.dir_item_value_typename_str = type(inspect_value).__name__
    # set '__doc__' lines, if available as string type
    if has_relevant_doc(inspect_value):
        doc_value = getattr(inspect_value, "__doc__")
        if isinstance(doc_value, str):
            string_to_lines_collection(doc_value, ic_panel.dir_item_doc_lines)
    return 'FINISHED', ""

class PYREC_OT_InspectExecRefresh(Operator):
    bl_idname = "py_rec.inspect_exec_refresh"
    bl_label = "Inspect Exec"
    bl_description = "Refresh Inspect Attributes from Inspect Exec string"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            self.report({'ERROR'}, "Unable to refresh Inspect Exec because panel_num is less than zero")
            return {'CANCELLED'}
        ret_val, report_val = inspect_exec_refresh(context, self.panel_num)
        if ret_val == 'FINISHED':
            return {'FINISHED'}
        self.report({'ERROR'}, report_val)
        return { ret_val }

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
                                             context.scene.py_rec.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) < 1:
            self.report({'ERROR'}, "Unable to Zoom In to Attribute because Inspect Panel reference is missing")
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
                                             context.scene.py_rec.inspect_context_collections)
        if ic_panel is None:
            self.report({'ERROR'}, "Unable to Zoom Out from Attribute because Inspect Panel reference is missing")
            return {'CANCELLED'}
        inspect_zoom_out(context, self.panel_num)
        return {'FINISHED'}

class PYREC_PG_DirAttributeItem(PropertyGroup):
    type_name: StringProperty()
    value_str: StringProperty()

class PYREC_UL_DirAttributeList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # self,  e.g. PYREC_UL_DirAttributeList
        # data, PYREC_PG_InspectPanelProps
        # item, e.g. PYREC_PG_DirAttributeItem
        # active_data, e.g. PYREC_PG_InspectPanelProps
        panel_options = data.panel_options
        split_denominator = 1
        if panel_options.display_dir_attribute_type:
            split_denominator = split_denominator + 1
        if panel_options.display_dir_attribute_value:
            split_denominator = split_denominator + 1
        split = layout.split(factor=1/split_denominator)
        split.label(text=item.name)
        if panel_options.display_dir_attribute_type:
            split.label(text=item.type_name)
        if panel_options.display_dir_attribute_value:
            row = split.row()
            # display value selector, if possible
            if panel_options.display_value_selector and data.dir_inspect_exec_str != "" and item.name != "." and \
                not item.name.startswith("__") and item.name != "bl_rna":
                result_value, result_error = get_inspect_exec_result(data.dir_inspect_exec_str, False)
                if result_error is None and result_value != None and hasattr(result_value, item.name):
                    attr_val = getattr(result_value, item.name)
                    # do not display if attribute value is None or if it is a zero-length list/tuple
                    if attr_val != None and not ( isinstance(attr_val, (list, tuple)) and len(attr_val) == 0) and \
                        not callable(attr_val):
                        try:
                            row.prop(result_value, item.name, text="")
                            return
                        except:
                            pass
            # show value str if value selector not available
            row.label(text=item.value_str)

class PYREC_UL_StringList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.name)

def inspect_index_int_zoom_in(context, ic_panel, panel_num):
    ic_panel.inspect_exec_str = "%s[%i]" % (ic_panel.dir_inspect_exec_str, ic_panel.index_int)
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelIndexIntZoomIn(Operator):
    bl_idname = "py_rec.inspect_index_int_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected Integer Index by appending Integer Index to current exec string, and " \
        "refresh Inspect Attributes list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.scene.py_rec.inspect_context_collections)
        if ic_panel is None:
            self.report({'ERROR'}, "Unable to Zoom In to Integer Index because Inspect Panel reference is missing")
            return {'CANCELLED'}
        inspect_index_int_zoom_in(context, self.panel_num)
        return {'FINISHED'}

def inspect_index_str_zoom_in(context, ic_panel, panel_num):
    ic_panel.inspect_exec_str = "%s[\"%s\"]" % (ic_panel.dir_inspect_exec_str, ic_panel.index_str_enum)
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelIndexStrZoomIn(Operator):
    bl_idname = "py_rec.inspect_index_str_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected String Index by appending String Index to current exec string, and " \
        "refresh Inspect Attributes list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.scene.py_rec.inspect_context_collections)
        if ic_panel is None:
            self.report({'ERROR'}, "Unable to Zoom In to String Index because Inspect Panel reference is missing")
            return {'CANCELLED'}
        inspect_index_str_zoom_in(context, ic_panel, self.panel_num)
        return {'FINISHED'}

def restore_inspect_context_panels(inspect_context_collections):
    for icc in inspect_context_collections:
        context_name = icc.name
        for icc_panel in icc.inspect_context_panels:
            # check if Py Inspect panel class has been registered
            if hasattr(bpy.types, "PYREC_PT_%s_Inspect%s" % (context_name, icc_panel.name)):
                continue
            # create and register class for panel, to add panel to UI
            register_inspect_panel_exec(context_name, int(icc_panel.name), icc_panel.panel_label)

class PYREC_OT_RestoreInspectContextPanels(Operator):
    bl_idname = "py_rec.restore_inspect_context_panels"
    bl_label = "Restore Context Inspect Panels"
    bl_description = "Restore 'Py Inspect' panels in current .blend file. Use this if context 'Py Inspect' panels " \
        "are missing, e.g. after .blend file is loaded"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        restore_inspect_context_panels(context.scene.py_rec.inspect_context_collections)
        return {'FINISHED'}

def get_commented_splitlines(input_str):
    if input_str is None or input_str == "":
        return ""
    out_str = ""
    for l in input_str.splitlines():
        out_str = out_str + "#  " + l + "\n"
    return out_str

def get_attribute_python_str(inspect_str, attr_name, attr_record_options):
    if attr_name != ".":
        inspect_str = inspect_str + "." + attr_name
    out_first_str = ""
    out_last_str = inspect_str
    # append attribute value to output, if needed
    if attr_record_options.include_value:
        result_value, result_error = get_inspect_exec_result(inspect_str, False)
        if result_value is None:
            out_last_str = out_last_str + " = None\n"
        else:
            py_val_str = bpy_value_to_string(result_value)
            if py_val_str != None:
                out_last_str = out_last_str + " = " + py_val_str + "\n"
                if attr_record_options.comment_type:
                    out_first_str = out_first_str + "# Type: " + type(result_value).__name__ + "\n"
                if attr_record_options.comment_doc and has_relevant_doc(result_value):
                    out_first_str = out_first_str + "# __doc__:\n" + \
                        get_commented_splitlines(str(result_value.__doc__))
            else:
                out_last_str = out_last_str + "  # = " + str(result_value) + "\n"
    return out_first_str + out_last_str

class PYREC_OT_InspectRecordAttribute(Operator):
    bl_description = "Record single/all attributes to Python code with from/to/output options"
    bl_idname = "py_rec.inspect_record_attribute"
    bl_label = "Record Attribute"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        p_r = context.scene.py_rec
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type, p_r.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Error: Unable to Record Attribute because Attributes list is empty")
            return {'CANCELLED'}
        return self.inspect_record_attribute(context, ic_panel, p_r.record_options.attribute)

    def draw(self, context):
        attr_record_options = context.scene.py_rec.record_options.attribute
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
                                             context.scene.py_rec.inspect_context_collections)
        # do not invoke if zero attributes available to record
        if len(ic_panel.dir_attributes) == 0:
            return {'FINISHED'}
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
            out_str = get_attribute_python_str(ic_panel.dir_inspect_exec_str, attr_name, attr_record_options)
        # get all inspect value Python attributes
        else:
            for attr_item in ic_panel.dir_attributes:
                if attr_item.name == ".":
                    continue
                out_str = out_str + get_attribute_python_str(ic_panel.dir_inspect_exec_str, attr_item.name,
                                                             attr_record_options)
                out_str = out_str + "\n"
        # append final newline to output
        out_str = out_str + "\n"
        # write output to users choice
        if attr_record_options.copy_to == "clipboard":
            context.window_manager.clipboard = out_str
        elif attr_record_options.copy_to == "new_text":
            new_text = bpy.data.texts.new(name=RECORD_ATTRIBUTE_TEXT_NAME)
            new_text.write(out_str)
        elif attr_record_options.copy_to == "text":
            if attr_record_options.copy_to_text != None:
                attr_record_options.copy_to_text.write(out_str)
            else:
                self.report({'ERROR'}, "Error: Unable to write to existing Text")
                return {'CANCELLED'}
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
                                             context.scene.py_rec.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Unable to Copy Attribute Reference because Attributes list is empty")
            return {'CANCELLED'}
        return self.copy_attribute_ref(ic_panel)

    def copy_attribute_ref(self, ic_panel):
        out_str = ic_panel.dir_inspect_exec_str
        attr_name = ic_panel.dir_attributes[ic_panel.dir_attributes_index].name
        if attr_name != ".":
            out_str = out_str + "." + attr_name
        copy_attribute_ref["attribute_ref"] = out_str
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
                                             context.scene.py_rec.inspect_context_collections)
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
