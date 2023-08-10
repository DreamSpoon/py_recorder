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

import traceback

import bpy
from bpy.types import Operator
from bpy.props import (IntProperty, StringProperty)

from .func import (get_inspect_context_panel, create_context_inspect_panel, inspect_attr_zoom_in,
    inspect_zoom_out, inspect_array_index_zoom_in, inspect_array_key_zoom_in, restore_inspect_context_panels,
    inspect_active_refresh, inspect_datablock_refresh, get_inspect_active_type_items, get_active_thing_inspect_str,
    unregister_inspect_panel, inspect_exec_refresh, get_attribute_python_str, apply_inspect_options)
from ..log_text import log_text_append

RECORD_ATTRIBUTE_TEXT_NAME = "pyrec_attribute.py"

class PYREC_OT_InspectOptions(Operator):
    bl_description = "Open Py Inspect panel Options window"
    bl_idname = "py_rec.inspect_options"
    bl_label = "Options"
    bl_options = {'REGISTER'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        p_r = context.window_manager.py_rec
        context_name = context.space_data.type
        # Py Inspect panel in View3D context also shows in Properties context -> Tool properties
        if context_name == "PROPERTIES":
            context_name = "VIEW_3D"
        ic_panel = get_inspect_context_panel(self.panel_num, context_name, p_r.inspect_context_collections)
        if ic_panel is None:
            return
        panel_options = ic_panel.panel_options
        if panel_options is None:
            return
        ret_val, error_msg = apply_inspect_options(context, self.panel_num, ic_panel, panel_options, context_name)
        if ret_val == 'CANCELLED':
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}
        return {'FINISHED'}

    def draw(self, context):
        p_r = context.window_manager.py_rec
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type, p_r.inspect_context_collections)
        if ic_panel is None:
            return
        panel_options = ic_panel.panel_options
        if panel_options is None:
            return
        layout = self.layout

        box = layout.box()
        box.prop(panel_options, "panel_option_label")

        box = layout.box()
        box.label(text="Attribute Value")
        box.prop(panel_options, "display_value_selector")

        box = layout.box()
        box.label(text="Attribute Type")
        row = box.row()
        row.prop(panel_options, "display_attr_type_only")
        col = row.column()
        col.prop(panel_options, "display_attr_type_function")
        col.prop(panel_options, "display_attr_type_builtin")
        col.prop(panel_options, "display_attr_type_bl")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class PYREC_OT_RemoveInspectPanel(Operator):
    bl_idname = "py_rec.remove_inspect_panel"
    bl_label = "Remove Inspect panel?"
    bl_description = "Remove this Inspect panel"
    bl_options = {'REGISTER'}

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

