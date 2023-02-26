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

# TODO: If dir() item is indexable (e.g. array, tuple, dict), then indicate this with '[]' item at top of dir()
#       attributes list.
#       If user selects the '[]' item in the list, then display integer index / string index / dropdown index picker.
# dir() listing will have two items prepended to it:
#    .
#    []
# '.' will show value, instead of attribute of value
# '[]' will show indexed value, if value is indexable, instead of value

import bpy
from bpy.types import (Operator, Panel, PropertyGroup, UIList)
from bpy.props import (BoolProperty, IntProperty, StringProperty)
from bpy.utils import (register_class, unregister_class)

from .inspect_options import PYREC_OT_InspectOptions
from .inspect_func import (get_dir, get_inspect_context_collection, get_inspect_context_panel)

inspect_panel_classes = {}
PANEL_REGISTER_EXEC_STR = "class PYREC_OBJECT_PT_Inspect%i(Panel):\n" \
      "    bl_space_type = '%s'\n" \
      "    bl_region_type = 'UI'\n" \
      "    bl_category = \"Item\"\n" \
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
        box.label(text="Attributes")
        row = box.row()
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

        row = box.row()
        row.template_list("PYREC_UL_InspectDirList", "", panel_props, "dir_listing", panel_props,
                          "dir_listing_index", rows=5)
        col = row.column(align=True)
        col.operator(PYREC_OT_InspectPanelZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = self.panel_num
        col.operator(PYREC_OT_InspectPanelZoomOut.bl_idname, icon='ZOOM_OUT', text="").panel_num = self.panel_num

    box = layout.box()
    if panel_props.dir_listing_exec_str != "":
        box.label(text="Exec: " + panel_props.dir_item_exec_str)
        box.label(text="Type: " + panel_props.dir_item_value_typename_str)
        if panel_options.display_value_selector:
#            value = get_inspect_exec_result(panel_props.inspect_exec_str)
#            if value != None:
#                box.prop(value, panel_props.dir_listing[panel_props.dir_listing_index], text="Value")
            box.label(text="Value: " + panel_props.dir_item_value_str)
        else:
            box.label(text="Value: " + panel_props.dir_item_value_str)

        if panel_options.display_attr_doc:
            box.label(text="__doc__: " + panel_props.dir_item_doc_str)
        if panel_options.display_attr_bl_description:
            box.label(text="bl_description: " + panel_props.dir_item_bl_description_str)

def register_inspect_panel_exec(context, index, panel_label):
    exec_str = PANEL_REGISTER_EXEC_STR % (index, context.space_data.type, panel_label, index, index, index,
                                          index)
#    print("\n*** register start of exec_str = ***" + exec_str + "\n\n*** end of exec_str = ***\n")
    exec(exec_str)

def unregister_inspect_panel_exec(index):
    if inspect_panel_classes.get("PYREC_OBJECT_PT_Inspect%i" % index) is None:
        return
    # remove from list of classes before unregistering class, to prevent reference errors
    exec_str = PANEL_UNREGISTER_EXEC_STR % (index, index)
#    print("\n*** unregister start of exec_str = ***" + exec_str + "\n\n*** end of exec_str = ***\n")
    exec(exec_str)

def get_inspect_exec_result(inspect_exec_str):
    if inspect_exec_str == "":
        return
    ie_str = "global inspect_exec_result\ninspect_exec_result['result'] = %s" % inspect_exec_str
#    print("\nget_inspect_exec_result = \n" + ie_str + "\n")
    try:
        exec(ie_str)
    except:
        return None
#    print("inspect_exec_result =")
#    print(inspect_exec_result["result"])
#    print()
    r = inspect_exec_result["result"]
    del inspect_exec_result["result"]
    return r

def get_dir_attribute_exec_str(base, attr_name):
    # if exec str is '.', which means 'self' is selected, then do not append attribute name
    if attr_name == ".":
        return base
    # if exec str is '[]', which means 'indexed value' is selected, then ...
    if attr_name == "[]":
        return base     # TODO more code ##################################
    return base + "." + attr_name

def update_inspect_dir_list(self, value):
    # self, e.g.  PYREC_PG_InspectPanelProps
    # value, e.g. bpy.types.Context
    panel_props = self
    panel_props.dir_item_exec_str = ""
    panel_props.dir_item_value_str = ""
    panel_props.dir_item_value_typename_str = ""
    panel_props.dir_item_doc_str = ""
    panel_props.dir_item_bl_description_str = ""
    # quit if dir() listing is empty
    if len(panel_props.dir_listing) < 1:
        return
    # set dir listing attribute info label strings from attribute value information
    panel_props.dir_item_exec_str = get_dir_attribute_exec_str(panel_props.dir_listing_exec_str,
        panel_props.dir_listing[panel_props.dir_listing_index].name)
    # exec the string to get the attribute's value
    result_value = get_inspect_exec_result(panel_props.dir_item_exec_str)
    panel_props.dir_item_value_str = str(result_value)
    # remaining attribute info is blank if attribute value is None
    if result_value is None:
        return
    # set 'type name' label
    panel_props.dir_item_value_typename_str = type(result_value).__name__
    # set '__doc__' label, if available as string type
    if hasattr(result_value, "__doc__"):
        doc = getattr(result_value, "__doc__")
        if isinstance(doc, str):
            panel_props.dir_item_doc_str = doc
    # set 'bl_description' label, if available as string type
    if hasattr(result_value, "bl_description"):
        bl_desc = getattr(result_value, "bl_description")
        if isinstance(bl_desc, str):
            panel_props.dir_item_bl_description_str = bl_desc

def add_inspect_context_panel_prop_grp(context_name, inspect_context_collections):
    # add PropertyGroup for inspect context panel
    ic_coll = get_inspect_context_collection(context_name, inspect_context_collections)
    if ic_coll is None:
        ic_coll = inspect_context_collections.add()
        ic_coll.name = context_name
    # create new panel
    i_panel = ic_coll.inspect_context_panels.add()
    i_panel.inspect_panel_number = ic_coll.inspect_context_panel_next_num
    ic_coll.inspect_context_panel_next_num = ic_coll.inspect_context_panel_next_num + 1
    return i_panel.inspect_panel_number

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
        "in Tools -> Item menu"
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
    # clear dir listing
    panel_props.dir_listing_exec_str = ""
    panel_props.dir_listing.clear()
    # clear label strings
    panel_props.dir_item_exec_str = ""
    panel_props.dir_item_value_str = ""
    panel_props.dir_item_value_typename_str = ""
    panel_props.dir_item_doc_str = ""
    panel_props.dir_item_bl_description_str = ""

    # if Inspect Exec string is empty then quit
    if panel_props.inspect_exec_str == "":
        return
    # get 'Inspect Exec' result value, and update label strings based on result
    inspect_value = get_inspect_exec_result(panel_props.inspect_exec_str)
    # dir listing can only be performed if 'inspect_value' is not None, because None does not have attributes
    if inspect_value is None:
        return
    # get current dir() array, and quit if array is empty
    dir_array = get_dir(inspect_value)
    if len(dir_array) < 1:
        return
    # update dir() listing
    panel_props.dir_listing_exec_str = panel_props.inspect_exec_str
    panel_props.dir_listing_index = 0

    # prepend two items in dir_listing, to include self value and indexed value, so these values are in same format
    # as dir() attributes, because self is attribute of its parent object, and indexed values are dynamic attributes
    dir_item = panel_props.dir_listing.add()
    dir_item.name = "."
    dir_item.type_name = ". Self value"
    # if inspect_value is indexable then add indexed value item
    if hasattr(inspect_value, '__len__'):
        dir_item = panel_props.dir_listing.add()
        dir_item.name = "[]"
        dir_item.type_name = "[] Indexed value"
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
        dir_item = panel_props.dir_listing.add()
        dir_item.name = attr_name
        item_value = getattr(inspect_value, attr_name)
        if item_value is None:
            dir_item.type_name = "None"
        else:
            dir_item.type_name = type(item_value).__name__
        dir_item.value_str = str(item_value)

    # set dir listing attribute info label strings from attribute value information
    panel_props.dir_item_exec_str = get_dir_attribute_exec_str(panel_props.dir_listing_exec_str,
                                                               panel_props.dir_listing[0].name)
    inspect_value = get_inspect_exec_result(panel_props.dir_item_exec_str)
    panel_props.dir_item_value_str = str(inspect_value)
    # remaining attribute info is blank if attribute value is None
    if inspect_value is None:
        return
    # set 'type name' label
    panel_props.dir_item_value_typename_str = type(inspect_value).__name__
    # set '__doc__' label, if available as string type
    if hasattr(inspect_value, "__doc__"):
        doc_attr = getattr(inspect_value, "__doc__")
        if isinstance(doc_attr, str):
            panel_props.dir_item_doc_str = doc_attr
    # set 'bl_description' label, if available as string type
    if hasattr(inspect_value, "bl_description"):
        bl_desc = getattr(inspect_value, "bl_description")
        if isinstance(bl_desc, str):
            panel_props.dir_item_bl_description_str = bl_desc

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

def inspect_zoom_in(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_props = ic_panel.panel_props
    if panel_props is None:
        return

    attr_name = panel_props.dir_listing[panel_props.dir_listing_index].name
    print(attr_name)
    if attr_name == "" or attr_name == "." or attr_name == "[]":
        print("skip this attr_name")
        return
    # zoom in to attribute
    panel_props.inspect_exec_str = panel_props.inspect_exec_str + "." + attr_name
    # do refresh using modified 'inspect_exec_str'
    inspect_exec_refresh(context, panel_num)

class PYREC_OT_InspectPanelZoomIn(Operator):
    bl_idname = "py_rec.inspect_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected attribute to make it current Inspect object, and refresh 'Value" \
        "Attributes' list"
    bl_options = {'REGISTER', 'UNDO'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        if self.panel_num == -1:
            return {'CANCELLED'}
        inspect_zoom_in(context, self.panel_num)
        return {'FINISHED'}

def inspect_zoom_out(context, panel_num):
    ic_panel = get_inspect_context_panel(panel_num, context.space_data.type,
                                         context.scene.py_rec.inspect_context_collections)
    if ic_panel is None:
        return
    panel_props = ic_panel.panel_props
    if panel_props is None:
        return

#    attr_name = panel_props.dir_listing[panel_props.dir_listing_index].name
#    old_exec_str = panel_props.inspect_exec_str
    ############### TODO more code here to zoom out using Finite State Machine

class PYREC_OT_InspectPanelZoomOut(Operator):
    bl_idname = "py_rec.inspect_zoom_out"
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

class PYREC_PG_InspectDirItem(PropertyGroup):
    type_name: StringProperty()
    value_str: StringProperty()

class PYREC_UL_InspectDirList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # self,  e.g. PYREC_UL_InspectDirList
        # data, PYREC_PG_InspectPanelProps
        # item, e.g. PYREC_PG_InspectDirItem
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
            if panel_options.display_value_selector and item.name != "." and item.name != "[]" and \
                not item.name.startswith("__") and item.name != "bl_rna":
                if data.dir_listing_exec_str != "":
                    result = get_inspect_exec_result(data.dir_listing_exec_str)
                    if result != None and hasattr(result, item.name):
                        try:
                            row.prop(result, item.name, text="")
                            return
                        except:
                            pass
            # show value str if value selector not available
            row.label(text=item.value_str)
