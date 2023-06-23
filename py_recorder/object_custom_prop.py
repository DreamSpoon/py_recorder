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

import bpy
from bpy.types import (Operator, Panel)

CPROP_NAME_INIT_PY = "__init__.py"

DATABLOCK_DUAL_TYPES = (
    (bpy.types.Action, "actions"),
    (bpy.types.Armature, "armatures"),
    (bpy.types.Brush, "brushes"),
    (bpy.types.CacheFile, "cache_files"),
    (bpy.types.Camera, "cameras"),
    (bpy.types.Collection, "collections"),
    (bpy.types.Curve, "curves"),
    (bpy.types.VectorFont, "fonts"),
    (bpy.types.GreasePencil, "grease_pencils"),
    (bpy.types.Image, "images"),
    (bpy.types.Lattice, "lattices"),
    (bpy.types.Library, "libraries"),
    (bpy.types.Light, "lights"),
    (bpy.types.LightProbe, "lightprobes"),
    (bpy.types.FreestyleLineStyle, "linestyles"),
    (bpy.types.Mask, "masks"),
    (bpy.types.Material, "materials"),
    (bpy.types.Mesh, "meshes"),
    (bpy.types.MetaBall, "metaballs"),
    (bpy.types.MovieClip, "movieclips"),
    (bpy.types.NodeGroup, "node_groups"),
    (bpy.types.Object, "objects"),
    (bpy.types.PaintCurve, "paint_curves"),
    (bpy.types.Palette, "palettes"),
    (bpy.types.ParticleSettings, "particles"),
    (bpy.types.ShapeKey, "shape_keys"),
    (bpy.types.Scene, "scenes"),
    (bpy.types.Screen, "screens"),
    (bpy.types.Sound, "sounds"),
    (bpy.types.Speaker, "speakers"),
    (bpy.types.Text, "texts"),
    (bpy.types.Texture, "textures"),
    (bpy.types.Volume, "volumes"),
    (bpy.types.WorkSpace, "workspaces"),
    (bpy.types.World, "worlds"),
)
if bpy.app.version >= (3,10,0):
    DATABLOCK_DUAL_TYPES = DATABLOCK_DUAL_TYPES + (bpy.types.PointCloud, "pointclouds"),
if bpy.app.version >= (3,30,0):
    DATABLOCK_DUAL_TYPES = DATABLOCK_DUAL_TYPES + (bpy.types.Curves, "hair_curves"),

def get_datablock_for_type(data):
    for dd in DATABLOCK_DUAL_TYPES:
        if isinstance(data, dd[0]):
            return dd[1]
    return None

class PYREC_OT_OBJ_ModifyInit(Operator):
    bl_description = "Modify active Object's custom property '"+CPROP_NAME_INIT_PY+""
    bl_idname = "py_rec.object_modify_init"
    bl_label = "Modify Data Type"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        if pr_ir.modify_data_type == "texts":
            context.active_object[CPROP_NAME_INIT_PY] = pr_ir.modify_data_text
        elif pr_ir.modify_data_type == "objects":
            context.active_object[CPROP_NAME_INIT_PY] = pr_ir.modify_data_obj
        else:
            try:
                del context.active_object[CPROP_NAME_INIT_PY]
            except:
                pass
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        pr_ir = context.window_manager.py_rec.record_options.info
        layout.prop(pr_ir, "modify_data_type")
        if pr_ir.modify_data_type == "texts":
            layout.prop(pr_ir, "modify_data_text")
        elif pr_ir.modify_data_type == "objects":
            layout.prop(pr_ir, "modify_data_obj")

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

class PYREC_OT_OBJ_AddCP_Data(Operator):
    bl_idname = "py_rec.object_add_custom_property_data"
    bl_label = "New"
    bl_description = "Create new Custom Property on active Object, with given Name and Data"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        return context.active_object != None and pr_ir.add_cp_data_name not in [None, ""] and \
            pr_ir.add_cp_datablock not in [None, ""]

    def execute(self, context):
        act_ob = context.active_object
        pr_ir = context.window_manager.py_rec.record_options.info
        v = getattr(bpy.data, pr_ir.add_cp_data_type).get(pr_ir.add_cp_datablock)
        if v != None:
            act_ob[pr_ir.add_cp_data_name] = v
        return {'FINISHED'}

class PYREC_PT_OBJ_AdjustCustomProp(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = "Py Custom Properties"
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
