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
    "version": (0, 6, 1),
    "author": "Dave",
    "blender": (2, 80, 0),
    "description": "Create and apply Presets. Inspect Python value attributes. Record Blender data to Python code",
    "location": "3DView -> Tools -> Tool -> Py Record Info, Py Exec Object. Right-click Context menu -> " \
        "Add Inspect Panel. Context -> Tool -> Py Inspect",
    "doc_url": "https://github.com/DreamSpoon/py_recorder#readme",
    "category": "Presets, Python",
}

import numpy
import types

import bpy
from bpy.app.handlers import persistent
from bpy.types import (Panel, PropertyGroup)
from bpy.props import (BoolProperty, CollectionProperty, PointerProperty, StringProperty)
from bpy.utils import (register_class, unregister_class)

from .addon_prefs import (PYREC_PG_LogAddonPrefs, PYREC_PG_InterfaceAddonPrefs, PYREC_AddonPreferences)
from .object_custom_prop import (PYREC_OT_OBJ_AddCP_Data, PYREC_OT_OBJ_ModifyInit, PYREC_PT_OBJ_AdjustCustomProp)
from .context_exec.panel import (append_exec_context_panel_all, remove_exec_context_panel_all)
from .context_exec.operator import PYREC_OT_ContextExec
from .context_exec.props import PYREC_PG_ContextExecOptions
from .inspect.func import (register_inspect_panel_draw_func, unregister_all_inspect_panel_classes)
from .inspect.menu import (PYREC_MT_InspectActive, append_inspect_context_menu_all,
    remove_inspect_context_menu_all, append_inspect_active_context_menu_all, remove_inspect_active_context_menu_all)
from .inspect.operator import (PYREC_OT_InspectOptions, PYREC_OT_AddInspectPanel, PYREC_OT_RemoveInspectPanel,
    PYREC_OT_InspectPanelAttrZoomIn, PYREC_OT_InspectPanelAttrZoomOut, PYREC_OT_InspectPanelArrayIndexZoomIn,
    PYREC_OT_InspectPanelArrayKeyZoomIn, PYREC_OT_RestoreInspectContextPanels, PYREC_OT_InspectRecordAttribute,
    PYREC_OT_InspectCopyAttribute, PYREC_OT_InspectPasteAttribute, PYREC_OT_InspectChoosePy,
    PYREC_OT_PyInspectActiveObject)
from .inspect.panel import draw_inspect_panel
from .inspect.props import (PYREC_PG_AttributeRecordOptions, PYREC_PG_DirAttributeItem, PYREC_PG_InspectPanelOptions,
    PYREC_PG_InspectPanel, PYREC_PG_InspectPanelCollection)
from .object_exec.operator import (PYREC_OT_BatchExecObject, PYREC_OT_ExecObject)
from .object_exec.panel import PYREC_PT_VIEW3D_ExecObject
from .object_exec.props import PYREC_PG_ObjectExecOptions
from .preset.list import (PYREC_UL_PresetClipboardProps, PYREC_UL_PresetApplyProps, PYREC_UL_PresetModifyProps,
    PYREC_UL_PresetModifyCollections, PYREC_UL_PresetModifyPresets)
from .preset.operator import (PYREC_OT_PresetClipboardClear, PYREC_OT_PresetClipboardRemoveItem,
    PYREC_OT_PresetClipboardCreatePreset, PYREC_OT_PresetPropsRemoveItem, PYREC_OT_PresetApply,
    PYREC_OT_PresetModifyCollection, PYREC_OT_PresetRemoveCollection, PYREC_OT_PresetModifyPreset,
    PYREC_OT_PresetRemovePreset, PYREC_OT_QuicksavePreferences, PYREC_OT_PresetExportFile, PYREC_OT_PresetImportFile,
    PYREC_OT_PresetExportObject, PYREC_OT_PresetImportObject, PYREC_OT_TransferObjectPresets,
    PYREC_OT_TextToPresetClipboard)
from .preset.panel import (PYREC_PT_View3dPreset, PYREC_PT_TextEditorPreset)
from .preset.props import (PYREC_PG_BoolProp, PYREC_PG_EulerProp, PYREC_PG_IntProp, PYREC_PG_FloatProp,
    PYREC_PG_FloatVector3Prop, PYREC_PG_FloatVector4Prop, PYREC_PG_Layer20Prop, PYREC_PG_Layer32Prop,
    PYREC_PG_StringProp, PYREC_PG_PresetPropDetail, PYREC_PG_Preset, PYREC_PG_PresetCollection,
    PYREC_PG_PresetTypeCollection, PYREC_PG_PresetClipboardPropDetail, PYREC_PG_PresetClipboard,
    PYREC_PG_PresetClipboardOptions, PYREC_PG_PresetApplyOptions, PYREC_PG_PresetModifyOptions,
    PYREC_PG_PresetOptions, PYREC_PG_PresetImpExpOptions)
from .record.driver.operator import (PYREC_OT_DriversToPython, PYREC_OT_SelectAnimdataSrcAll,
    PYREC_OT_SelectAnimdataSrcNone)
from .record.driver.panel import PYREC_PT_RecordDriver
from .record.driver.props import PYREC_PG_DriverRecordOptions
from .record.info.operator import (PYREC_OT_VIEW3D_CopyInfoToObjectText, PYREC_OT_VIEW3D_StartRecordInfoLine,
    PYREC_OT_VIEW3D_StopRecordInfoLine)
from .record.info.panel import PYREC_PT_VIEW3D_RecordInfo
from .record.info.props import PYREC_PG_InfoRecordOptions
from .record.node_tree.operator import PYREC_OT_RecordNodetree
from .record.node_tree.panel import PYREC_PT_RecordNodetree
from .record.node_tree.props import PYREC_PG_NodetreeRecordOptions

class PYREC_PG_RecordOptions(PropertyGroup):
    attribute: PointerProperty(type=PYREC_PG_AttributeRecordOptions)
    driver: PointerProperty(type=PYREC_PG_DriverRecordOptions)
    info: PointerProperty(type=PYREC_PG_InfoRecordOptions)
    nodetree: PointerProperty(type=PYREC_PG_NodetreeRecordOptions)

class PYREC_PG_PyRec(PropertyGroup):
    record_options: PointerProperty(type=PYREC_PG_RecordOptions)
    context_exec_options: PointerProperty(type=PYREC_PG_ContextExecOptions)
    object_exec_options: PointerProperty(type=PYREC_PG_ObjectExecOptions)
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
    PYREC_PG_ObjectExecOptions,
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
    PYREC_PG_RecordOptions,
    PYREC_PG_ContextExecOptions,

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
    PYREC_OT_PresetExportFile,
    PYREC_OT_PresetImportFile,
    PYREC_OT_PresetExportObject,
    PYREC_OT_PresetImportObject,
    PYREC_OT_TransferObjectPresets,
    PYREC_OT_TextToPresetClipboard,
    PYREC_PT_View3dPreset,
    PYREC_PT_TextEditorPreset,

    PYREC_PG_BoolProp,
    PYREC_PG_EulerProp,
    PYREC_PG_IntProp,
    PYREC_PG_FloatProp,
    PYREC_PG_FloatVector3Prop,
    PYREC_PG_FloatVector4Prop,
    PYREC_PG_Layer20Prop,
    PYREC_PG_Layer32Prop,
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
    PYREC_PG_PresetApplyOptions,
    PYREC_PG_PresetModifyOptions,
    PYREC_PG_PresetImpExpOptions,
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
    register_inspect_panel_draw_func(draw_inspect_panel)
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
