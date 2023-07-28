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

# Property Group Presets:
# Important: Enable 'Auto-Save Preferences' so Presets are SAVED (and not DELETED) when Blender closes.
# Use 'Copy Full Data Path', and paste to entry box in Text Editor, to create presets for any Blender type.
# Full Datapaths are added to the Preset Clipboard, fine-tuned, than saved into a Preset.
# Preset Clipboard data is different from final Presets data:
#     Properties in Presets are not linked, they are separate copies of the original pasted full datapath's value.
# Presets are organized by 'base type', which is the Python 'type'. Presets of a 'base type' can only be applied to
# the same 'type' of Blender thing.
# Each Preset's data includes (directly, or indirectly):
#     - 'base type' of value (stored in parent's value)
#     - 'property datapath' (relative to base type)
#     - 'type of value' (stored as string that represents Python type, e.g. 'int', 'str')
#     - 'value' (copied value, not linked to original property value, can be used/edited separately)
#
# Create presets by copy-pasting data properties to Text Editor sing:
#     1) Right-click menu -> Copy Full Data Path while cursor is on a property
#        e.g. Object "Cube", location X value:
#            bpy.data.objects["Cube"].location[0]
#     2) Ctrl-V paste into 'Text Editor' context to save copy of full datapath, and create a newline.
#        Only one 'Copy Full Data Path' per line - unknown line data is ignored.
#     3) Repeat steps 1) and 2) with any property of any type (Python type) of object.
#        The Text should now contain only 'Copy Full Data Path' pasted lines - one datapath per line.
#        Use '#' symbol to comment out lines of Text, if needed.
#     4) Press 'Clipboard Copy' button to read full datapaths and add to clipboard list of full datapaths.
#     5) Select 'base type' of preset from drop-down menu, for each item in the list
#     6) Select 'property datapath' of preset from drop-down menu, for each item in the list
#     7) Set the collection name and preset name of the new preset, and press 'Create Preset' button.
#
# By user choice, preset is named and saved in Blender Preferences or in File data.
# Presets saved in Blender Preferences (actually AddonPreferences) are accessible in any file, they are saved
# when Blender closes - if Auto-Save Preferences is ENABLED - important! Make sure to enable:
#     Edit -> Preferences -> Save & Load -> Auto-Save Preferences
#         Save & Load is located at bottom-left of Preferences window.
# Presets saved in a .blend file (presets in custom properties of Objects, in the 'py_rec' prop group that is saved
# with the file ) are accessible only in the currently open .blend file.
# Note: Presets can be used in asset Browser by drag-dropping an Object into the scene, and with that Object as
#       active Object, use right-click menu -> Py Preset -> From Object
#       This will add Preset Collections attached to the active Object to the 'File' Presets Collections
# Preset Collections, and Presets can be saved to Python versions and attached to Object / Material / etc. types
# with 'custom properties', e.g.
#     bpy.data.objects['Cube']['preset_collections'] = { <Preset Collections data structure, including Presets> }

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

from ..bl_util import (get_addon_module_name, do_tag_redraw)
from .func import (PRESET_SOURCE_ADDON_PREFS, get_source_preset_collections)
from .apply_func import preset_apply_preset
from .clipboard_func import (preset_clipboard_clear, preset_clipboard_remove_item, preset_clipboard_create_preset,
    copy_active_preset_to_clipboard, text_to_preset_clipboard)
from .impexp_func import (export_presets_file, import_presets_file, export_presets_object, import_presets_object,
    transfer_object_presets)
from .modify_func import (MODIFY_COLL_FUNC_MOVE, MODIFY_COLL_FUNC_RENAME, MODIFY_PRESET_FUNC_MOVE,
    MODIFY_PRESET_FUNC_RENAME, MODIFY_PRESET_FUNC_UPDATE, MODIFY_PRESET_FUNC_COPY_TO_CLIPBOARD, preset_remove_prop,
    preset_collection_modify_rename, preset_collection_remove_collection, preset_modify_rename,
    preset_collection_remove_preset, preset_collection_modify_move, update_preset, is_valid_update_datapath,
    get_modify_active_preset_collection, get_modify_active_single_preset, move_active_preset)