class PYREC_OT_InspectPanelAttrZoomIn(Operator):
    bl_idname = "py_rec.inspect_attr_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected attribute to make it current Inspect object, and refresh Inspect " \
        "Attributes list"
    bl_options = {'REGISTER'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Unable to Zoom In to Attribute because Attributes List is empty")
            return {'CANCELLED'}
        inspect_attr_zoom_in(context, ic_panel, self.panel_num)
        return {'FINISHED'}

class PYREC_OT_InspectPanelAttrZoomOut(Operator):
    bl_idname = "py_rec.inspect_attr_zoom_out"
    bl_label = "Zoom Out"
    bl_description = "Zoom out of current Inspect object to inspect parent object, and refresh Inspect Attributes list"
    bl_options = {'REGISTER'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None or len(ic_panel.dir_attributes) == 0:
            self.report({'ERROR'}, "Unable to Zoom Out from Attribute because Attributes List is empty")
            return {'CANCELLED'}
        inspect_zoom_out(context, ic_panel, self.panel_num)
        return {'FINISHED'}

class PYREC_OT_InspectPanelArrayIndexZoomIn(Operator):
    bl_idname = "py_rec.inspect_array_index_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected Integer Index by appending Integer Index to current exec string, and " \
        "refresh Inspect Attributes list"
    bl_options = {'REGISTER'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None:
            self.report({'ERROR'}, "Unable to Zoom In to Integer Index because Inspect Panel reference is missing")
            return {'CANCELLED'}
        inspect_array_index_zoom_in(context, ic_panel, self.panel_num)
        return {'FINISHED'}

class PYREC_OT_InspectPanelArrayKeyZoomIn(Operator):
    bl_idname = "py_rec.inspect_array_key_zoom_in"
    bl_label = "Zoom In"
    bl_description = "Zoom in to selected String Index by appending String Index to current exec string, and " \
        "refresh Inspect Attributes list"
    bl_options = {'REGISTER'}

    panel_num: IntProperty(default=-1, options={'HIDDEN'})

    def execute(self, context):
        ic_panel = get_inspect_context_panel(self.panel_num, context.space_data.type,
                                             context.window_manager.py_rec.inspect_context_collections)
        if ic_panel is None:
            self.report({'ERROR'}, "Unable to Zoom In to String Index because Inspect Panel reference is missing")
            return {'CANCELLED'}
        inspect_array_key_zoom_in(context, ic_panel, self.panel_num)
        return {'FINISHED'}

class PYREC_OT_RestoreInspectContextPanels(Operator):
    bl_idname = "py_rec.restore_inspect_context_panels"
    bl_label = "Restore Context Inspect Panels"
    bl_description = "Restore 'Py Inspect' panels in current .blend file. Use this if context 'Py Inspect' panels " \
        "are missing, e.g. after .blend file is loaded"
    bl_options = {'REGISTER'}

    def execute(self, context):
        restore_inspect_context_panels(context.window_manager.py_rec.inspect_context_collections)
        return {'FINISHED'}

class PYREC_OT_InspectRecordAttribute(Operator):
    bl_description = "Record single/all attributes to Python code with from/to/output options"
    bl_idname = "py_rec.inspect_record_attribute"
    bl_label = "Record Attribute"
    bl_options = {'REGISTER'}

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
            finished, out_str = get_attribute_python_str(ic_panel, ic_panel.dir_inspect_exec_str, attr_name,
                                                         attr_record_options)
            if finished == 'CANCELLED':
                self.report({'ERROR'}, out_str)
                return {'CANCELLED'}
        # get all inspect value Python attributes
        else:
            for attr_item in ic_panel.dir_attributes:
                if attr_item.name == ".":
                    continue
                finished, temp_str = get_attribute_python_str(ic_panel, ic_panel.dir_inspect_exec_str,
                                                              attr_item.name, attr_record_options)
                if finished == 'CANCELLED':
                    continue
                out_str = out_str + temp_str
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
    bl_options = {'REGISTER'}

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
    bl_options = {'REGISTER'}

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
        return self.paste_attribute_ref(context, ic_panel)

    def paste_attribute_ref(self, context, ic_panel):
        set_val_str = ic_panel.dir_inspect_exec_str
        attr_name = ic_panel.dir_attributes[ic_panel.dir_attributes_index].name
        if attr_name != ".":
            set_val_str = set_val_str + "." + attr_name
        get_val_str = copy_attribute_ref["attribute_ref"]
        try:
            exec(set_val_str + " = " + get_val_str)
        except:
            log_text = log_text_append("Exception raised by Paste Attribute exec of:\n  %s\n%s" %
                            (set_val_str + " = " + get_val_str, traceback.format_exc()) )
            self.report({'ERROR'}, "Unable to Paste Attribute, exception raised by exec() with paste " \
                "reference string. See Text named '%s' for details" % log_text.name)
            return {'CANCELLED'}
        return {'FINISHED'}

class PYREC_OT_InspectChoosePy(Operator):
    bl_description = "Open window to choose Python object to inspect"
    bl_idname = "py_rec.inspect_choose_py"
    bl_label = "Inspect"
    bl_options = {'REGISTER'}

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

class PYREC_OT_PyInspectActiveObject(Operator):
    bl_description = "Inspect active Object with new Py Inspect panel (see context Tools menu)"
    bl_idname = "py_rec.py_inspect_active_object"
    bl_label = "Object"
    bl_options = {'REGISTER'}

    inspect_type: StringProperty(default="OBJECT", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return len( get_inspect_active_type_items(None, context) ) > 0

    def execute(self, context):
        start_string = get_active_thing_inspect_str(context, self.inspect_type)
        if not create_context_inspect_panel(context, context.space_data.type,
                                            context.window_manager.py_rec.inspect_context_collections, start_string):
            self.report({'ERROR'}, "Inspect Active: Unable to inspect " + self.inspect_type)
            return {'CANCELLED'}
        return {'FINISHED'}
