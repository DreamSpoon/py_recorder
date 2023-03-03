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

import traceback
from datetime import datetime as dt

import bpy
from bpy.types import Operator

from .object_custom_prop import CPROP_NAME_INIT_PY
from .string_exec import exec_str

PY_INFO_TEXT_NAME = "InfoText"

SCRIPT_RUN_NAME_APPEND = "_RunTemp"
ERROR_RUN_NAME_APPEND = "_Error"

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

CP_DATA_TYPE_ITEMS = [
    ('actions', "Action", "", 1),
    ('armatures', "Armature", "", 2),
    ('brushes', "Brush", "", 3),
    ('cache_files', "Cache File", "", 4),
    ('cameras', "Camera", "", 5),
    ('collections', "Collection", "", 6),
    ('curves', "Curve", "", 7),
    ('fonts', "Font", "", 8),
    ('grease_pencils', "Grease Pencil", "", 9),
    ('images', "Image", "", 10),
    ('lattices', "Lattice", "", 11),
    ('libraries', "Library", "", 12),
    ('lights', "Light", "", 13),
    ('lightprobes', "Light Probe", "", 14),
    ('linestyles', "Line Style", "", 15),
    ('masks', "Mask", "", 16),
    ('materials', "Material", "", 17),
    ('meshes', "Mesh", "", 18),
    ('metaballs', "Meta Ball", "", 19),
    ('movieclips', "Movie Clip", "", 20),
    ('node_groups', "Node Group", "", 21),
    ('objects', "Object", "", 22),
    ('paint_curves', "Paint Curve", "", 23),
    ('palettes', "Palette", "", 24),
    ('particles', "Particle Settings", "", 25),
    ('shape_keys', "Shape Key", "", 26),
    ('scenes', "Scene", "", 27),
    ('screens', "Screen", "", 28),
    ('sounds', "Sound", "", 29),
    ('speakers', "Speaker", "", 30),
    ('textures', "Texture", "", 31),
    ('texts', "Text", "", 32),
    ('volumes', "Volume", "", 33),
    ('workspaces', "Work Space", "", 34),
    ('worlds', "World", "", 35),
]
if bpy.app.version >= (3,10,0):
    CP_DATA_TYPE_ITEMS = CP_DATA_TYPE_ITEMS + ('pointclouds', "Point Cloud", "", len(CP_DATA_TYPE_ITEMS)+1)
if bpy.app.version >= (3,30,0):
    CP_DATA_TYPE_ITEMS = CP_DATA_TYPE_ITEMS + ('hair_curves', "Hair Curve", "", len(CP_DATA_TYPE_ITEMS)+1)

MODIFY_DATA_TYPE_ITEMS = [
    ('texts', "Text", "", 1),
    ('objects', "Text Object", "", 2),
    ('None', "None", "", 3),
]

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
    return context.window_manager.clipboard

def check_add_prev_lines(line, split_str, prev_lines):
    if split_str != "":
        line = line.partition(split_str)[0]
    is_prev = prev_lines.get(line) != None
    if is_prev:
        return True
    else:
        prev_lines[line] = True
        return False

def filter_info_lines(info_lines, copy_start_line_offset, filter_end_line_offset, filter_line_count,
                      include_line_types):
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
        elif l.startswith("bpy.context.scene.py_rec"):
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
    # filter by line offset (descending order)
    if filter_end_line_offset != None and filter_end_line_offset > 0:
        filtered_lines = filtered_lines[:-filter_end_line_offset]
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
    filtered_lines = filter_info_lines(info_lines, options["copy_start_line_offset"],
        options["filter_end_line_offset"], options["filter_line_count"], options["include_line_types"])
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
        "filter_end_line_offset": pr_ir.filter_end_line_offset,
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

def get_current_info_line_count(context):
    return len(get_info_lines(context).splitlines())

class PYREC_OT_VIEW3D_StartRecordInfoLine(Operator):
    bl_idname = "py_rec.view3d_start_record_info_line"
    bl_label = "Start Record"
    bl_description = "Mark current end line of Info lines as 'Start Record' line. When 'Stop Record' is used, " \
        "then lines from Info context will be copied, beginning at 'Start Record' line and ending at 'Stop Record' " \
        "line, inclusive. See Info context window"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_ir = context.scene.py_rec.record_info_options
        pr_ir.record_info_line = True
        pr_ir.record_info_start_line_offset = get_current_info_line_count(context)
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
        pr_ir = context.scene.py_rec.record_info_options
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
        pr_ir = context.scene.py_rec.record_info_options
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

def create_error_text(error_text_name, error_msg):
    date_time = dt.now().strftime("Error date: %m/%d/%Y\nError time: %H:%M:%S\n")
    # create Text to receive error message string
    print("Py Recorder: create error traceback Text named: " + error_text_name)
    error_text = bpy.data.texts.new(name=error_text_name)
    error_text.from_string(date_time+error_msg)