class PYREC_OT_PresetClipboardClear(Operator):
    bl_idname = "py_rec.preset_clipboard_clear"
    bl_label = "Clear Clipboard"
    bl_description = "Delete all items in Property Clipboard. Using this function will affect only this file"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return len(context.window_manager.py_rec.preset_options.clipboard.prop_details) > 0

    def execute(self, context):
        clipboard = context.window_manager.py_rec.preset_options.clipboard
        cb_options = context.window_manager.py_rec.preset_options.clipboard_options
        preset_clipboard_clear(cb_options, clipboard)
        do_tag_redraw()
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Clear Clipboard contents? Cancel by pressing Esc,")
        layout.label(text="or click outside this window.")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class PYREC_OT_PresetClipboardRemoveItem(Operator):
    bl_idname = "py_rec.preset_clipboard_remove_item"
    bl_label = "Remove Item"
    bl_description = "Remove active item from Preset Clipboard"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        clipboard = context.window_manager.py_rec.preset_options.clipboard
        cb_options = context.window_manager.py_rec.preset_options.clipboard_options
        return len(clipboard.prop_details) > cb_options.active_prop_detail

    def execute(self, context):
        # remove active item from prop_details
        clipboard = context.window_manager.py_rec.preset_options.clipboard
        cb_options = context.window_manager.py_rec.preset_options.clipboard_options
        if len(clipboard.prop_details) <= cb_options.active_prop_detail:
            return {'CANCELLED'}
        preset_clipboard_remove_item(cb_options, clipboard)
        do_tag_redraw()
        return {'FINISHED'}

class PYREC_OT_PresetClipboardCreatePreset(Operator):
    bl_idname = "py_rec.preset_clipboard_create_preset"
    bl_label = "Create Preset"
    bl_description = "Create new Preset from items in Property Clipboard, using only items with base types that " \
        "match selected base type"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return False
        clipboard = preset_options.clipboard
        cb_options = preset_options.clipboard_options
        return len(clipboard.prop_details) > 0 and cb_options.create_base_type != " "

    def execute(self, context):
        p_r = context.window_manager.py_rec
        preset_options = p_r.preset_options
        if preset_options.lock_changes:
            return {'CANCELLED'}
        clipboard = preset_options.clipboard
        cb_options = preset_options.clipboard_options
        if len(clipboard.prop_details) == 0 or cb_options.create_base_type == " ":
            return {'CANCELLED'}
        preset_name = preset_clipboard_create_preset(get_source_preset_collections(context), clipboard, cb_options)
        self.report({'INFO'}, "New Preset created named: " + preset_name)
        return {'FINISHED'}

