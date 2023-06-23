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

from ...object_custom_prop import CPROP_NAME_INIT_PY

PY_INFO_TEXT_NAME = "InfoText"

LINETYPE_CONTEXT = "CONTEXT"
LINETYPE_MACRO = "MACRO"
LINETYPE_INFO = "INFO"
LINETYPE_OPERATION = "OPERATION"
LINETYPE_PREV_DUP = "PREV_DUP"
LINETYPE_PY_REC = "PY_REC"

def text_object_poll(self, object):
    return object.type == 'FONT'

def get_info_lines(context):
    win = context.window_manager.windows[0]
    area = win.screen.areas[0]
    # keep copy of old type, so it can be reset later
    old_area_type = area.type
    area.type = 'INFO'
    # save old clipboard value
    old_clipboard_value = context.window_manager.clipboard
    # copy info lines to clipboard, with override context if Blender version is >= 3.2
    if bpy.app.version < (3, 2, 0):
        info_context = context.copy()
        info_context['window'] = win
        info_context['screen'] = win.screen
        info_context['area'] = win.screen.areas[0]
        # switch context to Info type, and select all Info lines
        bpy.ops.info.select_all(info_context, action='SELECT')
        # switch context to Info type, and copy all Info lines
        bpy.ops.info.report_copy(info_context)
    else:
        with context.temp_override(area=area):
            # switch context to Info type, and select all Info lines
            bpy.ops.info.select_all(action='SELECT')
            # switch context to Info type, and copy all Info lines
            bpy.ops.info.report_copy()
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

def create_text_object_from_info_lines(text_str, context):
    # create Text Object
    font_curve = bpy.data.curves.new(type='FONT', name="Font Curve")
    font_curve.body = text_str
    text_obj = bpy.data.objects.new(name=PY_INFO_TEXT_NAME, object_data=font_curve)
    # link new Text Object to currently active Collection
    context.view_layer.active_layer_collection.collection.objects.link(text_obj)
    return text_obj

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
    # create/use given Text / Text Object
    if options["use_text_object"]:
        text_ob = options["output_text_object"]
        if text_ob is None:
            text_ob = create_text_object_from_info_lines(text_str, context)
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
        "use_text_object": pr_ir.use_text_object,
        "output_text": pr_ir.output_text,
        "output_text_object": pr_ir.output_text_object,
    }
