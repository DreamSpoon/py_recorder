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

RECORD_DRIVER_TEXT_NAME = "pyrec_drivers.py"

# Animation Data sources, where drivers can exist - with rows added, as needed, for each new version
# [
#     ( data_source_name, (attribute_name1, attribute_name2, ...) ),
# ]
ANIMDATA_SOURCES = [
    # TODO: add bpy.data.images? or add comment explaining absence of bpy.data.images
    # TODO: sort alphabetically?
    ( "Armature", ["armatures"] ),
    ( "Cache File", ["cache_files"] ),
    ( "Camera", ["cameras"] ),
    ( "Curve", ["curves"] ),
    ( "Grease Pencil", ["grease_pencils"] ),
    ( "Lattice", ["lattices"] ),
    ( "Light", ["lights"] ),
    ( "Light Probe", ["lightprobes"] ),
    ( "Linestyle", ["linestyles"] ),
    ( "Linestyle Nodes", ["linestyles", "node_tree"] ),
    ( "Mask", ["masks"] ),
    ( "Material", ["materials"] ),
    ( "Material Nodes", ["materials", "node_tree"] ),
    ( "Geometry Nodes / Node Group", ["node_groups"] ),
    ( "Shape Key", ["shape_keys"] ),
    ( "Mesh", ["meshes"] ),
    ( "Metaball", ["metaballs"] ),
    ( "Movie Clip", ["movieclips"] ),
    ( "Object", ["objects"] ),
    ( "Particle Settings", ["particles"] ),
    ( "Scene", ["scenes"] ),
    ( "Compositor Nodes", ["scenes", "node_tree"] ),
    ( "Speaker", ["speakers"] ),
    ( "Texture", ["textures"] ),
    ( "Texture Nodes", ["textures", "node_tree"] ),
    ( "Volume", ["volumes"] ),
    ( "World", ["worlds"] ),
    ( "World Material Nodes", ["worlds", "node_tree"] ),
]
if bpy.app.version >= (3,10,0):
    ANIMDATA_SOURCES.append( ( "Point Cloud", ["pointclouds"] ) )
if bpy.app.version >= (3,30,0):
    ANIMDATA_SOURCES.append( ( "Hair Curve", ["hair_curves"] ) )

# sort tuples alphabetically by first value in each tuple
def sort_tup(tup):
    return(sorted(tup, key = lambda x: x[0]))

# sort alphabetically by first value in each tuple
ANIMDATA_SOURCES = sort_tup(ANIMDATA_SOURCES)

# exported function
def get_animdata_bool_names():
    names = []
    for dst in ANIMDATA_SOURCES:
        names.append(dst[0])
    return names

def add_quotes_and_backslashes(in_str):
    return in_str.replace("\\", "\\\\").replace("\"", "\\\"")

def remove_quotes_and_backslashes(in_str):
    return in_str.replace("\\\"", "\"").replace("\\\\", "\\")

def get_data_ref_str(thing, data_rlookup_table):
    return data_rlookup_table.get(str(thing))

