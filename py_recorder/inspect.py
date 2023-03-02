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
from bpy.types import (Operator, Panel, PropertyGroup, UIList)
from bpy.props import (BoolProperty, IntProperty, StringProperty)
from bpy.utils import (register_class, unregister_class)

from .inspect_options import PYREC_OT_InspectOptions
from .inspect_func import (get_dir, get_inspect_context_collection, get_inspect_context_panel)
from .lex_py_attributes import lex_py_attributes

inspect_panel_classes = {}
PANEL_REGISTER_EXEC_STR = "class PYREC_OBJECT_PT_Inspect%i(Panel):\n" \
      "    bl_space_type = '%s'\n" \
      "    bl_region_type = 'UI'\n" \
      "    bl_category = \"Tool\"\n" \
      "    bl_label = \"%s\"\n" \
      "    panel_num = %i\n" \
      "    def draw(self, context):\n" \
      "        inspect_panel_draw(self, context)\n" \
      "register_class(PYREC_OBJECT_PT_Inspect%i)\n" \
      "global inspect_panel_classes\n" \
      "inspect_panel_classes['PYREC_OBJECT_PT_Inspect%i'] = PYREC_OBJECT_PT_Inspect%i\n"
PANEL_UNREGISTER_EXEC_STR = "global inspect_panel_classes\n" \
                            "c = inspect_panel_classes[\"PYREC_OBJECT_PT_Inspect%i\"]\n" \
                            "del inspect_panel_classes[\"PYREC_OBJECT_PT_Inspect%i\"]\n" \
                            "unregister_class(c)\n"
inspect_exec_result = {}

def display_panel_dir_attribute_value(layout, panel_props, panel_options):
    # display value selector, if enabled and value is available
    result_value = None
    result_error = None
    attr_name = panel_props.dir_attributes[panel_props.dir_attributes_index].name
    attr_val = None
    if panel_options.display_value_selector:
        if attr_name == ".":
            first_part, last_part = remove_last_py_attribute(panel_props.dir_inspect_exec_str)
            if first_part != None and last_part != None:
                result_value, result_error = get_inspect_exec_result(first_part)
                # if last part is indexed then force value to be displayed as label
                if (last_part[0]+last_part[-1]) == "[]":
                    result_value = None
                else:
                    attr_name = last_part
        else:
            result_value, result_error = get_inspect_exec_result(panel_props.dir_inspect_exec_str)
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

