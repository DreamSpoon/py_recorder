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

from .func import (get_source_preset_collections, get_modify_active_single_preset)

def draw_prop_value(layout, value_type_base, prop_base, lock_changes):
    if lock_changes:
        # display the property's value
        if value_type_base.value_type == "bool":
            layout.label(text=str(prop_base.bool_props[value_type_base.name].value))
        elif value_type_base.value_type == "Euler":
            v = prop_base.euler_props[value_type_base.name].value
            order = prop_base.euler_props[value_type_base.name].order
            layout.label(text="((%f, %f, %f), '%s')" % (v[0], v[1], v[2], order))
        elif value_type_base.value_type == "float":
            layout.label(text=str(prop_base.float_props[value_type_base.name].value))
        elif value_type_base.value_type == "int":
            layout.label(text=str(prop_base.int_props[value_type_base.name].value))
        elif value_type_base.value_type == "str":
            layout.label(text=str(prop_base.string_props[value_type_base.name].value))
        elif value_type_base.value_type == "FloatVector3":
            v = prop_base.float_vector3_props[value_type_base.name].value
            layout.label(text="(%f, %f, %f)" % (v[0], v[1], v[2]) )
        elif value_type_base.value_type == "FloatVector4":
            v = prop_base.float_vector4_props[value_type_base.name].value
            layout.label(text="(%f, %f, %f, %f)" % (v[0], v[1], v[2], v[3]) )
        elif value_type_base.value_type == "Layer20":
            v = prop_base.layer20_props[value_type_base.name].value
            layout.label(text="(%s)" % str(v) )
        elif value_type_base.value_type == "Layer32":
            v = prop_base.layer32_props[value_type_base.name].value
            layout.label(text="(%s)" % str(v) )
    else:
        # display the property's value
        if value_type_base.value_type == "bool":
            layout.prop(prop_base.bool_props[value_type_base.name], "value", text="")
        elif value_type_base.value_type == "Euler":
            col = layout.column(align=True)
            col.prop(prop_base.euler_props[value_type_base.name], "value", text="", slider=False)
            col.prop(prop_base.euler_props[value_type_base.name], "order", text="", slider=False)
        elif value_type_base.value_type == "float":
            layout.prop(prop_base.float_props[value_type_base.name], "value", text="", slider=False)
        elif value_type_base.value_type == "int":
            layout.prop(prop_base.int_props[value_type_base.name], "value", text="", slider=False)
        elif value_type_base.value_type == "str":
            layout.prop(prop_base.string_props[value_type_base.name], "value", text="")
        elif value_type_base.value_type == "FloatVector3":
            layout.prop(prop_base.float_vector3_props[value_type_base.name], "value", text="", slider=False)
        elif value_type_base.value_type == "FloatVector4":
            layout.prop(prop_base.float_vector4_props[value_type_base.name], "value", text="", slider=False)
        elif value_type_base.value_type == "Layer20":
            layout.prop(prop_base.layer20_props[value_type_base.name], "value", text="")
        elif value_type_base.value_type == "Layer32":
            layout.prop(prop_base.layer32_props[value_type_base.name], "value", text="")

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
        p_options = context.window_manager.py_rec.preset_options
        p_collections = get_source_preset_collections(context)
        base_types = p_collections[p_options.apply_options.collection].base_types
        apply_base_type = p_options.apply_options.base_type
        # remove ': datapath' from apply_base_type
        if apply_base_type.find(":") != -1:
            apply_base_type = apply_base_type[:apply_base_type.find(":")]
        preset = base_types[apply_base_type].presets[p_options.apply_options.preset]
        # draw row
        sp = layout.split(factor=p_options.clipboard_options.list_col_size3)
        sp.label(text=item.name)
        draw_prop_value(sp, item, preset, p_options.lock_changes)

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
        preset_options = context.window_manager.py_rec.preset_options
        sp = layout.split(factor=preset_options.clipboard_options.list_col_size3)
        sp.label(text=item.name)
        preset = get_modify_active_single_preset(preset_options, get_source_preset_collections(context))
        if preset is None:
            return
        draw_prop_value(sp, item, preset, preset_options.lock_changes)
