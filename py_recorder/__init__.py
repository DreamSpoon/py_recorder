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
    "version": (0, 5, 0),
    "author": "Dave",
    "blender": (2, 80, 0),
    "description": "Inspect Python object attributes. Record Blender data to Python code. Record Info lines to " \
        "Text / Text Object script so that user actions in Blender can be recreated later by running the script",
    "location": "3DView -> Tools -> Tool -> Py Record Info, Py Exec Object. Right-click Context menu -> " \
        "Add Inspect Panel. Context -> Tool -> Py Inspect",
    "doc_url": "https://github.com/DreamSpoon/py_recorder#readme",
    "category": "Python",
}

import numpy

import bpy
from bpy.app.handlers import persistent
from bpy.types import (Panel, PropertyGroup)
from bpy.props import (CollectionProperty, PointerProperty)
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
        pr_ir = context.window_manager.py_rec.record_options.info
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
        box.prop(pr_ir, "add_cp_data_name")
        box.prop(pr_ir, "add_cp_data_type")
        box.prop_search(pr_ir, "add_cp_datablock", bpy.data, pr_ir.add_cp_data_type, text="")
        box.operator(PYREC_OT_OBJ_AddCP_Data.bl_idname)

########################

class PYREC_PG_RecordOptions(PropertyGroup):
    attribute: PointerProperty(type=PYREC_PG_AttributeRecordOptions)
    driver: PointerProperty(type=PYREC_PG_DriverRecordOptions)
    info: PointerProperty(type=PYREC_PG_InfoRecordOptions)
    nodetree: PointerProperty(type=PYREC_PG_NodetreeRecordOptions)

class PYREC_PG_PyRec(PropertyGroup):
    inspect_context_collections: CollectionProperty(type=PYREC_PG_InspectPanelCollection)
    record_options: PointerProperty(type=PYREC_PG_RecordOptions)
    exec_options: PointerProperty(type=PYREC_PG_ExecOptions)

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
    PYREC_PG_ExecOptions,
    PYREC_OT_ContextExec,
    PYREC_PG_PyRec,
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
            if isinstance(from_item, bpy.types.PropertyGroup) or \
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
    append_exec_context_panel_all()

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
