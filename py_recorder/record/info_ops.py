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
from bpy.props import (BoolProperty, EnumProperty, IntProperty, PointerProperty, StringProperty)
from bpy.types import (Operator, Panel, PropertyGroup)

from ..bpy_value_string import BPY_DATA_TYPE_ITEMS
from ..object_custom_prop import CPROP_NAME_INIT_PY

PY_INFO_TEXT_NAME = "InfoText"

LINETYPE_CONTEXT = "CONTEXT"
LINETYPE_MACRO = "MACRO"
LINETYPE_INFO = "INFO"
LINETYPE_OPERATION = "OPERATION"
LINETYPE_PREV_DUP = "PREV_DUP"
LINETYPE_PY_REC = "PY_REC"

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

def text_object_poll(self, object):
    return object.type == 'FONT'

class PYREC_PG_InfoRecordOptions(PropertyGroup):
    create_root_object: BoolProperty(name="Create Root", description="New root Object will be created, instead of " +
        "using active Object as root (Text / Text Object will be linked to root Object)",
        default=False)
    root_init: BoolProperty(name="Root " + CPROP_NAME_INIT_PY, description="Create Custom Property '" +
        CPROP_NAME_INIT_PY + "' on root Object, so root Object can be 'run' by running its '" + CPROP_NAME_INIT_PY +
        "' script", default=True)
    use_text_object: BoolProperty(name="Use Text Object", description="Text Object will be used for output, " +
        "instead of Text (in Text Editor)", default=False)
    output_text_object: PointerProperty(name="Output Text Object", description="Text Object to receive output. " +
        "If empty then new Text Object will be created", type=bpy.types.Object, poll=text_object_poll)
    output_text: PointerProperty(name="Output Text", description="Text (in Text Editor) to receive " +
        "output", type=bpy.types.Text)
    filter_line_count: IntProperty(name="Line Count", description="Filter Line Count: Number of filtered lines to " +
        "copy from Info", default=20, min=1)
    include_line_type_context: BoolProperty(name="Context", description="Copy Context type Info lines (lines " +
        "beginning with \"bpy.context\")", default=True)
    include_line_type_info: BoolProperty(name="Info", description="Copy general information type Info lines " +
        "(example: console error output)", default=False)
    include_line_type_macro: BoolProperty(name="Macro", description="Copy Info lines that cannot be run",
        default=False)
    include_line_type_operation: BoolProperty(name="Operation", description="Copy Operation type Info lines (lines " +
        "beginning with \"bpy.ops\")", default=True)
    include_line_type_prev_dup: BoolProperty(name="Prev Duplicate", description="Copy Info lines that have " +
        "previous duplicates (i.e. the same \"bpy.ops\" operation repeated, or the same \"bpy.context\" value set). " +
        "If set to False, then only most recent operation / context change is copied", default=True)
    include_line_type_py_rec: BoolProperty(name="Py Recorder", description="Copy Info lines related to Py " +
        "Recorder operation or state change (lines beginning with \"bpy.ops.py_rec\" or " +
        "\"bpy.context.scene.py_rec\")", default=False)
    comment_line_type_context: BoolProperty(name="Context", description="Comment out Context type Info " +
        "lines (lines beginning with \"bpy.context\")", default=False)
    comment_line_type_info: BoolProperty(name="Info", description="Comment out general information type Info " +
        "lines (example: console error output)", default=True)
    comment_line_type_macro: BoolProperty(name="Macro", description="Comment out Macro type Info " +
        "lines", default=True)
    comment_line_type_operation: BoolProperty(name="Operation", description="Comment out Operation type Info lines " +
        "(lines beginning with \"bpy.ops\"", default=False)
    comment_line_type_prev_dup: BoolProperty(name="Prev Duplicate", description="Comment out previous duplicate " +
        "lines from Info", default=True)
    comment_line_type_py_rec: BoolProperty(name="Py Recorder", description="Comment out Info lines related to Py " +
        "Recorder operations or state changes (lines beginning with \"bpy.ops.py_rec\" or " +
        "\"bpy.context.scene.py_rec\")", default=True)
    root_collection: PointerProperty(name="Root", description="New root Objects will be put into this collection",
        type=bpy.types.Collection)
    text_object_collection: PointerProperty(name="Text", description="New Text Objects will be put into this " +
        "collection", type=bpy.types.Collection)
    add_cp_data_name: StringProperty(name="Name", description="Custom Property name", default="")
    add_cp_data_type: EnumProperty(name="Type", description="Data type", items=BPY_DATA_TYPE_ITEMS, default="objects")
    add_cp_datablock: StringProperty(name="Data", description="Custom Property value", default="")
    modify_data_type: EnumProperty(name="Type", description="Type of data, either Text or Text Object",
        items=[ ("texts", "Text", "", 1), ("objects", "Text Object", "", 2), ("None", "None", "", 3) ] )
    modify_data_text: PointerProperty(name="Data", description="Text (see Blender's builtin Text Editor) to " +
        "use for active Object's '"+CPROP_NAME_INIT_PY+"' script", type=bpy.types.Text)
    modify_data_obj: PointerProperty(name="Data", description="Text Object to use for active Object's '" +
        CPROP_NAME_INIT_PY+"' script", type=bpy.types.Object, poll=text_object_poll)
    record_info_line: BoolProperty(name="Record Info line", description="", default=False)
    record_info_start_line_offset: IntProperty(name="Start Record Info line count", description="", default=0)
    record_auto_import_bpy: BoolProperty(name="Auto 'import bpy'", description="Automatically prepend line to " +
        "recorded / copied script, to prevent run script error: \"NameError: name 'bpy' is not defined\"",
        default=False)

