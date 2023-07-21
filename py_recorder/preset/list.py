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

def draw_prop_value(layout, value_type_base, prop_base, lock_changes):
    if lock_changes:
        # display the property's value
        if value_type_base.value_type == "bool":
            layout.label(text=str(prop_base.bool_props[value_type_base.name].value))
        elif value_type_base.value_type == "float":
            layout.label(text=str(prop_base.float_props[value_type_base.name].value))
        elif value_type_base.value_type == "int":
            layout.label(text=str(prop_base.int_props[value_type_base.name].value))
        elif value_type_base.value_type == "str":
            layout.label(text=str(prop_base.string_props[value_type_base.name].value))
        elif value_type_base.value_type == "VectorXYZ":
            v = prop_base.vector_xyz_props[value_type_base.name].value
            layout.label(text="(%f, %f, %f)" % (v[0], v[1], v[2]))
    else:
        # display the property's value
        if value_type_base.value_type == "bool":
            layout.prop(prop_base.bool_props[value_type_base.name], "value", text="")
        elif value_type_base.value_type == "float":
            layout.prop(prop_base.float_props[value_type_base.name], "value", text="", slider=False)
        elif value_type_base.value_type == "int":
            layout.prop(prop_base.int_props[value_type_base.name], "value", text="", slider=False)
        elif value_type_base.value_type == "str":
            layout.prop(prop_base.string_props[value_type_base.name], "value", text="")
        elif value_type_base.value_type == "VectorXYZ":
            layout.prop(prop_base.vector_xyz_props[value_type_base.name], "value", text="", slider=False)

class PYREC_UL_PresetClipboardProps(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        p_r = context.window_manager.py_rec
        clipboard = p_r.preset_options.clipboard
        cb_options = p_r.preset_options.clipboard_options
        # item type is PYREC_PG_PresetClipboardPropDetail
        ob = item
        sp = layout
        if cb_options.list_show_datapath:
            sp = sp.split(factor=cb_options.list_col_size1)
            if ob.name.startswith("bpy.data."):
                sp.label(text=ob.name[9:])
            else:
                sp.label(text=ob.name)
        sp = sp.split(factor=cb_options.list_col_size2)
        sp.prop_search(ob, "base_type", ob, "available_base_types", text="")
        try:
            prop_path = ob.available_base_types[ob.base_type].value
        except:
            prop_path = ""
        sp = sp.split(factor=cb_options.list_col_size3)
        sp.label(text=prop_path)
        draw_prop_value(sp, ob, clipboard, p_r.preset_options.lock_changes)

class PYREC_UL_PresetApplyProps(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        # item type is PYREC_PG_PresetPropDetail
        p_r = context.window_manager.py_rec
        p_options = p_r.preset_options
        cb_options = p_options.clipboard_options
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

        sp = layout.split(factor=cb_options.list_col_size3)
        sp.label(text=item.name)
        draw_prop_value(sp, item, preset, p_r.preset_options.lock_changes)

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
        cb_options = p_options.clipboard_options
        # use Blender Addon Preferences or .blend file as Preset save data source
        if p_options.data_source == PRESET_SOURCE_ADDON_PREFS:
            p_collections = context.preferences.addons[PREFS_ADDONS_NAME].preferences.preset_collections
        else:
            p_collections = p_r.preset_collections
        base_types = p_collections[p_options.modify_active_collection].base_types
        preset = base_types[p_options.modify_base_type].presets[p_options.modify_active_preset]

        sp = layout.split(factor=cb_options.list_col_size3)
        sp.label(text=item.name)
        draw_prop_value(sp, item, preset, p_r.preset_options.lock_changes)
