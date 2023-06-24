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
#     4) Press 'Clipboard Copy' button to read full datapaths and add to clipbaord list of full datapaths.
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
from bpy.types import Operator

from .func import (PRESET_SOURCE_ADDON_PREFS, MODIFY_COLL_FUNC_RENAME, MODIFY_PRESET_FUNC_RENAME,
    preset_clipboard_clear, preset_clipboard_remove_item, preset_clipboard_create_preset, preset_remove_prop,
    preset_apply_preset, preset_collection_remove_collection, preset_collection_remove_preset,
    preset_collection_modify_rename, preset_modify_rename)

PREFS_ADDONS_NAME = "py_recorder"

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
        preset_clipboard_remove_item(cb_options, clipboard)
        return {'FINISHED'}

class PYREC_OT_PresetClipboardCreatePreset(Operator):
    bl_idname = "py_rec.preset_clipboard_create_preset"
    bl_label = "Create Preset"
    bl_description = "Create new Preset from items in Property Clipboard, using only items with base types that " \
        "match selected base type"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        p_r = context.window_manager.py_rec
        if p_r.preset_options.lock_changes:
            return False
        clipboard = p_r.preset_options.clipboard
        cb_options = p_r.preset_options.clipboard_options
        return len(clipboard.prop_details) > 0 and cb_options.create_base_type != " "

    def execute(self, context):
        p_r = context.window_manager.py_rec
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_r.preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        clipboard = context.window_manager.py_rec.preset_options.clipboard
        cb_options = context.window_manager.py_rec.preset_options.clipboard_options
        preset_name = preset_clipboard_create_preset(p_collections, clipboard, cb_options)
        # report 'Preset created'
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
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        if p_options.modify_active_collection >= len(p_collections):
            return False
        base_types = p_collections[p_options.modify_active_collection].base_types
        if p_options.modify_base_type not in base_types:
            return False
        presets = base_types[p_options.modify_base_type].presets
        if p_options.modify_active_preset >= len(presets):
            return False
        prop_details = presets[p_options.modify_active_preset].prop_details
        return p_options.modify_detail < len(prop_details)

    def execute(self, context):
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        preset_remove_prop(p_options, p_collections)
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
        return context.window_manager.py_rec.preset_options.apply_preset != " "

    def execute(self, context):
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        preset_apply_preset(p_options, p_collections)
        return {'FINISHED'}

class PYREC_OT_PresetModifyCollection(Operator):
    bl_idname = "py_rec.preset_modify_collection"
    bl_label = "Modify"
    bl_description = "Apply Modify Function to Preset Collection"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        p_r = context.window_manager.py_rec
        if p_r.preset_options.lock_changes:
            return False
        if p_r.preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        return len(p_collections) > 0

    def execute(self, context):
        p_options = context.window_manager.py_rec.preset_options
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = context.window_manager.py_rec.preset_collections
        preset_collection_modify_rename(p_options, p_collections)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        f = p_options.modify_collection_function
        if f == MODIFY_COLL_FUNC_RENAME:
            if len(p_collections) > p_options.modify_active_collection:
                label_text = p_collections[p_options.modify_active_collection].name
            else:
                label_text = ""
            layout.label(text="Rename Preset Collection: " + label_text)
            layout.prop(p_options, "modify_collection_rename", text="")

    def invoke(self, context, event):
        wm = context.window_manager
        p_options = wm.py_rec.preset_options
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = wm.py_rec.preset_collections
        f = p_options.modify_collection_function
        if f == MODIFY_COLL_FUNC_RENAME:
            # set initial rename string to original name string, if available
            if len(p_collections) > p_options.modify_active_collection:
                p_options.modify_collection_rename = p_collections[p_options.modify_active_collection].name
            else:
                p_options.modify_collection_rename = ""
        return wm.invoke_props_dialog(self)

class PYREC_OT_PresetRemoveCollection(Operator):
    bl_idname = "py_rec.preset_remove_collection"
    bl_label = "Remove Collection"
    bl_description = "Permanently delete active Collection"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        p_r = context.window_manager.py_rec
        if p_r.preset_options.lock_changes:
            return False
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        return p_options.modify_active_collection < len(p_collections)

    def execute(self, context):
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        preset_collection_remove_collection(p_options, p_collections)
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
        p_r = context.window_manager.py_rec
        if p_r.preset_options.lock_changes:
            return False
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        if p_options.modify_active_collection >= len(p_collections):
            return False
        tp = p_collections[p_options.modify_active_collection].base_types
        if p_options.modify_base_type not in tp:
            return False
        return p_options.modify_active_preset < len(tp[p_options.modify_base_type].presets)

    def execute(self, context):
        p_options = context.window_manager.py_rec.preset_options
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = context.window_manager.py_rec.preset_collections
        preset_modify_rename(p_options, p_collections)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        f = p_options.modify_preset_function
        if f == MODIFY_PRESET_FUNC_RENAME:
            label_text = ""
            if len(p_collections) > p_options.modify_active_collection:
                active_coll = p_collections[p_options.modify_active_collection]
                if p_options.modify_base_type in active_coll.base_types:
                    presets = active_coll.base_types[p_options.modify_base_type].presets
                    if len(presets) > p_options.modify_active_preset:
                        label_text = presets[p_options.modify_active_preset].name
            layout.label(text="Rename Preset: " + label_text)
            layout.prop(p_options, "modify_preset_rename", text="")

    def invoke(self, context, event):
        wm = context.window_manager
        p_options = wm.py_rec.preset_options
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = wm.py_rec.preset_collections
        f = p_options.modify_collection_function
        if f == MODIFY_PRESET_FUNC_RENAME:
            # set initial rename string to original name string, if available
            temp_name = ""
            if len(p_collections) > p_options.modify_active_collection:
                active_coll = p_collections[p_options.modify_active_collection]
                if p_options.modify_base_type in active_coll.base_types:
                    presets = active_coll.base_types[p_options.modify_base_type].presets
                    if len(presets) > p_options.modify_active_preset:
                        temp_name = presets[p_options.modify_active_preset].name
            p_options.modify_preset_rename = temp_name
        return wm.invoke_props_dialog(self)

class PYREC_OT_PresetRemovePreset(Operator):
    bl_idname = "py_rec.preset_remove_preset"
    bl_label = "Remove Preset"
    bl_description = "Permanently delete active Preset"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        p_r = context.window_manager.py_rec
        if p_r.preset_options.lock_changes:
            return False
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        if p_options.modify_active_collection >= len(p_collections):
            return False
        tp = p_collections[p_options.modify_active_collection].base_types
        if p_options.modify_base_type not in tp:
            return False
        return p_options.modify_active_preset < len(tp[p_options.modify_base_type].presets)

    def execute(self, context):
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        preset_collection_remove_preset(p_options, p_collections)
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Permanently delete Preset? Cancel by pressing Esc,")
        layout.label(text="or click outside this window.")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

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
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