def write_py_from_thing(textblock, line_prefix, data_rlookup_table, thing, path_str):
    # no drivers if no animation_data
    if not hasattr(thing, "animation_data") or thing.animation_data is None:
        return

    textblock.write(line_prefix + "drv_data_item = " + path_str + "\n")
    for d in thing.animation_data.drivers:
        drv = d.driver

        # check if the thing has length, and if so then include array index when adding driver
        path_resolved_thing = thing.path_resolve(d.data_path)
        if path_resolved_thing != None and hasattr(path_resolved_thing, "__len__"):
            textblock.write(line_prefix + "new_drv = drv_data_item.driver_add(\"" +
                           add_quotes_and_backslashes(d.data_path) + "\", " +
                           str(d.array_index) + ").driver\n")
        else:
            textblock.write(line_prefix + "new_drv = drv_data_item.driver_add(\"" +
                           add_quotes_and_backslashes(d.data_path) + "\").driver\n")

        textblock.write(line_prefix + "new_drv.type = \"" + drv.type + "\"\n")
        if drv.use_self:
            textblock.write(line_prefix + "new_drv.use_self = " + str(drv.use_self) + "\n")
        # write driver variables
        for v in drv.variables:
            textblock.write(line_prefix + "new_var = new_drv.variables.new()\n")
            textblock.write(line_prefix + "new_var.name = \"" + add_quotes_and_backslashes(v.name) + "\"\n")
            textblock.write(line_prefix + "new_var.type = \"" + v.type + "\"\n")
            # write targets of driver variable
            t_count = 0 # target count
            for t in v.targets:
                if t.id != None:
                    textblock.write(line_prefix + "new_var.targets[" + str(t_count) + "].id_type = \"" +
                                   t.id_type + "\"\n")
                    textblock.write(line_prefix + "new_var.targets[" + str(t_count) + "].id = " +
                                   get_data_ref_str(t.id, data_rlookup_table) + "\n")
                if t.bone_target != "":
                    textblock.write(line_prefix + "new_var.targets[" + str(t_count) + "].bone_target = \"" +
                                   add_quotes_and_backslashes(t.bone_target) + "\"\n")
                textblock.write(line_prefix + "new_var.targets[" + str(t_count) + "].transform_space = \"" +
                               t.transform_space + "\"\n")
                textblock.write(line_prefix + "new_var.targets[" + str(t_count) + "].transform_type = \"" +
                               t.transform_type + "\"\n")
                textblock.write(line_prefix + "new_var.targets[" + str(t_count) + "].rotation_mode = \"" +
                               t.rotation_mode + "\"\n")
                textblock.write(line_prefix + "new_var.targets[" + str(t_count) + "].data_path = \"" +
                               add_quotes_and_backslashes(t.data_path) + "\"\n")
                t_count = t_count + 1
        # write driver expression
        textblock.write(line_prefix + "new_drv.expression = \"" + drv.expression + "\"\n\n")

def write_py_data_recurse(textblock, line_prefix, rl_table, attr_list, attr_index, path_obj, path_str):
    next_attr_name = attr_list[attr_index]
    if not hasattr(path_obj, next_attr_name):
        return
    next_path_obj = getattr(path_obj, next_attr_name)
    if next_path_obj is None:
        return
    next_path_str =  path_str + "." + next_attr_name
    if hasattr(next_path_obj, "__len__"):
        c = 0
        for sub_obj in next_path_obj:
            # try to get thing name for indexing, rather than index number
            if hasattr(sub_obj, "name"):
                indexed_next_path_str = next_path_str + "[\""+sub_obj.name+"\"]"
            else:
                indexed_next_path_str = next_path_str + "["+str(c)+"]"
            # if this is the last attribute in the list then try to write py drivers from sub_obj
            if attr_index >= len(attr_list)-1:
                write_py_from_thing(textblock, line_prefix, rl_table, sub_obj, indexed_next_path_str)
            else:
                write_py_data_recurse(textblock, line_prefix, rl_table, attr_list, attr_index+1, sub_obj,
                                      indexed_next_path_str)
            c = c + 1
    else:
        # if this is the last attribute in the list then try to write py drivers from next_path_obj
        if attr_index >= len(attr_list)-1:
            write_py_from_thing(textblock, line_prefix, rl_table, next_path_obj, next_path_str)
        else:
            write_py_data_recurse(textblock, line_prefix, rl_table, attr_list, attr_index+1, next_path_obj,
                                  next_path_str)

