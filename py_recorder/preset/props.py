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

from bpy.props import (BoolProperty, CollectionProperty, EnumProperty, FloatProperty, FloatVectorProperty,
    IntProperty, PointerProperty, StringProperty)
from bpy.types import PropertyGroup

from .func import (PRESET_SOURCE_TYPES, PRESET_VIEW_TYPES, MODIFY_COLL_FUNC, MODIFY_PRESET_FUNC,
    set_input_full_datapath, get_input_full_datapath, create_base_type_items, set_apply_input_full_datapath,
    get_apply_input_full_datapath, apply_base_type_items, apply_collection_items, apply_preset_items,
    modify_base_type_items)

class PYREC_PG_BoolProp(PropertyGroup):
    name: StringProperty()
    value: BoolProperty()

class PYREC_PG_FloatProp(PropertyGroup):
    name: StringProperty()
    value: FloatProperty()

class PYREC_PG_IntProp(PropertyGroup):
    name: StringProperty()
    value: IntProperty()

class PYREC_PG_StringProp(PropertyGroup):
    name: StringProperty()
    value: StringProperty()

# https://docs.blender.org/api/current/bpy.props.html
# https://blender.stackexchange.com/questions/143072/how-to-make-multiple-float-property-in-python
# my_float_vector: FloatVectorProperty(
#         name = "Float Vector Value",
#         description="Something",
#         default=(0.0, 0.0, 0.0),
#         min= 0.0,
#         max = 0.1,
#         subtype = 'XYZ'
#         # 'COLOR', 'TRANSLATION', 'DIRECTION', 'VELOCITY',
#         # 'ACCELERATION', 'MATRIX', 'EULER', 'QUATERNION',
#         # 'AXISANGLE', 'XYZ', 'COLOR_GAMMA', 'LAYER'
#         )
#
# do more research, re: subtype
class PYREC_PG_VectorXYZ_Prop(PropertyGroup):
    name: StringProperty()
    value: FloatVectorProperty(subtype='XYZ')

class PYREC_PG_PresetClipboardPropDetail(PropertyGroup):
    # name is full datapath
    name: StringProperty()
    base_type: StringProperty()
    available_base_types: CollectionProperty(type=PYREC_PG_StringProp)
    value_type: StringProperty()

class PYREC_PG_PresetClipboard(PropertyGroup):
    # list
    prop_details: CollectionProperty(type=PYREC_PG_PresetClipboardPropDetail)
    # the following properties are indexed by prop_details[].name
    bool_props: CollectionProperty(type=PYREC_PG_BoolProp)
    int_props: CollectionProperty(type=PYREC_PG_IntProp)
    float_props: CollectionProperty(type=PYREC_PG_FloatProp)
    string_props: CollectionProperty(type=PYREC_PG_StringProp)
    vector_xyz_props: CollectionProperty(type=PYREC_PG_VectorXYZ_Prop)

class PYREC_PG_PresetClipboardOptions(PropertyGroup):
    # copy/paste input box
    input_full_datapath: StringProperty(name="Data Path", set=set_input_full_datapath, get=get_input_full_datapath,
        description="Full Data Path for preset. 'Copy Full Data Path', in right-click menu of a property, and " \
        "paste here. e.g. right-click on Object's Location values to see menu with 'Copy Full Data Path'",
        default="bpy.data.objects[0].location")
    # list options
    list_show_datapath: BoolProperty(name="Show Datapath", description="Show copied full datapath in Property " \
        "Clipboard list", default=False)
    # list column sizes (factors)
    list_col_size1: FloatProperty(default=0.2, min=0.1, max=0.9)
    list_col_size2: FloatProperty(default=0.4, min=0.1, max=0.9)
    list_col_size3: FloatProperty(default=0.4, min=0.1, max=0.9)
    active_prop_detail: IntProperty()
    # selected base_type for creating new preset
    create_base_type: EnumProperty(name="Base Type", description="Base Type for new Preset, when 'Create Preset' " \
        "button is used", items=create_base_type_items)
    create_preset_name: StringProperty(name="Preset", description="Name to give to new preset", default="Preset")
    create_preset_name_search: BoolProperty(name="Preset Name Search", description="Enable display of existing " \
        "Presets. Turn this off if text box ignores name changes", default=False)
    create_preset_coll_name: StringProperty(name="Preset Collection", description="Preset Collection for new " \
        "Preset. If empty then new Preset Collection will be created", default="Collection")
    create_preset_coll_name_search: BoolProperty(name="Collection Name Search", description="Enable display of " \
        "existing Presets. Turn this off if text box ignores name changes", default=False)