class PYREC_OT_PresetPropsRemoveItem(Operator):
    bl_idname = "py_rec.preset_props_remove_item"
    bl_label = "Remove Property"
    bl_description = "Remove Property from list of Preset Properties"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        p_r = context.window_manager.py_rec
        if p_r.preset_options.lock_changes:
            return False
        preset_options = p_r.preset_options
        p_collections = get_source_preset_collections(context)
        preset = get_modify_active_single_preset(preset_options, p_collections)
        if preset is None:
            return False
        prop_details = preset.prop_details
        return preset_options.modify_options.active_detail < len(prop_details)

    def execute(self, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return {'CANCELLED'}
        p_collections = get_source_preset_collections(context)
        preset = get_modify_active_single_preset(preset_options, p_collections)
        if preset is None:
            return {'CANCELLED'}
        prop_details = preset.prop_details
        if preset_options.modify_options.active_detail >= len(prop_details):
            return {'CANCELLED'}
        preset_remove_prop(preset_options, p_collections)
        do_tag_redraw()
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Permanently remove Property from Preset? Cancel by ")
        layout.label(text="pressing Esc, or click outside this window.")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class PYREC_OT_PresetApply(Operator):
    bl_idname = "py_rec.preset_apply"
    bl_label = "Apply Preset"
    bl_description = "Apply Preset to base type"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.window_manager.py_rec.preset_options.apply_options.preset != " "

    def execute(self, context):
        p_collections = get_source_preset_collections(context)
        err_msg = preset_apply_preset(context.window_manager.py_rec.preset_options, p_collections)
        if isinstance(err_msg, str):
            self.report({'ERROR'}, err_msg)
            return {'CANCELLED'}
        return {'FINISHED'}

class PYREC_OT_PresetModifyCollection(Operator):
    bl_idname = "py_rec.preset_modify_collection"
    bl_label = "Modify"
    bl_description = "Apply Modify Function to Preset Collection"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.window_manager.py_rec.preset_options.lock_changes:
            return False
        return len(get_source_preset_collections(context)) > 0

    def execute(self, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return {'CANCELLED'}
        f = preset_options.modify_options.collection_function
        if f == MODIFY_COLL_FUNC_MOVE:
            preset_collection_modify_move(context, preset_options, preset_options.impexp_options.dup_coll_action,
                                          preset_options.impexp_options.replace_preset)
            self.report({'INFO'}, "Moved Presets Collection from one Data Source to another")
        elif f == MODIFY_COLL_FUNC_RENAME:
            preset_collection_modify_rename(preset_options, get_source_preset_collections(context))
            do_tag_redraw()
            self.report({'INFO'}, "Renamed Presets Collection")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        preset_options = context.window_manager.py_rec.preset_options
        f = preset_options.modify_options.collection_function
        if f == MODIFY_COLL_FUNC_MOVE:
            if preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
                new_data_source = ".blend File"
            else:
                new_data_source = "Addons Preferences"
            layout.label(text="Move Presets Collection to Data Source:")
            layout.label(text="  " + new_data_source)
            layout.prop(preset_options.impexp_options, "replace_preset")
            layout.label(text="  Duplicate Collection Action")
            layout.prop(preset_options.impexp_options, "dup_coll_action", text="")
        elif f == MODIFY_COLL_FUNC_RENAME:
            active_coll = get_modify_active_preset_collection(preset_options, get_source_preset_collections(context))
            label_text = "" if active_coll is None else active_coll.name
            layout.label(text="Rename Preset Collection: " + label_text)
            layout.prop(preset_options.modify_options, "collection_rename", text="")

    def invoke(self, context, event):
        preset_options = context.window_manager.py_rec.preset_options
        f = preset_options.modify_options.collection_function
        if f == MODIFY_COLL_FUNC_RENAME:
            # set initial rename string to original name string, if available
            p_coll = get_modify_active_preset_collection(preset_options, get_source_preset_collections(context))
            preset_options.modify_options.collection_rename = "" if p_coll is None else p_coll.name
        return context.window_manager.invoke_props_dialog(self)

class PYREC_OT_PresetRemoveCollection(Operator):
    bl_idname = "py_rec.preset_remove_collection"
    bl_label = "Remove Collection"
    bl_description = "Permanently delete active Collection"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return False
        return get_modify_active_preset_collection(preset_options, get_source_preset_collections(context)) != None

    def execute(self, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return {'CANCELLED'}
        preset_collection_remove_collection(preset_options, get_source_preset_collections(context))
        do_tag_redraw()
        self.report({'INFO'}, "Removed Presets Collection")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Permanently delete Preset Collection? Cancel by ")
        layout.label(text="pressing Esc, or click outside this window.")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class PYREC_OT_PresetModifyPreset(Operator):
    bl_idname = "py_rec.preset_modify_preset"
    bl_label = "Modify"
    bl_description = "Apply Modify Function to Preset"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return False
        return get_modify_active_single_preset(preset_options, get_source_preset_collections(context)) != None

    def execute(self, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return {'CANCELLED'}
        p_collections = get_source_preset_collections(context)
        if get_modify_active_single_preset(preset_options, p_collections) is None:
            return {'CANCELLED'}
        f = preset_options.modify_options.preset_function
        if f == MODIFY_PRESET_FUNC_COPY_TO_CLIPBOARD:
            copy_result = copy_active_preset_to_clipboard(context, preset_options, p_collections)
            if copy_result is None:
                self.report({'ERROR'}, "Unable to copy active Preset to Preset Clipboard")
                return {'CANCELLED'}
            self.report({'INFO'}, "Copied %d properties from Preset to Preset Clipboard" % copy_result)
        elif f == MODIFY_PRESET_FUNC_MOVE:
            move_result = move_active_preset(context, preset_options, p_collections,
                                             preset_options.impexp_options.replace_preset)
            if move_result == False:
                self.report({'ERROR'}, "Unable to move active Preset to another Collection")
                return {'CANCELLED'}
            self.report({'INFO'}, "Moved Preset")
        elif f == MODIFY_PRESET_FUNC_RENAME:
            preset_modify_rename(preset_options, p_collections)
            do_tag_redraw()
            self.report({'INFO'}, "Renamed Preset")
        elif f == MODIFY_PRESET_FUNC_UPDATE:
            update_preset(preset_options, p_collections)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        p_r = context.window_manager.py_rec
        preset_options = p_r.preset_options
        p_collections = get_source_preset_collections(context)
        f = preset_options.modify_options.preset_function
        if f == MODIFY_PRESET_FUNC_MOVE:
            layout.label(text="Data Source")
            layout.prop(preset_options.modify_options, "move_to_data_source", text="")
            layout.label(text="Move to Collection")
            layout.prop(preset_options.modify_options, "move_to_collection", text="")
            layout.prop(preset_options.impexp_options, "replace_preset", text="Replace Existing")
        elif f == MODIFY_PRESET_FUNC_RENAME:
            preset = get_modify_active_single_preset(preset_options, p_collections)
            label_text = "" if preset is None else preset.name
            layout.label(text="Rename Preset: " + label_text)
            layout.prop(preset_options.modify_options, "preset_rename", text="")
        elif f == MODIFY_PRESET_FUNC_UPDATE:
            layout.label(text="Update from Copy Full Datapath")
            layout.prop(preset_options.modify_options, "update_full_datapath", text="")
            layout.label(text="  Expected Type: " + preset_options.modify_options.base_type)
            if is_valid_update_datapath():
                layout.label(text="Datapath validated")
            else:
                layout.label(text="Enter valid Datapath")
    def invoke(self, context, event):
        wm = context.window_manager
        preset_options = wm.py_rec.preset_options
        p_collections = get_source_preset_collections(context)
        f = preset_options.modify_options.preset_function
        if f == MODIFY_PRESET_FUNC_MOVE:
            return wm.invoke_props_dialog(self)
        elif f == MODIFY_PRESET_FUNC_RENAME:
            # set initial rename string to original name string, if available
            temp_name = ""
            if len(p_collections) > preset_options.modify_options.active_collection:
                active_coll = p_collections[preset_options.modify_options.active_collection]
                if preset_options.modify_options.base_type in active_coll.base_types:
                    presets = active_coll.base_types[preset_options.modify_options.base_type].presets
                    if len(presets) > preset_options.modify_options.active_preset:
                        temp_name = presets[preset_options.modify_options.active_preset].name
            preset_options.modify_options.preset_rename = temp_name
            return wm.invoke_props_dialog(self)
        elif f == MODIFY_PRESET_FUNC_UPDATE:
            return wm.invoke_props_dialog(self)
        return self.execute(context)

class PYREC_OT_PresetRemovePreset(Operator):
    bl_idname = "py_rec.preset_remove_preset"
    bl_label = "Remove Preset"
    bl_description = "Permanently delete active Preset"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return False
        p_collections = get_source_preset_collections(context)
        return get_modify_active_single_preset(preset_options, p_collections) != None

    def execute(self, context):
        preset_options = context.window_manager.py_rec.preset_options
        if preset_options.lock_changes:
            return False
        p_collections = get_source_preset_collections(context)
        if get_modify_active_single_preset(preset_options, p_collections) is None:
            return
        preset_collection_remove_preset(context.window_manager.py_rec.preset_options, p_collections)
        self.report({'INFO'}, "Removed Preset")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Permanently delete Preset? Cancel by pressing Esc,")
        layout.label(text="or click outside this window.")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class PYREC_OT_QuicksavePreferences(Operator):
    bl_idname = "py_rec.quicksave_preferences"
    bl_label = ""
    bl_description = "Save Presets in Blender Preferences by saving Blender Preferences. This will save any " \
        "changes to Presets / Preset Collections - only applies to Preset / Preset Colleciton data in " \
        "Blender Preferences"
    bl_options = {'REGISTER'}

    def execute(self, context):
        bpy.ops.wm.save_userpref()
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Quicksave Blender Preferences? Cancel by")
        layout.label(text="pressing Esc, or click outside this window.")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class PYREC_OT_PresetExportFile(Operator, ImportHelper):
    bl_idname = "py_rec.preset_export_file"
    bl_label = "Export File"
    bl_description = "Create a .py file copy of Presets Collections from current Presets source. This .py file " \
        "can be imported into Blender with Py Preset -> Import File function"
    bl_options = {'REGISTER'}

    filter_glob: bpy.props.StringProperty(default="*.py", options={'HIDDEN'})

    def execute(self, context):
        export_result = export_presets_file(get_source_preset_collections(context), self.filepath)
        if isinstance(export_result, str):
            self.report({'ERROR'}, "Unable to export Presets Collections to file with path " + self.filepath)
            return {'CANCELLED'}
        self.report({'INFO'}, "Exported %d Presets Collections with total of %d Presets to file with path %s" \
                    % (export_result[0], export_result[1], self.filepath) )
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        p_r = context.window_manager.py_rec
        layout.label(text="Presets Data Source")
        layout.prop(p_r.preset_options, "data_source", text="")

    def invoke(self, context, event):
        self.filepath = "bl_presets.py"
        return super().invoke(context, event)

class PYREC_OT_PresetImportFile(Operator, ImportHelper):
    bl_idname = "py_rec.preset_import_file"
    bl_label = "Import File"
    bl_description = "Open a .py file with Presets Collections and copy to current Presets source. This .py file " \
        "can be created with Py Preset -> Export File function"
    bl_options = {'REGISTER'}

    filter_glob: bpy.props.StringProperty(default="*.py", options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        return context.window_manager.py_rec.preset_options.lock_changes == False

    def execute(self, context):
        if context.window_manager.py_rec.preset_options.lock_changes:
            return {'CANCELLED'}
        preset_options = context.window_manager.py_rec.preset_options
        import_result = import_presets_file(get_source_preset_collections(context), self.filepath,
            preset_options.impexp_options.dup_coll_action, preset_options.impexp_options.replace_preset)
        if isinstance(import_result, str):
            self.report({'ERROR'}, import_result)
            return {'CANCELLED'}
        if isinstance(import_result, (int, int)):
            self.report({'INFO'}, "Imported %d Presets Collections with total of %d Presets from file with path %s" \
                        % (import_result[0], import_result[1], self.filepath))
        do_tag_redraw()
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        p_r = context.window_manager.py_rec
        layout.label(text="Presets Data Source")
        layout.prop(p_r.preset_options, "data_source", text="")
        layout.separator()
        layout.label(text="Import Options")
        layout.prop(p_r.preset_options.impexp_options, "replace_preset")
        layout.label(text="  Duplicate Collection Action")
        layout.prop(p_r.preset_options.impexp_options, "dup_coll_action", text="")

    def invoke(self, context, events):
        self.filepath = "bl_presets.py"
        return super().invoke(context, events)

class PYREC_OT_PresetExportObject(Operator):
    bl_idname = "py_rec.preset_export_object"
    bl_label = "Export Object"
    bl_description = "Attach a .py string to active Object, with copy of Presets Collections from current Presets " \
        "source. This .py string attached to active Object can be imported into Blender with Py Preset -> " \
        "Import Object function"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        act_ob = context.active_object
        if act_ob is None:
            self.report({'ERROR'}, "Unable to Export Presets Collections, no active Object")
            return {'CANCELLED'}
        export_result = export_presets_object(get_source_preset_collections(context), act_ob)
        if isinstance(export_result, str):
            self.report({'ERROR'}, "Unable to export Presets Collections to Object named " + act_ob.name)
            return {'CANCELLED'}
        self.report({'INFO'}, "Exported %d Presets Collections with total of %d Presets to Object named %s" \
                    % (export_result[0], export_result[1], act_ob.name) )
        return {'FINISHED'}

class PYREC_OT_PresetImportObject(Operator):
    bl_idname = "py_rec.preset_import_object"
    bl_label = "Import Object"
    bl_description = "Read a .py string attached to active Object, to create Presets Collections and add to " \
        "current Presets Collections Data Source. Current Presets Collections data can be attached to any " \
        "Object with Py Preset -> Export Object function"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None and context.window_manager.py_rec.preset_options.lock_changes == False

    def execute(self, context):
        if context.active_object is None or context.window_manager.py_rec.preset_options.lock_changes:
            return {'CANCELLED'}
        preset_options = context.window_manager.py_rec.preset_options
        import_result = import_presets_object(get_source_preset_collections(context), context.active_object,
            preset_options.impexp_options.dup_coll_action, preset_options.impexp_options.replace_preset)
        if isinstance(import_result, str):
            self.report({'ERROR'}, import_result)
            return {'CANCELLED'}
        do_tag_redraw()
        self.report({'INFO'}, "Imported %d Presets Collections with total of %d Presets from Object named %s" \
                    % (import_result[0], import_result[1], context.active_object.name))
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        p_r = context.window_manager.py_rec
        layout.label(text="Presets Data Source")
        layout.prop(p_r.preset_options, "data_source", text="")
        layout.separator()
        layout.label(text="Import Options")
        layout.prop(p_r.preset_options.impexp_options, "replace_preset")
        layout.label(text="  Duplicate Collection Action")
        layout.prop(p_r.preset_options.impexp_options, "dup_coll_action", text="")

    def invoke(self, context, events):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class PYREC_OT_TransferObjectPresets(Operator):
    bl_idname = "py_rec.transfer_object_presets"
    bl_label = "Transfer Presets"
    bl_description = "Copy Presets Collections data from active Object to all other selected Objects"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        sel_ob = [ ob for ob in context.selected_objects if ob != context.active_object ]
        return context.active_object != None and len(sel_ob) >= 1

    def execute(self, context):
        sel_ob = [ ob for ob in context.selected_objects if ob != context.active_object ]
        if context.active_object is None or len(sel_ob) < 1:
            return {'CANCELLED'}
        err_msg = transfer_object_presets(context.active_object, sel_ob)
        if isinstance(err_msg, str):
            self.report({'ERROR'}, "Unable to Transfer Presets between Objects, " + err_msg)
            return {'CANCELLED'}
        return {'FINISHED'}

class PYREC_OT_TextToPresetClipboard(Operator):
    bl_idname = "py_rec.text_to_preset_clipboard"
    bl_label = "Text to Clipboard"
    bl_description = "Read current Text (in Text-Editor) and try to add each line to Presets Clipboard"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.space_data.text != None

    def execute(self, context):
        if context.space_data.text is None:
            return {'CANCELLED'}
        text_to_preset_clipboard(context.space_data.text)
        return {'FINISHED'}