class PYREC_PT_VIEW3D_RecordInfo(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tool"
    bl_label = "Py Record Info"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        layout = self.layout

        box = layout.box()
        sub_box = box.box()
        # show 'Stop Record' button if recording is on,
        if pr_ir.record_info_line:
            sub_box.operator(PYREC_OT_VIEW3D_StopRecordInfoLine.bl_idname)
        # show 'Start Record' button if recording is off
        else:
            sub_box.operator(PYREC_OT_VIEW3D_StartRecordInfoLine.bl_idname)

        rec_state = "Off"
        if pr_ir.record_info_line:
            rec_state = "On"
        sub_box.label(text="Recording: " + rec_state)
        box.operator(PYREC_OT_VIEW3D_CopyInfoToObjectText.bl_idname)

        box = layout.box()
        sub_box = box.box()
        sub_box.prop(pr_ir, "record_auto_import_bpy")
        sub_box.prop(pr_ir, "filter_line_count")

        sub_box.prop(pr_ir, "root_init")
        sub_box.prop(pr_ir, "create_root_object")
        if pr_ir.create_root_object:
            sub_box.prop(pr_ir, "root_collection")
        sub_box.prop(pr_ir, "use_text_object")
        if pr_ir.use_text_object:
            sub_box.prop(pr_ir, "output_text_object")
            sub_box.prop(pr_ir, "text_object_collection")
        else:
            sub_box.prop(pr_ir, "output_text")

        sub_box = box.box()
        sub_box.label(text="Line Options")
        row = sub_box.row()
        row.label(text="Type")
        row.label(text="Include/Comment")
        sub_sub_box = sub_box.box()
        row = sub_sub_box.row()
        row.label(text="Context")
        row.prop(pr_ir, "include_line_type_context", text="")
        row.prop(pr_ir, "comment_line_type_context", text="")
        row = sub_sub_box.row()
        row.label(text="Info")
        row.prop(pr_ir, "include_line_type_info", text="")
        row.prop(pr_ir, "comment_line_type_info", text="")
        row = sub_sub_box.row()
        row.label(text="Macro")
        row.prop(pr_ir, "include_line_type_macro", text="")
        row.prop(pr_ir, "comment_line_type_macro", text="")
        row = sub_sub_box.row()
        row.label(text="Operation")
        row.prop(pr_ir, "include_line_type_operation", text="")
        row.prop(pr_ir, "comment_line_type_operation", text="")
        row = sub_sub_box.row()
        row.label(text="Prev Duplicate")
        row.prop(pr_ir, "include_line_type_prev_dup", text="")
        row.prop(pr_ir, "comment_line_type_prev_dup", text="")
        row = sub_sub_box.row()
        row.label(text="Py Recorder")
        row.prop(pr_ir, "include_line_type_py_rec", text="")
        row.prop(pr_ir, "comment_line_type_py_rec", text="")

def get_datablock_for_type(data):
    for dd in DATABLOCK_DUAL_TYPES:
        if isinstance(data, dd[0]):
            return dd[1]
    return None

def get_info_lines(context):
    win = context.window_manager.windows[0]
    area = win.screen.areas[0]
    # keep copy of old type, so it can be reset later
    old_area_type = area.type
    area.type = 'INFO'
    # save old clipboard value
    old_clipboard_value = context.window_manager.clipboard
    # copy info lines to clipboard
    info_context = context.copy()
    info_context['window'] = win
    info_context['screen'] = win.screen
    info_context['area'] = win.screen.areas[0]
    # switch context to Info type, and select all Info lines
    bpy.ops.info.select_all(info_context, action='SELECT')
    # switch context to Info type, and copy all Info lines
    bpy.ops.info.report_copy(info_context)
    # reset area type to its previous value, to avoid errors
    area.type = old_area_type
    # if clipboard is empty then return empty string
    if context.window_manager.clipboard == "":
        return ""
    # get contents of clipboard (copy of all Info lines)
    ret_value = context.window_manager.clipboard
    # retore old clipboard value
    context.window_manager.clipboard = old_clipboard_value
    return ret_value

def check_add_prev_lines(line, split_str, prev_lines):
    if split_str != "":
        line = line.partition(split_str)[0]
    is_prev = prev_lines.get(line) != None
    if is_prev:
        return True
    else:
        prev_lines[line] = True
        return False

def filter_info_lines(info_lines, copy_start_line_offset, filter_line_count, include_line_types):
    if info_lines is None or include_line_types is None or len(include_line_types) < 1:
        return []
    filtered_lines = []
    include_context = LINETYPE_CONTEXT in include_line_types
    include_info = LINETYPE_INFO in include_line_types
    include_macro = LINETYPE_MACRO in include_line_types
    include_operation = LINETYPE_OPERATION in include_line_types
    include_prev_dup = LINETYPE_PREV_DUP in include_line_types
    include_py_rec = LINETYPE_PY_REC in include_line_types
    # filter by copy start line offset (ascending order)
    if copy_start_line_offset != None and copy_start_line_offset > 0:
        info_lines = info_lines[copy_start_line_offset:]
    # filter by line type
    prev_lines = {}
    # traverse info_lines array in reverse order, because of previous duplicate checking
    for l in reversed(info_lines):
        if l.startswith("bpy.ops.py_rec"):
            if include_py_rec:
                is_dup = check_add_prev_lines(l, "(", prev_lines)
                if is_dup and not include_prev_dup:
                    continue
                filtered_lines.append( (LINETYPE_PY_REC, is_dup, l) )
        elif l.startswith("bpy.context.window_manager.py_rec"):
            if include_py_rec:
                is_dup = check_add_prev_lines(l, "=", prev_lines)
                if is_dup and not include_prev_dup:
                    continue
                filtered_lines.append( (LINETYPE_PY_REC, is_dup, l) )
        elif l.startswith("bpy.ops"):
            if include_operation:
                is_dup = check_add_prev_lines(l, "(", prev_lines)
                if is_dup and not include_prev_dup:
                    continue
                filtered_lines.append( (LINETYPE_OPERATION, is_dup, l) )
        elif l.startswith("bpy.data.window_managers[\"WinMan\"].(null)"):
            if include_macro:
                is_dup = check_add_prev_lines(l, "", prev_lines)
                if is_dup and not include_prev_dup:
                    continue
                filtered_lines.append( (LINETYPE_MACRO, is_dup, l) )
        elif l.startswith("bpy.context"):
            if include_context:
                is_dup = check_add_prev_lines(l, "=", prev_lines)
                if is_dup and not include_prev_dup:
                    continue
                filtered_lines.append( (LINETYPE_CONTEXT, is_dup, l) )
        elif include_info:
            is_dup = check_add_prev_lines(l, "", prev_lines)
            if is_dup and not include_prev_dup:
                continue
            filtered_lines.append( (LINETYPE_INFO, is_dup, l) )
    # reverse the reversed order
    filtered_lines = [fl for fl in reversed(filtered_lines)]
    # filter by line count
    if filter_line_count != None and filter_line_count > 0:
        filtered_lines = filtered_lines[-filter_line_count:]
    return filtered_lines

def create_text_object(context, obj_name="Text", text_body=""):
    font_curve = bpy.data.curves.new(type='FONT', name="Font Curve")
    font_curve.body = text_body
    text_obj = bpy.data.objects.new(name=obj_name, object_data=font_curve)
    # link new Text Object to currently active Collection
    context.view_layer.active_layer_collection.collection.objects.link(text_obj)
    return text_obj

def get_text_str_from_info_lines(info_lines, comment_line_types):
    if info_lines is None:
        return ""
    text_str = ""
    for l in info_lines:
        if comment_line_types != None and (l[0] in comment_line_types or \
                                           (l[1] and LINETYPE_PREV_DUP in comment_line_types)):
            text_str = text_str + "# "
        text_str = text_str + l[2] + "\n"
    return text_str

def create_text_object_from_info_lines(text_str, context, text_obj_collection):
    # create Text Object
    text_ob = create_text_object(context, obj_name=PY_INFO_TEXT_NAME, text_body=text_str)
    # set Text Object Collection if needed
    if text_obj_collection != None:
        # unlink from previous Collection(s)
        for uc in text_ob.users_collection:
            uc.objects.unlink(text_ob)
        # link to given Text Object Collection
        text_obj_collection.objects.link(text_ob)
    return text_ob

def create_text_from_info_lines(text_str):
    # create Text Object
    text = bpy.data.texts.new(PY_INFO_TEXT_NAME)
    text.write(text_str)
    return text

# if success then return new Text / Text Object, else return None
def copy_filtered_info_lines(context, options):
    info_lines = get_info_lines(context).splitlines()
    line_end = len(info_lines)
    filtered_lines = filter_info_lines(info_lines, options["copy_start_line_offset"], options["filter_line_count"],
                                       options["include_line_types"])
    text_str = get_text_str_from_info_lines(filtered_lines, options["comment_line_types"])
    # do not create object if body of text_str is empty
    if text_str == "":
        # return fail
        return None, None, None

    if options["record_auto_import_bpy"]:
        text_str = "import bpy\n" + text_str

    # get root Object from active Object only if active Object is selected
    root_ob = context.active_object
    if root_ob != None and not root_ob.select_get():
        root_ob = None
    # create root Object if needed
    if options["create_root_object"]:
        bpy.ops.mesh.primitive_cube_add()
        if root_ob != None:
            context.active_object.location = root_ob.matrix_world.to_translation()
        root_ob = context.active_object
        # set root Collection if needed
        if options["root_collection"] != None:
            # unlink from previous Collection
            if len(root_ob.users_collection) > 0:
                root_ob.users_collection[0].objects.unlink(root_ob)
            # link to given root Collection
            options["root_collection"].objects.link(root_ob)
    # create/use given Text / Text Object
    if options["use_text_object"]:
        text_ob = options["output_text_object"]
        if text_ob is None:
            text_ob = create_text_object_from_info_lines(text_str, context, options["text_obj_collection"])
        else:
            # prepend newline to separate new text lines from old text lines
            text_ob.data.body = text_ob.data.body + "\n" + text_str
        # if root Object exists, parent Text Object to root Object (Keep Transform)
        if root_ob:
            text_ob.parent = root_ob
        link_thing = text_ob
    else:
        text = options["output_text"]
        if text is None:
            text = create_text_from_info_lines(text_str)
        else:
            # prepend newline to separate new text lines from old text lines
            text.write("\n"+text_str)
        link_thing = text
    # if root Object exists and Root Init is enabled, then link Text Object to root Object
    if root_ob != None and options["root_init"]:
        root_ob[CPROP_NAME_INIT_PY] = link_thing
    # return success
    return line_end, len(filtered_lines), link_thing

def get_include_line_types(pr_ir):
    # convert include line type booleans to string array
    include_line_types = []
    if pr_ir.include_line_type_context:
        include_line_types.append(LINETYPE_CONTEXT)
    if pr_ir.include_line_type_info:
        include_line_types.append(LINETYPE_INFO)
    if pr_ir.include_line_type_macro:
        include_line_types.append(LINETYPE_MACRO)
    if pr_ir.include_line_type_operation:
        include_line_types.append(LINETYPE_OPERATION)
    if pr_ir.include_line_type_prev_dup:
        include_line_types.append(LINETYPE_PREV_DUP)
    if pr_ir.include_line_type_py_rec:
        include_line_types.append(LINETYPE_PY_REC)
    return include_line_types

def get_comment_line_types(pr_ir):
    # convert comment line type booleans to string array
    comment_line_types = []
    if pr_ir.comment_line_type_context:
        comment_line_types.append(LINETYPE_CONTEXT)
    if pr_ir.comment_line_type_info:
        comment_line_types.append(LINETYPE_INFO)
    if pr_ir.comment_line_type_macro:
        comment_line_types.append(LINETYPE_MACRO)
    if pr_ir.comment_line_type_operation:
        comment_line_types.append(LINETYPE_OPERATION)
    if pr_ir.comment_line_type_prev_dup:
        comment_line_types.append(LINETYPE_PREV_DUP)
    if pr_ir.comment_line_type_py_rec:
        comment_line_types.append(LINETYPE_PY_REC)
    return comment_line_types

def get_copy_info_options(pr_ir, copy_start_line_offset):
    return {
        "record_auto_import_bpy": pr_ir.record_auto_import_bpy,
        "copy_start_line_offset": copy_start_line_offset,
        "filter_line_count": pr_ir.filter_line_count,
        "include_line_types": get_include_line_types(pr_ir),
        "comment_line_types": get_comment_line_types(pr_ir),
        "root_init": pr_ir.root_init,
        "create_root_object": pr_ir.create_root_object,
        "root_collection": pr_ir.root_collection,
        "text_obj_collection": pr_ir.text_object_collection,
        "use_text_object": pr_ir.use_text_object,
        "output_text": pr_ir.output_text,
        "output_text_object": pr_ir.output_text_object,
    }

class PYREC_OT_VIEW3D_StartRecordInfoLine(Operator):
    bl_idname = "py_rec.view3d_start_record_info_line"
    bl_label = "Start Record"
    bl_description = "Mark current end line of Info lines as 'Start Record' line. When 'Stop Record' is used, " \
        "then lines from Info context will be copied, beginning at 'Start Record' line and ending at 'Stop Record' " \
        "line, inclusive. See Info context window"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        pr_ir.record_info_line = True
        pr_ir.record_info_start_line_offset = len(get_info_lines(context).splitlines())
        self.report({'INFO'}, "Start Record: begin at Info line number %i" % pr_ir.record_info_start_line_offset)
        return {'FINISHED'}

class PYREC_OT_VIEW3D_StopRecordInfoLine(Operator):
    bl_idname = "py_rec.view3d_stop_record_info_line"
    bl_label = "Stop Record"
    bl_description = "Copy Info context lines to Text or Text Object body, and link Text / Text Object to active " \
        "Object (active Object must be selected). Copy begins at 'Start Record' line and ends at 'Stop Record' " \
        "line of Info context, inclusive"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        line_start = pr_ir.record_info_start_line_offset
        line_end, filter_line_count, output_thing = copy_filtered_info_lines(context,
                                                                             get_copy_info_options(pr_ir, line_start))
        # reset recording variables
        pr_ir.record_info_line = False
        pr_ir.record_info_start_line_offset = 0
        if output_thing is None:
            self.report({'ERROR'}, "Stop Record: Zero filtered Info lines found, no lines written")
            return {'CANCELLED'}
        if isinstance(output_thing, bpy.types.Object):
            thing_type = "Object"
        elif isinstance(output_thing, bpy.types.Text):
            thing_type = "Text"
        else:
            thing_type = "thing"
        if line_start+1 == line_end:
            l_str = " %i" % line_end
        else:
            l_str = "s beginning at %i, ending at %i," % (line_start+1, line_end)
        if hasattr(output_thing, "name"):
            thing_name = output_thing.name
        else:
            thing_name = str(output_thing)
        self.report({'INFO'}, "Stop Record: copy Info line"+l_str+" (filtered line count %i) to %s %s" %
                    (filter_line_count, thing_type, thing_name))
        return {'FINISHED'}

class PYREC_OT_VIEW3D_CopyInfoToObjectText(Operator):
    bl_idname = "py_rec.view3d_copy_info_to_object_text"
    bl_label = "Copy Info"
    bl_description = "Copy recently run Blender commands (e.g. rotate Object, create Mesh Plane) to Text or Text " \
        "Object body, and link Text / Text Object to active Object (active Object must be selected). See Info " \
        "context window"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_ir = context.window_manager.py_rec.record_options.info
        line_end, filter_line_count, output_thing = copy_filtered_info_lines(context,
                                                                             get_copy_info_options(pr_ir, None))
        if output_thing is None:
            self.report({'ERROR'}, "Copy Info: Zero filtered Info lines found, no lines written")
            return {'CANCELLED'}
        if isinstance(output_thing, bpy.types.Object):
            thing_type = "Object"
        elif isinstance(output_thing, bpy.types.Text):
            thing_type = "Text"
        else:
            thing_type = "thing"
        if line_end == 1:
            l_str = " 1"
        else:
            l_str = "s from 1 to %i" % line_end
        if hasattr(output_thing, "name"):
            thing_name = output_thing.name
        else:
            thing_name = str(output_thing)
        self.report({'INFO'}, "Copy Info: copy Info line"+l_str+" (filtered line count %i) to %s %s" %
                    (filter_line_count, thing_type, thing_name))
        return {'FINISHED'}
