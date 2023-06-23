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

from bpy.types import UIList

from .func import PRESET_SOURCE_ADDON_PREFS

PREFS_ADDONS_NAME = "py_recorder"

class PYREC_UL_PresetClipboardProps(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        clipboard = context.window_manager.py_rec.preset_options.clipboard
        cb_options = context.window_manager.py_rec.preset_options.clipboard_options
        # item type is PYREC_PG_PresetClipboardPropDetail
        ob = item
        sp = layout
        if cb_options.list_show_datapath:
            sp = sp.split(factor=cb_options.list_col_size1)
            sp.label(text=ob.name[9:])
        sp = sp.split(factor=cb_options.list_col_size2)
        sp.prop_search(ob, "base_type", ob, "available_base_types", text="")
        try:
            prop_path = ob.available_base_types[ob.base_type].value
        except:
            prop_path = ""
        sp = sp.split(factor=cb_options.list_col_size3)
        sp.label(text=prop_path)
        # display the property's value
        if ob.value_type == "bool":
            sp.prop(clipboard.bool_props[ob.name], "value", text="")
        elif ob.value_type == "float":
            sp.prop(clipboard.float_props[ob.name], "value", text="", slider=False)
        elif ob.value_type == "int":
            sp.prop(clipboard.int_props[ob.name], "value", text="", slider=False)
        elif ob.value_type == "str":
            sp.prop(clipboard.string_props[ob.name], "value", text="")
        elif ob.value_type == "VectorXYZ":
            sp.prop(clipboard.vector_xyz_props[ob.name], "value", text="", slider=False)

class PYREC_UL_PresetApplyProps(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # item type is PYREC_PG_PresetPropDetail
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        base_types = p_collections[p_options.apply_collection].base_types
        apply_base_type = p_options.apply_base_type
        # remove ': datapath' from apply_base_type
        if apply_base_type.find(":") != -1:
            apply_base_type = apply_base_type[:apply_base_type.find(":")]
        preset = base_types[apply_base_type].presets[p_options.apply_preset]

        sp = layout.split(factor=0.5)
        sp.label(text=item.name)
        # display the property's value
        if item.value_type == "bool":
            sp.prop(preset.bool_props[item.name], "value", text="")
        elif item.value_type == "float":
            sp.prop(preset.float_props[item.name], "value", text="", slider=False)
        elif item.value_type == "int":
            sp.prop(preset.int_props[item.name], "value", text="", slider=False)
        elif item.value_type == "str":
            sp.prop(preset.string_props[item.name], "value", text="")
        elif item.value_type == "VectorXYZ":
            sp.prop(preset.vector_xyz_props[item.name], "value", text="", slider=False)

class PYREC_UL_PresetModifyCollections(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # item type is PYREC_PG_BaseTypePropPresetsCollection
        layout.label(text=item.name)

class PYREC_UL_PresetModifyPresets(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name)

class PYREC_UL_PresetModifyProps(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # item type is PYREC_PG_PresetPropDetail
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        base_types = p_collections[p_options.modify_active_collection].base_types
        preset = base_types[p_options.modify_base_type].presets[p_options.modify_active_preset]

        sp = layout.split(factor=0.5)
        sp.label(text=item.name)
        # display the property's value
        if item.value_type == "bool":
            sp.prop(preset.bool_props[item.name], "value", text="")
        elif item.value_type == "float":
            sp.prop(preset.float_props[item.name], "value", text="", slider=False)
        elif item.value_type == "int":
            sp.prop(preset.int_props[item.name], "value", text="", slider=False)
        elif item.value_type == "str":
            sp.prop(preset.string_props[item.name], "value", text="")
        elif item.value_type == "VectorXYZ":
            sp.prop(preset.vector_xyz_props[item.name], "value", text="", slider=False)