def add_text_prepend_import_bpy(text):
    # save state of Text current/select line/character, with plus one line because 'import bpy' will be prepended
    old_data = (text.current_character, text.current_line_index+1,
                text.select_end_character, text.select_end_line_index+1)
    # write prepend to first character of first line of text
    (text.current_character, text.current_line_index,
     text.select_end_character, text.select_end_line_index) = (0, 0, 0, 0)
    text.write("import bpy\n")
    # restore state of Text current and select line/character
    (text.current_character, text.current_line_index,
     text.select_end_character, text.select_end_line_index) = old_data

def remove_text_prepend_import_bpy(text):
    # save state of Text current/select line/character, with minus one line because 'import bpy' will be removed
    current_line_index = text.current_line_index-1
    if current_line_index < 0:
        current_line_index = 0
    select_end_line_index = text.select_end_line_index-1
    if select_end_line_index < 0:
        select_end_line_index = 0
    old_data = (text.current_character, current_line_index,
                text.select_end_character, select_end_line_index)
    # select first line of 'text'
    (text.current_character, text.current_line_index,
     text.select_end_character, text.select_end_line_index) = (0, 0, 0, 1)
    # write empty string to 'delete' selected line
    text.write("")
    # restore state of Text current and select line/character
    (text.current_character, text.current_line_index,
     text.select_end_character, text.select_end_line_index) = old_data

# returns False on error, otherwise returns True
def run_script_in_text_editor(context, textblock, auto_import_bpy):
    # prepend 'import bpy' line if needed
    if auto_import_bpy:
        add_text_prepend_import_bpy(textblock)
    # switch context UI type to Text Editor
    prev_type = context.area.ui_type
    context.area.ui_type = 'TEXT_EDITOR'
    # set Text as active in Text Editor
    context.space_data.text = textblock
    # try to run script, allowing for graceful fail, where graceful fail is:
    #   -Python error, lines after run_script will not be run, i.e.
    #     -remain in Text Editor with temporary Text active, so user has quick access to Text script with error
    try:
        print("Py Recorder: bpy.ops.text.run_script() called with Text named: " + textblock.name)
        bpy.ops.text.run_script()
    except:
        # return False because script caused an error, so Text Editor will remain as current context, and user has
        # quick access to script with error
        tb = traceback.format_exc()
        print(tb)   # print(tb) replaces traceback.print_exc()
        # create Text to receive error traceback message as string
        create_error_text(textblock.name+ERROR_RUN_NAME_APPEND, tb)
        return False
    # change context to previous type
    context.area.ui_type = prev_type
    # remove 'import bpy' line if it was prepended
    if auto_import_bpy:
        remove_text_prepend_import_bpy(textblock)
    # return True because script did not cause error
    return True

# returns False on error, otherwise returns True
def run_text_object_body(context, text_ob, use_temp_text, auto_import_bpy):
    text_str = text_ob.data.body
    if use_temp_text:
        # temporary Text name includes Text Object name, to help user identify and debug issues/errors
        temp_text = bpy.data.texts.new(name=text_ob.name+SCRIPT_RUN_NAME_APPEND)
        # write lines from Text Object body to temporary Text
        temp_text.write(text_str)
        # return False if run script resulted in error
        if not run_script_in_text_editor(context, temp_text, auto_import_bpy):
            return False
        # remove temporary Text, only if run script did not result in error
        bpy.data.texts.remove(temp_text)
    else:
        print("Py Recorder: exec() with Text Object named: " + text_ob.name)
        succeed, error_msg = exec_str(text_str, auto_import_bpy)
        if not succeed:
            create_error_text(text_ob.name+ERROR_RUN_NAME_APPEND, error_msg)
            return False
    return True

# returns False on error, otherwise returns True
def run_object_init(context, ob, use_temp_text, auto_import_bpy):
    init_thing = ob.get(CPROP_NAME_INIT_PY)
    if init_thing != None:
        if isinstance(init_thing, bpy.types.Text):
            # if run results in error then return False to indicate error result
            if not run_script_in_text_editor(context, init_thing, auto_import_bpy):
                return False
        elif isinstance(init_thing, bpy.types.Object) and init_thing.type == 'FONT':
            # if run results in error then return False to indicate error result
            if not run_text_object_body(context, init_thing, use_temp_text, auto_import_bpy):
                return False
    # no errors, so return True
    return True

class PYREC_OT_VIEW3D_RunObjectScript(Operator):
    bl_idname = "py_rec.view3d_run_object_script"
    bl_label = "Exec Object"
    bl_description = "Run selected Objects' Custom Property '"+CPROP_NAME_INIT_PY+"' as script. If property is " \
        "Text Object type: Text Object body is copied to temporary Text, and Text is run as script. If property is " \
        "Text type: Text is run as script using '.run_script()'"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pr_ir = context.scene.py_rec.record_info_options
        for ob in context.selected_objects:
            # if run results in error, then halt and print name of Object that has script with error
            if not run_object_init(context, ob, pr_ir.use_temp_text, pr_ir.run_auto_import_bpy):
                self.report({'ERROR'}, "Error, see System Console for details of run of Object named: " + ob.name)
                return {'CANCELLED'}
        return {'FINISHED'}