def inspect_panel_draw(self, context):
    context_name = context.space_data.type
    ic_panel = get_inspect_context_panel(self.panel_num, context_name,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_props = ic_panel.panel_props
    panel_options = panel_props.panel_options
    if panel_props is None or panel_options is None:
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
        row.prop(panel_props, "inspect_data_type", text="")
        row.prop_search(panel_props, "inspect_datablock", bpy.data, panel_props.inspect_data_type, text="")
        layout.operator(PYREC_OT_InspectDatablockRefresh.bl_idname).panel_num = self.panel_num
    if panel_options.display_exec_refresh:
        box = layout.box()
        box.prop(panel_props, "inspect_exec_str", text="")
        box.operator(PYREC_OT_InspectExecRefresh.bl_idname).panel_num = self.panel_num
    if panel_options.display_value_attributes:
        box = layout.box()

        index_type = panel_props.index_type
        if index_type == "int" or index_type == "str" or index_type == "int_str":
            sub_box = box.box()
            sub_box.label(text="Index")
            sub_box.label(text="Item Count: "+str(max(len(panel_props.index_str_coll), panel_props.index_max_int+1)))
        if index_type == "int" or index_type == "int_str":
            row = sub_box.row()
            row.prop(panel_props, "index_int", text="")
            row.operator(PYREC_OT_InspectPanelIndexIntZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
                self.panel_num
        if index_type == "str" or index_type == "int_str":
            row = sub_box.row()
            row.prop(panel_props, "index_str_enum", text="")
            row.operator(PYREC_OT_InspectPanelIndexStrZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
                self.panel_num

        sub_box = box.box()
        sub_box.label(text="Attributes")
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
        row.template_list("PYREC_UL_DirAttributeList", "", panel_props, "dir_attributes", panel_props,
                          "dir_attributes_index", rows=5)
        col = row.column(align=True)
        col.operator(PYREC_OT_InspectPanelAttrZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = self.panel_num
        col.operator(PYREC_OT_InspectPanelAttrZoomOut.bl_idname, icon='ZOOM_OUT', text="").panel_num = self.panel_num

    box = layout.box()
    if panel_props.dir_inspect_exec_str != "":
        box.label(text="Exec: " + panel_props.dir_item_exec_str)
        box.label(text="Type: " + panel_props.dir_item_value_typename_str)
        display_panel_dir_attribute_value(box, panel_props, panel_options)
        # display documentation / description
        if panel_options.display_attr_doc:
            box.label(text="__doc__:")
            split = box.split(factor=0.95)
            split.template_list("PYREC_UL_StringList", "", panel_props, "dir_item_doc_lines", panel_props,
                              "dir_item_doc_lines_index", rows=2)
        if panel_options.display_attr_bl_description:
            box.label(text="bl_description:")
            split = box.split(factor=0.95)
            split.template_list("PYREC_UL_StringList", "", panel_props, "dir_item_bl_description_lines", panel_props,
                              "dir_item_bl_description_lines_index", rows=2)

def register_inspect_panel_exec(context, index, panel_label):
    exec_str = PANEL_REGISTER_EXEC_STR % (index, context.space_data.type, panel_label, index, index, index,
                                          index)
    exec(exec_str)

def unregister_inspect_panel_exec(index):
    if inspect_panel_classes.get("PYREC_OBJECT_PT_Inspect%i" % index) is None:
        return
    # remove from list of classes before unregistering class, to prevent reference errors
    exec_str = PANEL_UNREGISTER_EXEC_STR % (index, index)
    exec(exec_str)

# returns 2-tuple of (output value, error string)
# error string is None if no error occurred during exec
def get_inspect_exec_result(inspect_exec_str):
    if inspect_exec_str == "":
        return None, "empty inspect exec string"
    ie_str = "global inspect_exec_result\ninspect_exec_result['result'] = %s" % inspect_exec_str
    try:
        exec(ie_str)
    except:
        return None, "exception raised during exec"
    r = inspect_exec_result["result"]
    del inspect_exec_result["result"]
    return r, None

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

def update_dir_attributes(self, value):
    # self, e.g.  PYREC_PG_InspectPanelProps
    # value, e.g. bpy.types.Context
    panel_props = self
    panel_props.dir_item_exec_str = ""
    panel_props.dir_item_value_str = ""
    panel_props.dir_item_value_typename_str = ""
    panel_props.dir_item_doc_lines.clear()
    panel_props.dir_item_bl_description_lines.clear()
    # quit if dir() listing is empty
    if len(panel_props.dir_attributes) < 1:
        return
    # set dir listing attribute info label strings from attribute value information
    panel_props.dir_item_exec_str = get_dir_attribute_exec_str(panel_props.dir_inspect_exec_str,
        panel_props.dir_attributes[panel_props.dir_attributes_index].name)
    # exec the string to get the attribute's value
    result_value, result_error = get_inspect_exec_result(panel_props.dir_item_exec_str)
    if result_error is None:
        panel_props.dir_item_value_str = str(result_value)
    # remaining attribute info is blank if attribute value is None
    if result_value is None:
        return
    # set 'type name' label
    panel_props.dir_item_value_typename_str = type(result_value).__name__
    # set '__doc__' label, if available as string type
    if hasattr(result_value, "__doc__"):
        doc_value = getattr(result_value, "__doc__")
        if isinstance(doc_value, str):
            string_to_lines_collection(doc_value, panel_props.dir_item_doc_lines)
    # set 'bl_description' label, if available as string type
    if hasattr(result_value, "bl_description"):
        bl_desc = getattr(result_value, "bl_description")
        if isinstance(bl_desc, str):
            string_to_lines_collection(bl_desc, panel_props.dir_item_bl_description_lines)

def add_inspect_context_panel_prop_grp(context_name, inspect_context_collections):
    # add PropertyGroup for inspect context panel
    ic_coll = get_inspect_context_collection(context_name, inspect_context_collections)
    if ic_coll is None:
        ic_coll = inspect_context_collections.add()
        ic_coll.name = context_name
    # create new panel
    i_panel = ic_coll.inspect_context_panels.add()
    i_panel.name = str(ic_coll.inspect_context_panel_next_num)
    ic_coll.inspect_context_panel_next_num = ic_coll.inspect_context_panel_next_num + 1
    return ic_coll.inspect_context_panel_next_num - 1

def create_context_inspect_panel(context, add_inspect_panel_name, add_inspect_panel_auto_number):
    p_r = context.scene.py_rec
    context_name = context.space_data.type
    count = add_inspect_context_panel_prop_grp(context_name, p_r.inspect_context_collections)
    # exec string to add panel class, and register the new class
    panel_label = add_inspect_panel_name
    if panel_label == "":
        panel_label = "Py Inspect"
    if add_inspect_panel_auto_number:
        if count > 0:
            panel_label = panel_label + "." + str(count).zfill(3)
    # create class for Panel, and register class to add Panel to UI
    register_inspect_panel_exec(context, count, panel_label)

class PYREC_OT_AddInspectPanel(Operator):
    bl_idname = "py_rec.add_inspect_panel"
    bl_label = "Add Inspect Panel"
    bl_description = "Add Inspect panel to active context Tools menu. If View 3D context, Inspect panel is added " \
        "in Tools -> Tool menu"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})
    add_inspect_panel_name: StringProperty(name="Name", description="Next Inspect panel created is given this name",
        default="Py Inspect")
    add_inspect_panel_auto_number: BoolProperty(name="Auto-number", description="Append number to Inspect panel " +
        "name. Number is incremented after new panel is created", default=True)

    def execute(self, context):
        create_context_inspect_panel(context, self.add_inspect_panel_name, self.add_inspect_panel_auto_number)
        return {'FINISHED'}

def remove_context_inspect_panel(panel_num):
    unregister_inspect_panel_exec(panel_num)

class PYREC_OT_RemoveInspectPanel(Operator):
    bl_idname = "py_rec.remove_inspect_panel"
    bl_label = "Remove Inspect panel?"
    bl_description = "Remove this Inspect panel"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            return {'CANCELLED'}
        remove_context_inspect_panel(self.panel_num)
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
    panel_props = ic_panel.panel_props
    if panel_props is None:
        return
    if panel_props.inspect_datablock == "":
        return
    panel_props.inspect_exec_str = "bpy.data.%s[\"%s\"]" % (panel_props.inspect_data_type, panel_props.inspect_datablock)
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectDatablockRefresh(Operator):
    bl_idname = "py_rec.inspect_datablock_refresh"
    bl_label = "Datablock Refresh"
    bl_description = "Refresh inspect attributes from 'Inspect Datablock'"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            return {'CANCELLED'}
        inspect_datablock_refresh(context, self.panel_num)
        return {'FINISHED'}

def inspect_exec_refresh(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_props = ic_panel.panel_props
    panel_options = panel_props.panel_options
    if panel_props is None or panel_options is None:
        return
    # clear index, and dir() attribute listing
    panel_props.index_type = "none"
    panel_props.index_int = 0
    panel_props.index_max_int = 0
    panel_props.index_str_coll.clear()
    panel_props.dir_inspect_exec_str = ""
    panel_props.dir_attributes.clear()
    # clear label strings
    panel_props.dir_item_exec_str = ""
    panel_props.dir_item_value_str = ""
    panel_props.dir_item_value_typename_str = ""
    panel_props.dir_item_doc_lines.clear()
    panel_props.dir_item_bl_description_lines.clear()

    # if Inspect Exec string is empty then quit
    if panel_props.inspect_exec_str == "":
        return
    # get 'Inspect Exec' result value, and update label strings based on result
    inspect_value, inspect_error = get_inspect_exec_result(panel_props.inspect_exec_str)
    if inspect_error != None:
        return

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
                index_str_item = panel_props.index_str_coll.add()
                index_str_item.name = key_name
        # check for integer type index
        has_index_int = False
        try:
            x = inspect_value[0]    # this line will raise exception if inspect_value cannot be indexed with integer
            # the following lines in the 'try' block will be run only if inspect_value can be indexed with integer
            has_index_int = True
            panel_props.index_max_int = len(inspect_value)-1
            panel_props.index_int = 0
        except:
            pass
        # set prop to indicate available index types
        if has_index_int and has_index_str:
            panel_props.index_type = "int_str"
        elif has_index_int:
            panel_props.index_type = "int"
        elif has_index_str:
            panel_props.index_type = "str"

    # dir listing can only be performed if 'inspect_value' is not None, because None does not have attributes
    if inspect_value is None:
        dir_array = []
    else:
        # get current dir() array, and quit if array is empty
        dir_array = get_dir(inspect_value)
    # update dir() listing
    panel_props.dir_inspect_exec_str = panel_props.inspect_exec_str
    panel_props.dir_attributes_index = 0

    # prepend two items in dir_attributes, to include self value and indexed value, so these values are in same format
    # as dir() attributes, because self is attribute of its parent object, and indexed values are dynamic attributes
    dir_item = panel_props.dir_attributes.add()
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
        dir_item = panel_props.dir_attributes.add()
        dir_item.name = attr_name
        item_value = getattr(inspect_value, attr_name)
        if item_value is None:
            dir_item.type_name = "None"
        else:
            dir_item.type_name = type(item_value).__name__
        dir_item.value_str = str(item_value)

    # set dir listing attribute info label strings from attribute value information
    panel_props.dir_item_exec_str = get_dir_attribute_exec_str(panel_props.dir_inspect_exec_str,
                                                               panel_props.dir_attributes[0].name)
    inspect_value, inspect_error = get_inspect_exec_result(panel_props.dir_item_exec_str)
    if inspect_error != None:
        return
    panel_props.dir_item_value_str = str(inspect_value)
    # remaining attribute info is blank if attribute value is None
    if inspect_value is None:
        return
    # set 'type name' label
    panel_props.dir_item_value_typename_str = type(inspect_value).__name__
    # set '__doc__' lines, if available as string type
    if hasattr(inspect_value, "__doc__"):
        doc_value = getattr(inspect_value, "__doc__")
        if isinstance(doc_value, str):
            string_to_lines_collection(doc_value, panel_props.dir_item_doc_lines)
    # set 'bl_description' lines, if available as string type
    if hasattr(inspect_value, "bl_description"):
        bl_desc = getattr(inspect_value, "bl_description")
        if isinstance(bl_desc, str):
            string_to_lines_collection(bl_desc, panel_props.dir_item_bl_description_lines)

class PYREC_OT_InspectExecRefresh(Operator):
    bl_idname = "py_rec.inspect_exec_refresh"
    bl_label = "Exec Refresh"
    bl_description = "Refresh inspect attributes from 'Inspect Exec' string"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            return {'CANCELLED'}
        inspect_exec_refresh(context, self.panel_num)
        return {'FINISHED'}

def inspect_attr_zoom_in(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_props = ic_panel.panel_props
    if panel_props is None:
        return

    if len(panel_props.dir_attributes) < 1:
        return
    attr_item = panel_props.dir_attributes[panel_props.dir_attributes_index]
    if attr_item is None:
        return
    attr_name = attr_item.name
    if attr_name == "" or attr_name == ".":
        return
    # zoom in to attribute
    panel_props.inspect_exec_str = panel_props.dir_inspect_exec_str + "." + attr_name
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelAttrZoomIn(Operator):
    bl_idname = "py_rec.inspect_attr_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected attribute to make it current Inspect object, and refresh 'Attributes' list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            return {'CANCELLED'}
        inspect_attr_zoom_in(context, self.panel_num)
        return {'FINISHED'}

# returns 2-tuple of (exec_str less last attribute, last attribute)
def remove_last_py_attribute(exec_str):
    output, e = lex_py_attributes(exec_str)
    # cannot remove last attribute if error, or no output, or too few output attributes
    if e != None or output is None or len(output) < 2:
        return None, None
    # use end_position of last output item to return exec_str up to, and including, end of second last attribute
    return exec_str[ : output[-2][1]+1 ], exec_str[ output[-1][0] : output[-1][1]+1 ]

def inspect_zoom_out(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_props = ic_panel.panel_props
    if panel_props is None:
        return

    # try remove last attribute of inspect object, and if success, then update exec string and refresh attribute list
    first_part, _ = remove_last_py_attribute(panel_props.dir_inspect_exec_str)
    if first_part is None:
        return
    panel_props.inspect_exec_str = first_part
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelAttrZoomOut(Operator):
    bl_idname = "py_rec.inspect_attr_zoom_out"
    bl_label = "Zoom Out"
    bl_description = "Zoom out of current Inspect object to inspect parent object, and refresh 'Value" \
        "Attributes' list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
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
                result_value, result_error = get_inspect_exec_result(data.dir_inspect_exec_str)
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

def inspect_index_int_zoom_in(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_props = ic_panel.panel_props
    if panel_props is None:
        return
    panel_props.inspect_exec_str = "%s[%i]" % (panel_props.dir_inspect_exec_str, panel_props.index_int)
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelIndexIntZoomIn(Operator):
    bl_idname = "py_rec.inspect_index_int_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected Integer Index by appending Integer Index to current exec string, and " \
        "refresh 'Attributes' list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            return {'CANCELLED'}
        inspect_index_int_zoom_in(context, self.panel_num)
        return {'FINISHED'}


def inspect_index_str_zoom_in(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_props = ic_panel.panel_props
    if panel_props is None:
        return
    panel_props.inspect_exec_str = "%s[\"%s\"]" % (panel_props.dir_inspect_exec_str, panel_props.index_str_enum)
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelIndexStrZoomIn(Operator):
    bl_idname = "py_rec.inspect_index_str_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected String Index by appending String Index to current exec string, and " \
        "refresh 'Attributes' list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            return {'CANCELLED'}
        inspect_index_str_zoom_in(context, self.panel_num)
        return {'FINISHED'}