class PYREC_PG_PresetPropDetail(PropertyGroup):
    # name is property path (relative to base type)
    name: StringProperty()
    # value_type is used to determine which props type collection will be used (e.g. bool_props)
    value_type: StringProperty()

# lists of preset property values, for a single Blender Python 'type'/'sub-type'
# e.g. type 'ParticleSettings' and sub-type EffectorWeights, such as:
#      'bpy.data.particles["ParticleSettings"].effector_weights'
# both can be included in a single preset, because prop names can include '.' symbol to use Python sub-attributes
class PYREC_PG_Preset(PropertyGroup):
    prop_details: CollectionProperty(type=PYREC_PG_PresetPropDetail)

    # 'name' of each item in collection is Python attribute name, so preset value can be linked with 'name' lookup
    bool_props: CollectionProperty(type=PYREC_PG_BoolProp)
    int_props: CollectionProperty(type=PYREC_PG_IntProp)
    float_props: CollectionProperty(type=PYREC_PG_FloatProp)
    string_props: CollectionProperty(type=PYREC_PG_StringProp)
    vector_xyz_props: CollectionProperty(type=PYREC_PG_VectorXYZ_Prop)

# a collection of presets that apply to only one base type, base type is 'name' of this item in parent collection,
# e.g. base type 'bpy.types.Object'
class PYREC_PG_PresetCollection(PropertyGroup):
    presets: CollectionProperty(type=PYREC_PG_Preset)

# a collection of presets, ordered in lists by Blender Python 'type'
class PYREC_PG_PresetTypeCollection(PropertyGroup):
#    parent_collection: StringProperty()
    # 'name' of each item in this collection is Blender Python type name
    base_types: CollectionProperty(type=PYREC_PG_PresetCollection)

class PYREC_PG_PresetOptions(PropertyGroup):
    data_source: EnumProperty(name="Data Source", description="Presets and Preset Collections Data will be saved " \
        "in selected location. Changes to Presets and Preset Collections will only be applied to saved data in " \
        "this location", items=PRESET_SOURCE_TYPES)
    view_type: EnumProperty(name="View", items=PRESET_VIEW_TYPES)

    clipboard: PointerProperty(type=PYREC_PG_PresetClipboard)
    clipboard_options: PointerProperty(type=PYREC_PG_PresetClipboardOptions)

    # copy/paste input box
    apply_input_full_datapath: StringProperty(name="Data Path", set=set_apply_input_full_datapath,
        get=get_apply_input_full_datapath, description="Full Data Path for preset type list. 'Copy Full Data " +
        "Path', in right-click menu of a property, and paste here. e.g. right-click on Object's Location values " +
        "to see menu with 'Copy Full Data Path'", default="bpy.data.objects[0].location")
    apply_available_types: CollectionProperty(type=PropertyGroup)
    apply_base_type: EnumProperty(items=apply_base_type_items)
    apply_collection: EnumProperty(items=apply_collection_items)
    apply_preset: EnumProperty(items=apply_preset_items)
    apply_detail: IntProperty()

    modify_active_collection: IntProperty()
    modify_base_type: EnumProperty(items=modify_base_type_items)
    modify_active_preset: IntProperty()
    modify_detail: IntProperty()
    modify_collection_function: EnumProperty(items=MODIFY_COLL_FUNC)
    modify_collection_rename: StringProperty()
    modify_preset_function: EnumProperty(items=MODIFY_PRESET_FUNC)
    modify_preset_rename: StringProperty()
