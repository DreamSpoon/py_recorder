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

bl_info = {
    "name": "Python Recorder",
    "version": (0, 5, 3),
    "author": "Dave",
    "blender": (2, 80, 0),
    "description": "Create and apply Presets. Inspect Python object attributes. Record Blender data to Python code",
    "location": "3DView -> Tools -> Tool -> Py Record Info, Py Exec Object. Right-click Context menu -> " \
        "Add Inspect Panel. Context -> Tool -> Py Inspect",
    "doc_url": "https://github.com/DreamSpoon/py_recorder#readme",
    "category": "Presets, Python",
}

import bpy
from bpy.app.handlers import persistent
from bpy.types import (Panel, PropertyGroup)
from bpy.props import (BoolProperty, CollectionProperty, PointerProperty, StringProperty)
from bpy.utils import (register_class, unregister_class)

from .inspect.inspect_panel import (PYREC_PG_AttributeRecordOptions, PYREC_PG_InspectPanelCollection,
    PYREC_OT_AddInspectPanel, PYREC_OT_RemoveInspectPanel, PYREC_OT_InspectOptions,
    PYREC_OT_InspectPanelAttrZoomIn, PYREC_OT_InspectPanelAttrZoomOut, PYREC_OT_InspectPanelArrayIndexZoomIn,
    PYREC_OT_InspectPanelArrayKeyZoomIn, PYREC_OT_RestoreInspectContextPanels, PYREC_OT_InspectRecordAttribute,
    PYREC_OT_InspectCopyAttribute, PYREC_OT_InspectPasteAttribute, PYREC_OT_InspectChoosePy, PYREC_PG_DirAttributeItem,
    PYREC_PG_InspectPanelOptions, PYREC_PG_InspectPanel, PYREC_MT_InspectActive, PYREC_OT_PyInspectActiveObject,
    draw_inspect_panel, append_inspect_context_menu_all, remove_inspect_context_menu_all,
    append_inspect_active_context_menu_all, remove_inspect_active_context_menu_all)
from .inspect.inspect_exec import (register_inspect_exec_panel_draw_func, unregister_all_inspect_panel_classes)
from .object_custom_prop import (CPROP_NAME_INIT_PY, PYREC_OT_OBJ_AddCP_Data, PYREC_OT_OBJ_ModifyInit)
from .exec_object import (PYREC_OT_BatchExecObject, PYREC_OT_ExecObject, PYREC_PT_VIEW3D_ExecObject)
from .record.driver_ops import (PYREC_PG_DriverRecordOptions, PYREC_OT_DriversToPython, PYREC_PT_RecordDriver,
    PYREC_OT_SelectAnimdataSrcAll, PYREC_OT_SelectAnimdataSrcNone)
from .record.node_tree_ops import (PYREC_OT_RecordNodetree, PYREC_PT_RecordNodetree, PYREC_PG_NodetreeRecordOptions)
from .record.info_ops import (PYREC_OT_VIEW3D_CopyInfoToObjectText, PYREC_OT_VIEW3D_StartRecordInfoLine,
    PYREC_OT_VIEW3D_StopRecordInfoLine, PYREC_PG_InfoRecordOptions, PYREC_PT_VIEW3D_RecordInfo, get_datablock_for_type)
from .exec_panel import (PYREC_PG_ExecOptions, PYREC_OT_ContextExec, append_exec_context_panel_all,
    remove_exec_context_panel_all)
from .preset.preset_ui import (PYREC_OT_PresetClipboardClear, PYREC_OT_PresetClipboardRemoveItem,
    PYREC_OT_PresetClipboardCreatePreset, PYREC_UL_PresetClipboardProps,
    PYREC_UL_PresetApplyProps, PYREC_UL_PresetModifyProps, PYREC_UL_PresetModifyCollections,
    PYREC_UL_PresetModifyPresets, PYREC_OT_PresetPropsRemoveItem, PYREC_OT_PresetApply,
    PYREC_OT_PresetModifyCollection, PYREC_OT_PresetRemoveCollection, PYREC_OT_PresetModifyPreset,
    PYREC_OT_PresetRemovePreset, PYREC_OT_QuicksavePreferences, PYREC_PT_Preset)
