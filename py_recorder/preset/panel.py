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

from bpy.types import Panel

from .func import (PRESET_SOURCE_ADDON_PREFS, PRESET_VIEW_APPLY, PRESET_VIEW_MODIFY,
    PRESET_VIEW_CLIPBOARD, PRESET_VIEW_IMPORT_EXPORT, get_source_preset_collections)
from .operator import (PYREC_OT_PresetClipboardCreatePreset, PYREC_OT_PresetClipboardRemoveItem,
    PYREC_OT_PresetClipboardClear, PYREC_OT_PresetApply, PYREC_OT_PresetModifyCollection,
    PYREC_OT_PresetRemovePreset, PYREC_OT_PresetRemoveCollection, PYREC_OT_PresetModifyPreset,
    PYREC_OT_PresetPropsRemoveItem, PYREC_OT_QuicksavePreferences, PYREC_OT_PresetImportFile,
    PYREC_OT_PresetExportFile, PYREC_OT_PresetExportObject, PYREC_OT_PresetImportObject,
    PYREC_OT_TransferObjectPresets, PYREC_OT_TextToPresetClipboard)

class PresetBaseClass(Panel):
    def draw_func_apply(self, context, p_r):
        layout = self.layout
        p_options = p_r.preset_options
        p_collections = get_source_preset_collections(context)
        layout.operator(PYREC_OT_PresetApply.bl_idname)
        layout.prop(p_options.apply_options, "full_datapath")
        layout.prop(p_options.apply_options, "base_type", text="Type")
        layout.prop(p_options.apply_options, "collection", text="Collection")
        layout.prop(p_options.apply_options, "preset", text="Preset")

        layout.separator()
        apply_coll_name = p_options.apply_options.collection
        apply_type_name = p_options.apply_options.base_type
        # remove ': datapath' from apply_type_name
        if apply_type_name.find(":") != -1:
            apply_type_name = apply_type_name[:apply_type_name.find(":")]
        apply_preset_name = p_options.apply_options.preset
        named_prop_preset = None
        if apply_coll_name in p_collections:
            base_types = p_collections[apply_coll_name].base_types
            if apply_type_name in base_types:
                presets = base_types[apply_type_name].presets
                if apply_preset_name in presets:
                    named_prop_preset = presets[apply_preset_name]
        layout.prop(p_options.clipboard_options, "list_col_size3", slider=True, text="Prop")
        if named_prop_preset is None:
            layout.box().label(text="")
        else:
            layout.template_list("PYREC_UL_PresetApplyProps", "", named_prop_preset, "prop_details",
                                 p_options.apply_options, "detail")

    def draw_func_modify(self, context, p_r):
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            base_pkg_name = __package__ if __package__.find(".") == -1 else __package__[:__package__.find(".")]
            data_source = context.preferences.addons[base_pkg_name].preferences
        else:
            data_source = p_r
        p_collections = data_source.preset_collections
        layout = self.layout

        row = layout.row()
        row.prop(p_r.preset_options.modify_options, "collection_function", text="")
        row.operator(PYREC_OT_PresetModifyCollection.bl_idname)

        row = layout.row()
        row.template_list("PYREC_UL_PresetModifyCollections", "", data_source, "preset_collections",
                          p_options.modify_options, "active_collection", rows=3)
        row.operator(PYREC_OT_PresetRemoveCollection.bl_idname, text="", icon='REMOVE')

        layout.separator()
        layout.prop(p_options.modify_options, "base_type", text="Type")
        layout.separator()

        row = layout.row()
        row.prop(p_r.preset_options.modify_options, "preset_function", text="")
        row.operator(PYREC_OT_PresetModifyPreset.bl_idname)
        layout.separator()

        row = layout.row()
        if p_options.modify_options.active_collection < len(p_collections):
            tp = p_collections[p_options.modify_options.active_collection].base_types
            if p_options.modify_options.base_type in tp:
                row.template_list("PYREC_UL_PresetModifyPresets", "", tp[p_options.modify_options.base_type],
                                  "presets", p_options.modify_options, "active_preset", rows=3)
            else:
                row.box().label(text="")
        else:
            row.box().label(text="")
        row.operator(PYREC_OT_PresetRemovePreset.bl_idname, text="", icon='REMOVE')

        layout.separator()
        layout.prop(p_options.clipboard_options, "list_col_size3", slider=True, text="Prop")
        row = layout.row()
        preset_coll_index = p_options.modify_options.active_collection
        preset_type_name = p_options.modify_options.base_type
        preset_index = p_options.modify_options.active_preset
        named_prop_preset = None
        if preset_coll_index < len(p_collections):
            base_types = p_collections[preset_coll_index].base_types
            if preset_type_name in base_types:
                presets = base_types[preset_type_name].presets
                if preset_index < len(presets):
                    named_prop_preset = presets[preset_index]
        if named_prop_preset is None:
            row.box().label(text="")
        else:
            row.template_list("PYREC_UL_PresetModifyProps", "", named_prop_preset, "prop_details",
                              p_options.modify_options, "active_detail", rows=3)
        function_col = row.column()
        function_col.operator(PYREC_OT_PresetPropsRemoveItem.bl_idname, text="", icon='REMOVE')

    # draw Preset Clipboard
    def draw_func_clipboard(self, context, p_r):
        clipboard = p_r.preset_options.clipboard
        cb_options = p_r.preset_options.clipboard_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_r.preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            base_pkg_name = __package__ if __package__.find(".") == -1 else __package__[:__package__.find(".")]
            data_source = context.preferences.addons[base_pkg_name].preferences
        else:
            data_source = p_r
        layout = self.layout

        row = layout.row()
        row.label(text="", icon='RNA')
        row.prop(cb_options, "input_full_datapath", text="")
        if context.space_data.type == 'TEXT_EDITOR':
            layout.operator(PYREC_OT_TextToPresetClipboard.bl_idname)

        layout.label(text="  New Preset")
        row = layout.row()
        if cb_options.create_preset_coll_name_search:
            row.prop_search(cb_options, "create_preset_coll_name", data_source, "preset_collections",
                text="Collection", results_are_suggestions=True)
        else:
            row.prop(cb_options, "create_preset_coll_name", text="Collection")
        row.prop(cb_options, "create_preset_coll_name_search", icon='VIEWZOOM', text="", toggle=True)
        layout.prop(cb_options, "create_base_type", text="Type")
        row = layout.row()

        coll_name = cb_options.create_preset_coll_name
        p_collections = data_source.preset_collections
        bt = cb_options.create_base_type
        name_search = cb_options.create_preset_name_search
        if name_search  and coll_name in p_collections and bt in p_collections[coll_name].base_types:
            row.prop_search(cb_options, "create_preset_name", p_collections[coll_name].base_types[bt], "presets",
                text="Name", results_are_suggestions=True)
        else:
            row.prop(cb_options, "create_preset_name", text="Name")
        row.prop(cb_options, "create_preset_name_search", icon='VIEWZOOM', text="", toggle=True)

        layout.operator(PYREC_OT_PresetClipboardCreatePreset.bl_idname)
        layout.separator()

        # column size (factor) sliders
        row = layout.row(align=True)
        if cb_options.list_show_datapath:
            row.prop(cb_options, "list_col_size1", slider=True, text="Full")
        row.prop(cb_options, "list_col_size2", slider=True, text="Type")
        row.prop(cb_options, "list_col_size3", slider=True, text="Prop")

        # container row
        cont_row = layout.row(align=True)

        # attribute list column
        attr_list_col = cont_row.column()

        # list labels
        sp = attr_list_col
        if cb_options.list_show_datapath:
            sp = sp.split(factor=cb_options.list_col_size1)
            sp.label(text="Full")
        sp = sp.split(factor=cb_options.list_col_size2)
        sp.label(text="Type")
        sp = sp.split(factor=cb_options.list_col_size3)
        sp.label(text="Prop")
        sp.label(text="Value")
        # list
        attr_list_col.template_list("PYREC_UL_PresetClipboardProps", "", clipboard, "prop_details", cb_options,
                                    "active_prop_detail")
        # functions column
        function_col = cont_row.column()
        function_col.separator(factor=4)
        function_col.operator(PYREC_OT_PresetClipboardRemoveItem.bl_idname, text="", icon='REMOVE')
        function_col.separator(factor=2)
        function_col.prop(cb_options, "list_show_datapath", text="", icon='RNA', toggle=True)

        path_text = ""
        try:
            path_text += " " + clipboard.prop_details[cb_options.active_prop_detail].name[9:]
        except:
            pass
        layout.label(text=path_text)

        layout.operator(PYREC_OT_PresetClipboardClear.bl_idname)

    def draw_func_import_export(self):
        layout = self.layout
        layout.label(text="File")
        layout.operator(PYREC_OT_PresetImportFile.bl_idname)
        layout.operator(PYREC_OT_PresetExportFile.bl_idname)
        layout.label(text="Object")
        layout.operator(PYREC_OT_PresetImportObject.bl_idname)
        layout.operator(PYREC_OT_PresetExportObject.bl_idname)
        layout.operator(PYREC_OT_TransferObjectPresets.bl_idname)

    def draw(self, context):
        p_r = context.window_manager.py_rec
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.prop(p_r.preset_options, "data_source", text="Save to")
        if p_r.preset_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            row.operator(PYREC_OT_QuicksavePreferences.bl_idname, text="", icon="DOCUMENTS")
        box.prop(p_r.preset_options, "lock_changes")
        box.prop(p_r.preset_options, "view_type")
        layout.separator()
        pf = p_r.preset_options.view_type
        if pf == PRESET_VIEW_APPLY:
            self.draw_func_apply(context, p_r)
        elif pf == PRESET_VIEW_MODIFY:
            self.draw_func_modify(context, p_r)
        elif pf == PRESET_VIEW_CLIPBOARD:
            self.draw_func_clipboard(context, p_r)
        elif pf == PRESET_VIEW_IMPORT_EXPORT:
            self.draw_func_import_export()

class PYREC_PT_View3dPreset(PresetBaseClass):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Py Preset"
    bl_options = {'DEFAULT_CLOSED'}

class PYREC_PT_TextEditorPreset(PresetBaseClass):
    bl_label = "Py Preset"
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_options = {'DEFAULT_CLOSED'}