def create_rlookup_table_recurse(rl_table, attr_list, attr_list_index, path_obj, path_str):
    next_attr_name = attr_list[attr_list_index]
    if not hasattr(path_obj, next_attr_name):
        return
    next_path_obj = getattr(path_obj, next_attr_name)
    if next_path_obj is None:
        return
    next_path_str =  path_str + "." + next_attr_name

    if hasattr(next_path_obj, "__len__"):
        c = 0
        for sub_obj in next_path_obj:
            # try to get thing name for indexing, rather than index number
            if hasattr(sub_obj, "name"):
                indexed_next_path_str = next_path_str + "[\""+sub_obj.name+"\"]"
            else:
                indexed_next_path_str = next_path_str + "["+str(c)+"]"
            # if this is the last attribute in the list then add the sub_obj to the reverse lookup table
            if attr_list_index >= len(attr_list)-1:
                rl_table[str(sub_obj)] = indexed_next_path_str
            else:
                create_rlookup_table_recurse(rl_table, attr_list, attr_list_index+1, sub_obj, indexed_next_path_str)
            c = c + 1
    else:
        # if this is the last attribute in the list then add the next_path_obj to the reverse lookup table
        if attr_list_index >= len(attr_list)-1:
            rl_table[str(next_path_obj)] = next_path_str
        else:
            create_rlookup_table_recurse(rl_table, attr_list, attr_list_index+1, next_path_obj, next_path_str)

def create_data_rlookup_table():
    new_rlookup_table = {}
    for ad_src in ANIMDATA_SOURCES:
        create_rlookup_table_recurse(new_rlookup_table, ad_src[1], 0, bpy.data, "bpy.data")
    return new_rlookup_table

def create_driver_py_from_data_item(space_pad, make_into_function, animdata_bool_vec):
    data_rlookup_table = create_data_rlookup_table()

    line_prefix = ""
    if isinstance(space_pad, int):
        line_prefix = " " * space_pad
    elif isinstance(space_pad, str):
        line_prefix = space_pad

    out_text = bpy.data.texts.new(RECORD_DRIVER_TEXT_NAME)
    out_text.write("# Blender Python script to re-create drivers of objects\n")

    if make_into_function:
        out_text.write("import bpy\n\n" +
                       "def create_drivers_of_objects():\n")

    text_len_before = len(out_text.lines)
    # iterate through all items in selected sources, and write code to create drivers
    for c in range(len(ANIMDATA_SOURCES)):
        # check if user selected this source
        if animdata_bool_vec[c]:
            write_py_data_recurse(out_text, line_prefix, data_rlookup_table, ANIMDATA_SOURCES[c][1], 0, bpy.data,
                              "bpy.data")
    text_len_after = len(out_text.lines)
    # if zero lines were written in function, then write a pass statement
    if text_len_after == text_len_before:
        out_text.write(line_prefix + "pass\n")

    if make_into_function:
        out_text.write("\ncreate_drivers_of_objects()\n")

    # scroll to top of lines of text, so user sees start of script immediately upon opening the textblock
    out_text.current_line_index = 0
    out_text.cursor_set(0)
    return out_text

class PYREC_OT_DriversToPython(bpy.types.Operator):
    bl_description = "Convert all drivers of selected data sources to Python code, available in the Text Editor"
    bl_idname = "py_rec.driver_editor_record_driver"
    bl_label = "Record Driver"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        dr = context.window_manager.py_rec.record_options.driver
        text = create_driver_py_from_data_item(dr.num_space_pad, dr.make_function, dr.animdata_bool_vec)
        self.report({'INFO'}, "Driver(s) recorded to Python in Text named '%s'" % text.name)
        return {'FINISHED'}

def set_bool_vec_state(bool_vec, state):
    for c in range(len(bool_vec)):
        bool_vec[c] = state

class PYREC_OT_SelectAnimdataSrcAll(bpy.types.Operator):
    bl_description = "Select all available data sources"
    bl_idname = "py_rec.driver_editor_select_animdata_src_all"
    bl_label = "Select All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        dr = context.window_manager.py_rec.record_options.driver
        set_bool_vec_state(dr.animdata_bool_vec, True)
        return {'FINISHED'}

class PYREC_OT_SelectAnimdataSrcNone(bpy.types.Operator):
    bl_description = "Select all available data sources"
    bl_idname = "py_rec.driver_editor_select_animdata_src_none"
    bl_label = "Select None"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        dr = context.window_manager.py_rec.record_options.driver
        set_bool_vec_state(dr.animdata_bool_vec, False)
        return {'FINISHED'}