from .preset.preset_prop import (PYREC_PG_BoolProp, PYREC_PG_IntProp, PYREC_PG_FloatProp, PYREC_PG_VectorXYZ_Prop,
    PYREC_PG_StringProp, PYREC_PG_PresetPropDetail, PYREC_PG_Preset, PYREC_PG_PresetCollection,
    PYREC_PG_PresetTypeCollection, PYREC_PG_PresetClipboardPropDetail, PYREC_PG_PresetClipboard,
    PYREC_PG_PresetClipboardOptions, PYREC_PG_PresetOptions)
from .addon_prefs import (PYREC_PG_LogAddonPrefs, PYREC_PG_InterfaceAddonPrefs, PYREC_AddonPreferences)

class PYREC_PT_OBJ_AdjustCustomProp(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = "Py Exec Custom Properties"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def draw(self, context):
        py_rec_record_options_info = context.window_manager.py_rec.record_options.info
        layout = self.layout
        act_ob = context.active_object

        layout.label(text="Init")
        box = layout.box()
        if act_ob.get(CPROP_NAME_INIT_PY) is None:
            box.label(text=CPROP_NAME_INIT_PY+":  None")
        else:
            box.prop_search(act_ob, '["'+CPROP_NAME_INIT_PY+'"]', bpy.data,
                            get_datablock_for_type(act_ob[CPROP_NAME_INIT_PY]))
        box.operator(PYREC_OT_OBJ_ModifyInit.bl_idname)

        layout.label(text="New Property")
        box = layout.box()
        box.prop(py_rec_record_options_info, "add_cp_data_name")
        box.prop(py_rec_record_options_info, "add_cp_data_type")
        box.prop_search(py_rec_record_options_info, "add_cp_datablock", bpy.data,
                        py_rec_record_options_info.add_cp_data_type, text="")
        box.operator(PYREC_OT_OBJ_AddCP_Data.bl_idname)

class PYREC_PG_LogOptions(PropertyGroup):
    output_text_name: StringProperty(name="Log Text Name", description="Name of Textblock that receives log entries " \
        "(see builtin Text-Editor)", default="py_rec_log")
    enable_timestamp: BoolProperty(name="Timestamp", description="If enabled then log entries include time and date " \
        "at beginning of each entry", default=True)

class PYREC_PG_RecordOptions(PropertyGroup):
    attribute: PointerProperty(type=PYREC_PG_AttributeRecordOptions)
    driver: PointerProperty(type=PYREC_PG_DriverRecordOptions)
    info: PointerProperty(type=PYREC_PG_InfoRecordOptions)
    nodetree: PointerProperty(type=PYREC_PG_NodetreeRecordOptions)

class PYREC_PG_PyRec(PropertyGroup):
    log_options: PointerProperty(type=PYREC_PG_LogOptions)
    record_options: PointerProperty(type=PYREC_PG_RecordOptions)
    exec_options: PointerProperty(type=PYREC_PG_ExecOptions)
    preset_options: PointerProperty(type=PYREC_PG_PresetOptions)
    preset_collections: CollectionProperty(type=PYREC_PG_PresetTypeCollection)
    inspect_context_collections: CollectionProperty(type=PYREC_PG_InspectPanelCollection)

classes = [
    PYREC_OT_RecordNodetree,
    PYREC_PT_RecordNodetree,
    PYREC_OT_OBJ_ModifyInit,
    PYREC_OT_OBJ_AddCP_Data,
    PYREC_PT_OBJ_AdjustCustomProp,
    PYREC_OT_VIEW3D_StartRecordInfoLine,
    PYREC_OT_VIEW3D_StopRecordInfoLine,
    PYREC_OT_VIEW3D_CopyInfoToObjectText,
    PYREC_PT_VIEW3D_RecordInfo,
    PYREC_OT_BatchExecObject,
    PYREC_OT_ExecObject,
    PYREC_PT_VIEW3D_ExecObject,
    PYREC_OT_AddInspectPanel,
    PYREC_MT_InspectActive,
    PYREC_OT_PyInspectActiveObject,
    PYREC_OT_RemoveInspectPanel,
    PYREC_OT_InspectOptions,
    PYREC_OT_InspectPanelAttrZoomIn,
    PYREC_OT_InspectPanelAttrZoomOut,
    PYREC_OT_InspectPanelArrayIndexZoomIn,
    PYREC_OT_InspectPanelArrayKeyZoomIn,
    PYREC_OT_DriversToPython,
    PYREC_OT_SelectAnimdataSrcAll,
    PYREC_OT_SelectAnimdataSrcNone,
    PYREC_OT_RestoreInspectContextPanels,
    PYREC_OT_InspectRecordAttribute,
    PYREC_OT_InspectCopyAttribute,
    PYREC_OT_InspectPasteAttribute,
    PYREC_OT_InspectChoosePy,
    PYREC_OT_ContextExec,
    PYREC_PT_RecordDriver,
    PYREC_PG_DirAttributeItem,
    PYREC_PG_InspectPanelOptions,
    PYREC_PG_InspectPanel,
    PYREC_PG_InspectPanelCollection,
    PYREC_PG_AttributeRecordOptions,
    PYREC_PG_DriverRecordOptions,
    PYREC_PG_InfoRecordOptions,
    PYREC_PG_NodetreeRecordOptions,
    PYREC_PG_LogOptions,
    PYREC_PG_RecordOptions,
    PYREC_PG_ExecOptions,

    PYREC_UL_PresetClipboardProps,
    PYREC_UL_PresetApplyProps,
    PYREC_UL_PresetModifyProps,
    PYREC_UL_PresetModifyCollections,
    PYREC_UL_PresetModifyPresets,
    PYREC_OT_PresetPropsRemoveItem,
    PYREC_OT_PresetApply,
    PYREC_OT_PresetModifyCollection,
    PYREC_OT_PresetRemoveCollection,
    PYREC_OT_PresetModifyPreset,
    PYREC_OT_PresetRemovePreset,
    PYREC_OT_QuicksavePreferences,
    PYREC_PT_Preset,

    PYREC_PG_BoolProp,
    PYREC_PG_IntProp,
    PYREC_PG_FloatProp,
    PYREC_PG_VectorXYZ_Prop,
    PYREC_PG_StringProp,
    PYREC_PG_PresetPropDetail,
    PYREC_PG_Preset,
    PYREC_PG_PresetCollection,
    PYREC_PG_PresetTypeCollection,
    PYREC_OT_PresetClipboardClear,
    PYREC_OT_PresetClipboardRemoveItem,
    PYREC_OT_PresetClipboardCreatePreset,
    PYREC_PG_PresetClipboardPropDetail,
    PYREC_PG_PresetClipboard,
    PYREC_PG_PresetClipboardOptions,
    PYREC_PG_PresetOptions,

    PYREC_PG_PyRec,
    PYREC_PG_LogAddonPrefs,
    PYREC_PG_InterfaceAddonPrefs,
    PYREC_AddonPreferences,
]

def duplicate_prop(to_prop, from_prop):
    if isinstance(from_prop, PropertyGroup):
        for attr_name in dir(from_prop):
            attr_value = getattr(from_prop, attr_name)
            if attr_name in [ "bl_rna", "rna_type", "id_data" ] or callable(attr_value) or attr_name.startswith("__"):
                continue
            if isinstance(attr_value, PropertyGroup) or \
                (hasattr(attr_value, "__len__") and not isinstance(attr_value, str)):
                duplicate_prop(getattr(to_prop, attr_name), attr_value)
            else:
                setattr(to_prop, attr_name, attr_value)
    elif hasattr(from_prop, "__len__"):
        if hasattr(to_prop, "clear") and callable(getattr(to_prop, "clear")):
            to_prop.clear()
        for index, from_item in enumerate(from_prop):
            if hasattr(to_prop, "clear") and callable(getattr(to_prop, "clear")):
                to_item = to_prop.add()
                to_item.name = from_item.name
            if isinstance(from_item, PropertyGroup) or \
                (hasattr(from_item, "__len__") and not isinstance(from_item, str)):
                duplicate_prop(to_item, from_item)
            else:
                to_prop[index] = from_item

def load_py_rec_from_scene():
    # copy to WindowManager (singleton, only one) from first Scene (one or more, never zero)
    duplicate_prop(bpy.data.window_managers[0].py_rec, bpy.data.scenes[0].py_rec)

def save_py_rec_to_scene():
    # copy to first Scene (one or more, never zero) from WindowManager (singleton, only one)
    duplicate_prop(bpy.data.scenes[0].py_rec, bpy.data.window_managers[0].py_rec)

@persistent
def load_post_handler_func(dummy):
    # restore state of py_rec before restoring context panels, because restore requires data from py_rec
    load_py_rec_from_scene()
    # register Py Inspect panel UI classes, using data from (now) loaded .blend file
    bpy.ops.py_rec.restore_inspect_context_panels()

@persistent
def save_pre_handler_func(dummy):
    # save state of py_rec before saving .blend file, so Py Inspect panel info is saved
    save_py_rec_to_scene()

# context exec panels must be registered after addon is registered, so a timer is used with call to this function,
# a short time after a file is loaded
def timed_reg_exec():
    addon_prefs = bpy.context.preferences.addons[__name__].preferences
    if addon_prefs.interface.draw_context_exec:
        append_exec_context_panel_all()

def register():
    register_inspect_exec_panel_draw_func(draw_inspect_panel)
    for cls in classes:
        register_class(cls)
    # Scene property is used so py_rec state is saved with .blend file data, because WindowManager properties are not
    # saved with .blend file.
    bpy.types.Scene.py_rec = PointerProperty(type=PYREC_PG_PyRec)
    # WindowManager property is used so the same Py Inspect panel properties are available across all Scenes in loaded
    # .blend file. Creating new Scenes, and switching active Scenes, causes difficulties linking data for Py Inspect
    # panels with UI classes for Py Inspect panels - because UI classes (Py Inspect panels) are the same across all
    # Scenes, but py_rec properties data is different for each Scene.
    bpy.types.WindowManager.py_rec = PointerProperty(type=PYREC_PG_PyRec)
    if not load_post_handler_func in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_post_handler_func)
    if not save_pre_handler_func in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(save_pre_handler_func)
    # append 'Add Inspect Panel' button to all Context menus (all Context types)
    append_inspect_context_menu_all()
    append_inspect_active_context_menu_all()
    # set a timer, so bpy.context can be accessed, to register 'context exec' panels, because 'context exec' panels
    # can be disabled in AddonPreferences, and AddonPreferences is only accessible from a valid context
    bpy.app.timers.register(timed_reg_exec, first_interval=0)

def unregister():
    remove_exec_context_panel_all()
    remove_inspect_active_context_menu_all()
    # remove 'Add Inspect Panel' button from all Context menus (all Context types)
    remove_inspect_context_menu_all()
    # unregister Py Inspect panel UI classes
    unregister_all_inspect_panel_classes()
    if save_pre_handler_func in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(save_pre_handler_func)
    if load_post_handler_func in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post_handler_func)
    del bpy.types.WindowManager.py_rec
    del bpy.types.Scene.py_rec
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
