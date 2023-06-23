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
from bpy.types import Operator
from bpy.props import IntProperty

from .func import (get_inspect_context_panel, get_pre_exec_str, refresh_exec_inspect_value)
from .operator import (PYREC_OT_RemoveInspectPanel, PYREC_OT_InspectOptions, PYREC_OT_InspectChoosePy,
    PYREC_OT_InspectPanelArrayIndexZoomIn, PYREC_OT_InspectPanelArrayKeyZoomIn, PYREC_OT_InspectPanelAttrZoomIn,
    PYREC_OT_InspectPanelAttrZoomOut, PYREC_OT_InspectRecordAttribute, PYREC_OT_InspectCopyAttribute,
    PYREC_OT_InspectPasteAttribute)
from ..py_code_utils import get_dir

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

    # get 'Inspect Exec' result value and, if result matches expectation then allow attribute list to be drawn
    pre_exec_str = get_pre_exec_str(ic_panel)
    post_exec_str = ic_panel.dir_inspect_exec_str
    inspect_value, inspect_error = refresh_exec_inspect_value(pre_exec_str, post_exec_str)
    # check new inspect exec state against old state
    exec_state = ic_panel.inspect_exec_state
    show_attr_list = True
    # check for empty state / inspect error
    if len(exec_state) == 0 or inspect_error != None:
        show_attr_list = False
    # check for same value as converted to string - to avoid invalid reference errors
    elif str(inspect_value) != exec_state.get("exec_value_str"):
        show_attr_list = False
    # check for same type
    elif str(type(inspect_value)) != exec_state.get("exec_value_type"):
        show_attr_list = False
    elif inspect_value is None:
        show_attr_list = False
    else:
        attr_names = get_dir(inspect_value)
        # check for same number of attributes
        if len(attr_names) != exec_state["exec_value_attr_name_count"]:
            show_attr_list = False
        # check for full set intersection
        elif len(set(attr_names) & exec_state["exec_value_attr_names"]) != exec_state["exec_value_attr_name_count"]:
            show_attr_list = False
    # if unable to display list, then clear dictionary to prevent invalid references,
    # i.e. exec_state["exec_value"]
    if not show_attr_list:
        ic_panel.inspect_exec_state.clear()
    # top row of Py Inspect panel buttons, always visible
    row = layout.row()
    row.operator(PYREC_OT_RemoveInspectPanel.bl_idname, icon='REMOVE', text="").panel_num = self.panel_num
    row.separator()
    row.operator(PYREC_OT_InspectOptions.bl_idname, icon='OPTIONS', text="").panel_num = self.panel_num
    row.separator()
    row.operator(PYREC_OT_InspectChoosePy.bl_idname, icon='HIDE_OFF', text="").panel_num = self.panel_num

    # array index / key
    array_index_key_type = ic_panel.array_index_key_type
    if array_index_key_type == "int" or array_index_key_type == "str" or array_index_key_type == "int_str":
        box = layout.box()
        box.label(text="Index Item Count: "+str(max(len(ic_panel.array_key_set),
                                                        ic_panel.array_index_max+1)))
    if array_index_key_type == "int" or array_index_key_type == "int_str":
        row = box.row()
        row.prop(ic_panel, "array_index", text="")
        row.operator(PYREC_OT_InspectPanelArrayIndexZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
            self.panel_num
    if array_index_key_type == "str" or array_index_key_type == "int_str":
        row = box.row()
        row.prop(ic_panel, "array_key", text="")
        row.operator(PYREC_OT_InspectPanelArrayKeyZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
            self.panel_num

    # current inspect exec string and attributes count
    box = layout.box()
    box.label(text="Inspect: " + ic_panel.dir_inspect_exec_str)
    if show_attr_list:
        # attributes of inspect exec value
        # subtract 1 to account for the '.' list item (which represents 'self' value)
        box.label(text="Inspect Attributes ( %i )" % ( 0 if len(ic_panel.dir_attributes)-1 < 0 else \
                                                           len(ic_panel.dir_attributes)-1 ))
    else:
        box.label(text="Inspect Attributes ( 0 )")
    # column size sliders
    if panel_options.display_dir_attribute_type or panel_options.display_dir_attribute_value:
        row = box.row(align=True)
        row.prop(ic_panel, "dir_col_size1", slider=True, text="Name")
        if panel_options.display_dir_attribute_type and panel_options.display_dir_attribute_value:
            row.prop(ic_panel, "dir_col_size2", slider=True, text="Type / Value")
    # container row
    cont_row = box.row(align=True)
    # attribute list column
    attr_list_col = cont_row.column()
    # list labels
    split = attr_list_col.split(factor=ic_panel.dir_col_size1)
    split.label(text="Name")
    if panel_options.display_dir_attribute_type:
        if panel_options.display_dir_attribute_value:
            split = split.split(factor=ic_panel.dir_col_size2)
        split.label(text="Type")
    if panel_options.display_dir_attribute_value:
        split.label(text="Value")
    if show_attr_list:
        # draw list
        list_classname = "PYREC_UL_%s_DirAttributeList%s" % (context_name, ic_panel.name)
        attr_list_col.template_list(list_classname, "", ic_panel, "dir_attributes", ic_panel, "dir_attributes_index",
                                    rows=5)
    else:
        # draw empty box
        attr_list_col.box().separator(factor=8)

    # functions column
    function_col = cont_row.column(align=True)
    function_col.operator(PYREC_OT_InspectPanelAttrZoomIn.bl_idname, icon='ZOOM_IN', text="").panel_num = \
        self.panel_num
    function_col.separator()
    function_col.operator(PYREC_OT_InspectPanelAttrZoomOut.bl_idname, icon='ZOOM_OUT', text="").panel_num = \
        self.panel_num
    function_col.separator(factor=2)
    function_col.operator(PYREC_OT_InspectRecordAttribute.bl_idname, icon='DOCUMENTS', text="").panel_num = \
        self.panel_num
    function_col.operator(PYREC_OT_InspectCopyAttribute.bl_idname, icon='COPY_ID', text="").panel_num = \
        self.panel_num
    function_col.operator(PYREC_OT_InspectPasteAttribute.bl_idname, icon='PASTEDOWN', text="").panel_num = \
        self.panel_num
    function_col.separator(factor=2)
    function_col.prop(panel_options, "display_dir_attribute_type", text="", icon='CON_TRANSFORM_CACHE', toggle=True)
    function_col.prop(panel_options, "display_dir_attribute_value", text="", icon='CON_TRANSFORM', toggle=True)
    function_col.prop(panel_options, "display_attr_doc", text="", icon='HELP', toggle=True)

    # display documentation / description if enabled
    if panel_options.display_attr_doc:
        attr_list_col.label(text="__doc__:")
        if show_attr_list:
            # draw __doc__ lines
#            split = attr_list_col.split(factor=0.95)
            list_classname = "PYREC_UL_%s_DocLineList%s" % (context_name, ic_panel.name)
            attr_list_col.template_list(list_classname, "", ic_panel, "dir_item_doc_lines", ic_panel,
                                        "dir_item_doc_lines_index", rows=2)
        else:
            # draw empty box
            attr_list_col.box().separator(factor=8)
