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

from mathutils import (Color, Vector)

import bpy

from ...bpy_value_string import bpy_value_to_string

RECORD_NODETREE_TEXT_NAME = "pyrec_nodetree.py"

exclude_attr_default_list = {
    "name": "",
    "label": "",
    "width": 0.0,
    "width_hidden": 42.0,
    "height": 100.0,
    "color": Color((0.608, 0.608, 0.608)),
    "use_custom_color": False,
    "mute": False,
    "hide": False,
    "select": None,
}

LOC_DEC_PLACES_UNI_NODE_OPT = "loc_decimal_places"
WRITE_ATTR_NAME_UNI_NODE_OPT = "write_attr_name"
WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT = "write_attr_width_height"
WRITE_ATTR_SELECT_UNI_NODE_OPT = "write_attr_select"

FILTER_OUT_ATTRIBS = ['color', 'dimensions', 'height', 'hide', 'inputs', 'internal_links', 'label', 'location',
                         'mute', 'name', 'outputs', 'parent', 'rna_type', 'select', 'show_options', 'show_preview',
                         'show_texture', 'type', 'use_custom_color', 'width', 'width_hidden',
                         'is_active_output', 'interface']

NODES_WITH_WRITE_OUTPUTS = ['ShaderNodeValue', 'ShaderNodeRGB', 'CompositorNodeValue', 'CompositorNodeRGB']

# add escape characters to backslashes and double-quote chars in given string
def esc_char_string(in_str):
    return in_str.replace('\\', '\\\\').replace('"', '\\"')

def bpy_compare_to_value(blender_value, va):
    if hasattr(blender_value, "__len__") and hasattr(va, "__len__"):
        # is it a set?
        if isinstance(blender_value, set):
            for item in blender_value:
                if item not in va:
                    return False
        else:
            for val_index in range(len(blender_value)):
                if blender_value[val_index] != va[val_index]:
                    return False
        return True
    else:
        return blender_value == va

def write_filtered_attribs(out_text, node, ignore_attribs):
    # loop through all attributes of 'node' object
    for attr_name in dir(node):
        # if attribute is in ignore attributes list, then continue to next attribute
        if attr_name in ignore_attribs:
            continue
        # get the attribute's value
        the_attr = getattr(node, attr_name)
        # filter out attributes that are built-ins (Python/Blender), or callable functions, or
        # attributes that are ignored/handled elsewhere
        if attr_name.startswith('__') or attr_name.startswith('bl_') or callable(the_attr) or \
            attr_name in FILTER_OUT_ATTRIBS:
            continue
        # if type is Color Ramp
        if type(the_attr) == bpy.types.ColorRamp:
            out_text.write("    node.%s.color_mode = \"%s\"\n" % (attr_name, the_attr.color_mode))
            out_text.write("    node.%s.interpolation = \"%s\"\n" % (attr_name, the_attr.interpolation))
            # remove one element before adding any new elements, leaving the minimum of one element in list
            # (deleting last element causes Blender error, but one elements needs to be deleted in case only 1 is used)
            out_text.write("    node.%s.elements.remove(node.%s.elements[0])\n" % (attr_name, attr_name))
            # add new elements, as needed
            elem_index = -1
            for el in the_attr.elements:
                elem_index = elem_index + 1
                # if writing first element then don't create new element
                if elem_index < 1:
                    out_text.write("    elem = node.%s.elements[0]\n" % attr_name)
                    out_text.write("    elem.position = %f\n" % el.position)
                # else create new element
                else:
                    out_text.write("    elem = node.%s.elements.new(%f)\n" % (attr_name, el.position))
                out_text.write("    elem.color = (%f, %f, %f, %f)\n" %
                               (el.color[0], el.color[1], el.color[2], el.color[3]))
        # if type is Curve Mapping, e.g. nodes Float Curve (Shader), RGB Curve (Shader), Time Curve (Compositor)
        elif type(the_attr) == bpy.types.CurveMapping:
            out_text.write("    node.%s.use_clip = %s\n" % (attr_name, the_attr.use_clip))
            out_text.write("    node.%s.clip_min_x = %f\n" % (attr_name, the_attr.clip_min_x))
            out_text.write("    node.%s.clip_min_y = %f\n" % (attr_name, the_attr.clip_min_y))
            out_text.write("    node.%s.clip_max_x = %f\n" % (attr_name, the_attr.clip_max_x))
            out_text.write("    node.%s.clip_max_y = %f\n" % (attr_name, the_attr.clip_max_y))
            out_text.write("    node.%s.extend = \"%s\"\n" % (attr_name, the_attr.extend))
            # note: Float Curve and Time Curve have 1 curve, RGB curve has 4 curves (C, R, G, B)
            curve_index = -1
            for curve in the_attr.curves:
                curve_index = curve_index + 1
                # addd new points, as needed
                point_index = -1
                for p in curve.points:
                    point_index = point_index + 1
                    # each curve starts with 2 points by default, so write into these points before creating more
                    # (2 points minimum, cannot delete them)
                    if point_index < 2:
                        out_text.write("    point = node.%s.curves[%d].points[%d]\n" %
                                       (attr_name, curve_index, point_index))
                        out_text.write("    point.location = (%f, %f)\n" % (p.location[0], p.location[1]))
                    # create new point
                    else:
                        out_text.write("    point = node.%s.curves[%d].points.new(%f, %f)\n" %
                                       (attr_name, curve_index, p.location[0], p.location[1]))
                    out_text.write("    point.handle_type = \"%s\"\n" % p.handle_type)
            # reset the clipping view
            out_text.write("    node.%s.reset_view()\n" % attr_name)
            # update the view of the mapping (trigger UI update)
            out_text.write("    node.%s.update()\n" % attr_name)
        # remaining types are String, Integer, Float, etc. (including bpy.types, e.g. bpy.types.Collection)
        else:
            val_str = bpy_value_to_string(the_attr)
            # do not write attributes that have value None
            # e.g. an 'object' attribute, that is set to None to indicate no object
            if val_str != None:
                out_text.write("    node.%s = %s\n" % (attr_name, val_str))

def get_node_io_value_str(node_io_element):
    # ignore virtual sockets and shader sockets, no default
    if node_io_element.bl_idname == 'NodeSocketVirtual' or node_io_element.bl_idname == 'NodeSocketShader':
        return None
    # if node doesn't have attribute 'default_value', then cannot save the value - so continue
    if not hasattr(node_io_element, 'default_value'):
        return None
    return bpy_value_to_string(node_io_element.default_value)

def write_socket_lines(out_text, node_grp_sockets, in_out_str):
    lines_to_write_bl4 = []
    lines_to_write_pre_bl4 = []
    lines_to_write_socket_values = []
    if in_out_str == 'INPUT':
        new_socket_var_name = "new_in_socket"
    else:
        new_socket_var_name = "new_out_socket"
    # write node group sockets
    for socket_num, ng_socket in enumerate(node_grp_sockets):
        # collect lines to be written before writing, to allow for checking if socket attributes need to be written
        def_val_lines_to_write = 0
        # check/write the min, max, default, and 'hide value' data
        if hasattr(ng_socket, "min_value") and ng_socket.min_value != -340282346638528859811704183484516925440.0:
            def_val_lines_to_write += 1
            lines_to_write_socket_values.append("    %s[%d].min_value = %s\n" % (new_socket_var_name,
                                                socket_num, bpy_value_to_string(ng_socket.min_value)))
        if hasattr(ng_socket, "max_value") and ng_socket.max_value != 340282346638528859811704183484516925440.0:
            def_val_lines_to_write += 1
            lines_to_write_socket_values.append("    %s[%d].max_value = %s\n" % (new_socket_var_name,
                                                socket_num, bpy_value_to_string(ng_socket.max_value)))
        if hasattr(ng_socket, "default_value") and ng_socket.default_value != None and \
            ng_socket.default_value != 0.0 and not bpy_compare_to_value(ng_socket.default_value, (0.0, 0.0, 0.0)) and \
                not ( ng_socket.bl_socket_idname == 'NodeSocketColor' and \
                        bpy_compare_to_value(ng_socket.default_value, (0.0, 0.0, 0.0, 1.0)) ):
            def_val_lines_to_write += 1
            lines_to_write_socket_values.append("    %s[%d].default_value = %s\n" % (new_socket_var_name,
                                                socket_num, bpy_value_to_string(ng_socket.default_value)))
        if ng_socket.hide_value:
            def_val_lines_to_write += 1
            lines_to_write_socket_values.append("    %s[%d].hide_value = True\n" % (new_socket_var_name,
                                                socket_num))
        # create new socket in/out variable only if necessary, i.e. if socket attribute values differ from default
        # values
        if def_val_lines_to_write > 0:
            lines_to_write_bl4.append("        %s[%d] = new_node_group.interface.new_socket(socket_type='%s', name=" \
                                      "\"%s\", in_out='%s')\n" % (new_socket_var_name, socket_num,
                                      ng_socket.bl_socket_idname, ng_socket.name, in_out_str) )
            if in_out_str == 'INPUT':
                lines_to_write_pre_bl4.append("        %s[%d] = new_node_group.inputs.new(type='%s', name=\"%s\")\n" %
                                              (new_socket_var_name, socket_num, ng_socket.bl_socket_idname,
                                               ng_socket.name))
            else:
                lines_to_write_pre_bl4.append("        %s[%d] = new_node_group.outputs.new(type='%s', name=\"%s\")\n" %
                                              (new_socket_var_name, socket_num, ng_socket.bl_socket_idname,
                                               ng_socket.name))
        else:
            lines_to_write_bl4.append("        new_node_group.interface.new_socket(socket_type='%s', name=\"%s\", " \
                                      "in_out='%s')\n" % (ng_socket.bl_socket_idname, ng_socket.name,
                                                          in_out_str))
            if in_out_str == 'INPUT':
                lines_to_write_pre_bl4.append("        new_node_group.inputs.new(type='%s', name=\"%s\")\n" %
                                              (ng_socket.bl_socket_idname, ng_socket.name))
            else:
                lines_to_write_pre_bl4.append("        new_node_group.outputs.new(type='%s', name=\"%s\")\n" %
                                              (ng_socket.bl_socket_idname, ng_socket.name))
    out_text.write("    " + new_socket_var_name + " = {}\n")
    out_text.write("    if bpy.app.version >= (4, 0, 0):\n")
    for l in lines_to_write_bl4:
        out_text.write(l)
    out_text.write("    else:\n")
    for l in lines_to_write_pre_bl4:
        out_text.write(l)
    for l in lines_to_write_socket_values:
        out_text.write(l)

def write_prerequisites(out_text):
    out_text.write("import bpy\n\n" +
                   "def set_node_io_values(node, is_input, io_values):\n" +
                   "    io_name_counts = {}\n" +
                   "    if is_input:\n" +
                   "        node_io = node.inputs\n" +
                   "    else:\n" +
                   "        node_io = node.outputs\n" +
                   "    for io_instance in node_io:\n" +
                   "        if io_instance.name not in io_values:\n" +
                   "            continue\n" +
                   "        name_count = io_name_counts.get(io_instance.name)\n" +
                   "        if name_count is None:\n" +
                   "            name_count = 1\n" +
                   "        else:\n" +
                   "            name_count += 1\n" +
                   "        io_name_counts[io_instance.name] = name_count\n" +
                   "        io_val = io_values[io_instance.name].get(name_count-1)\n" +
                   "        if io_val != None:\n" +
                   "            io_instance.default_value = io_val\n\n" +
                   "def create_nodetree_link(tree_links, from_node, from_name, from_name_count, to_node, to_name, " +
                   "to_name_count):\n" +
                   "    for out_s in from_node.outputs:\n" +
                   "        if out_s.name == from_name:\n" +
                   "            if from_name_count == 0:\n" +
                   "                for in_s in to_node.inputs:\n" +
                   "                    if in_s.name == to_name:\n" +
                   "                        if to_name_count == 0:\n" +
                   "                            return tree_links.new(out_s, in_s)\n" +
                   "                        to_name_count -= 1\n" +
                   "                return None\n" +
                   "            from_name_count -= 1\n" +
                   "    return None\n\n")

def get_node_io_name_num_for_socket(is_input, io_socket):
    if is_input:
        search_io = io_socket.node.inputs
    else:
        search_io = io_socket.node.outputs
    name_count = 0
    for sock in search_io:
        if sock == io_socket:
            return name_count
        if sock.name == io_socket.name:
            name_count += 1

def create_code_text(context, ng_output_min_max_def, uni_node_options):
    mat = context.space_data
    out_text = bpy.data.texts.new(RECORD_NODETREE_TEXT_NAME)
    node_group = bpy.data.node_groups.get(mat.edit_tree.name)
    is_tree_node_group = (node_group != None)

    out_text.write("# Python script from Blender version %d.%d.%d to create " %
                   (bpy.app.version[0], bpy.app.version[1], bpy.app.version[2]))
    # if using Node Group (Shader or Geometry Nodes)
    if is_tree_node_group:
        if mat.edit_tree.type == 'GEOMETRY':
            out_text.write("Geometry Nodes node group named %s\n\n" % mat.edit_tree.name)
        else:
            out_text.write("Shader Nodes node group named %s\n\n" % mat.edit_tree.name)
        write_prerequisites(out_text)
        out_text.write("# add nodes and links to node group\n" +
                        "def add_group_nodes(node_group_name):\n")
    # if using Compositor node tree
    elif mat.edit_tree.bl_idname == 'CompositorNodeTree':
        out_text.write("Compositor node tree\n\n")
        write_prerequisites(out_text)
        out_text.write("# add nodes and links to compositor node tree\n" +
                        "def add_shader_nodes(material):\n")
    # using Material node tree
    else:
        # check if World or Object material
        if bpy.data.worlds.get(mat.id.name):
            out_text.write("World Material named " + mat.id.name + "\n\n")
        elif bpy.data.linestyles.get(mat.id.name):
            out_text.write("Linestyle Material named " + mat.id.name + "\n\n")
        else:
            out_text.write("Object Material named " + mat.id.name + "\n\n")
        write_prerequisites(out_text)
        out_text.write("# add nodes and links to material\n" +
                        "def add_shader_nodes(material):\n")
    if is_tree_node_group:
        out_text.write("    new_node_group = bpy.data.node_groups.new(name=node_group_name, type='%s')\n" %
                       mat.edit_tree.bl_idname)
        out_text.write("    # remove old group inputs and outputs\n")
        out_text.write("    if bpy.app.version >= (4, 0, 0):\n")
        out_text.write("        for item in new_node_group.interface.items_tree:\n")
        out_text.write("            if item.item_type == 'SOCKET':\n")
        out_text.write("                new_node_group.interface.remove(item)\n")
        out_text.write("    else:\n")
        out_text.write("        new_node_group.inputs.clear()\n")
        out_text.write("        new_node_group.outputs.clear()\n")
 
        if bpy.app.version >= (4, 0, 0):
            node_grp_inputs = [ s for s in node_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT' ]
            node_grp_outputs = [ s for s in node_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'OUTPUT' ]
        else:
            node_grp_inputs = node_group.inputs
            node_grp_outputs = node_group.outputs
        if len(node_grp_inputs) > 0 or len(node_grp_outputs) > 0:
            out_text.write("    # create new group inputs and outputs\n")

        write_socket_lines(out_text, node_grp_inputs, 'INPUT')
        write_socket_lines(out_text, node_grp_outputs, 'OUTPUT')

        out_text.write("    tree_nodes = new_node_group.nodes\n")
    else:
        out_text.write("    tree_nodes = material.node_tree.nodes\n")
    out_text.write("    # delete all existing nodes before creating new nodes\n")
    out_text.write("    tree_nodes.clear()\n")
    out_text.write("    # create nodes\n")
    out_text.write("    new_nodes = {}\n")
    # set parenting order of nodes (e.g. parenting to frames) after creating all the nodes in the tree,
    # so that parent nodes are referenced only after parent nodes are created
    frame_parenting_text = ""
    # write info about the individual nodes
    for tree_node in mat.edit_tree.nodes:
        out_text.write("    # %s\n" % tree_node.bl_label)
        out_text.write("    node = tree_nodes.new(type=\"%s\")\n" % tree_node.bl_idname)
        ignore_attribs = []
        for attr in exclude_attr_default_list:
            # Input Color node will write this value, so ignore it for now
            if tree_node.bl_idname == 'FunctionNodeInputColor' and attr == 'color':
                continue
            if hasattr(tree_node, attr):
                gotten_attr = getattr(tree_node, attr)
                # if a default value is found, then skip the default value
                if gotten_attr == exclude_attr_default_list[attr]:
                    continue
                # if not writing 'name' then skip
                elif attr == 'name' and uni_node_options[WRITE_ATTR_NAME_UNI_NODE_OPT] == False:
                    continue
                # if not writing width and height then skip
                elif (attr == 'width' or attr == 'height') and \
                        uni_node_options[WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT] == False:
                    continue
                # if not writing select state then skip
                elif attr == 'select' and uni_node_options[WRITE_ATTR_SELECT_UNI_NODE_OPT] == False:
                    continue

                out_text.write("    node.%s = %s\n" % (attr, bpy_value_to_string(gotten_attr)))
        # node with parent is special, this node is offset by their parent frame's location
        parent_loc = Vector((0, 0))
        if tree_node.parent != None:
            parent_loc = tree_node.parent.location
        # do rounding of location values, if needed, and write the values
        precision = uni_node_options[LOC_DEC_PLACES_UNI_NODE_OPT]
        loc_x = tree_node.location.x + parent_loc.x
        loc_y = tree_node.location.y + parent_loc.y
        out_text.write("    node.location = (%0.*f, %0.*f)\n" % (precision, loc_x, precision, loc_y))
        # Input Color, this attribute is special because this node type's Color attribute is swapped - very strange!
        # (maybe a dinosaur left over from old versions of Blender)
        if tree_node.bl_idname == 'FunctionNodeInputColor':
            out_text.write("    node.color = %s\n" % (bpy_value_to_string(tree_node.color)))
            ignore_attribs.append("color")

        write_filtered_attribs(out_text, tree_node, ignore_attribs)

        # if not a Frame or a Reroute, then write tree_node inputs and outputs
        if tree_node.type not in ["FRAME", "REROUTE"]:
            # get node input(s) default value(s), each input might be [ float, (R, G, B, A), (X, Y, Z), shader ]
            # TODO: this part needs more testing re: different node input default value(s) and type(s)
            input_name_counts = {}
            input_values = {}
            for node_input in tree_node.inputs:
                name_count = input_name_counts.get(node_input.name)
                if name_count is None:
                    name_count = 0
                name_count += 1
                input_name_counts[node_input.name] = name_count
                if node_input.hide_value or node_input.is_linked:
                    continue
                value_str = get_node_io_value_str(node_input)
                if value_str is None:
                    continue
                if input_values.get(node_input.name) is None:
                    input_values[node_input.name] = {}
                input_values[node_input.name][name_count-1] = value_str
            if len(input_values) > 0:
                out_text.write("    set_node_io_values(node, True, {\n")
                for inp_name in input_values:
                    out_text.write("        \"%s\": {\n" % inp_name)
                    for inp_name_c in input_values[inp_name]:
                        out_text.write("            %d: %s,\n" % (inp_name_c, input_values[inp_name][inp_name_c]))
                    out_text.write("            },\n")
                out_text.write("        })\n")

            # get node output(s) default value(s), each output might be [ float, (R, G, B, A), (X, Y, Z), shader ]
            # TODO: this part needs more testing re: different node output default value(s) and type(s)
            if tree_node.bl_idname in NODES_WITH_WRITE_OUTPUTS:
                output_name_counts = {}
                output_values = {}
                for node_output in tree_node.outputs:
                    name_count = output_name_counts.get(node_output.name)
                    if name_count is None:
                        name_count = 0
                    name_count += 1
                    output_name_counts[node_output.name] = name_count
                    # always write the value, even if linked, because this node is special
                    value_str = get_node_io_value_str(node_output)
                    if value_str is None:
                        continue
                    if output_values.get(node_output.name) is None:
                        output_values[node_output.name] = {}
                    output_values[node_output.name][name_count-1] = value_str
                if len(output_values) > 0:
                    out_text.write("    set_node_io_values(node, False, {\n")
                    for outp_name in output_values:
                        out_text.write("        \"%s\": {\n" % outp_name)
                        for outp_name_c in output_values[outp_name]:
                            out_text.write("            %d: %s,\n" % (outp_name_c, output_values[outp_name][outp_name_c]))
                        out_text.write("            },\n")
                    out_text.write("        })\n")

        out_text.write("    new_nodes[\"%s\"] = node\n" % tree_node.name)
        # save a reference to parent node for later, if parent node exists
        if tree_node.parent != None:
            frame_parenting_text = "%s    new_nodes[\"%s\"].parent = new_nodes[\"%s\"]\n" % \
                                   (frame_parenting_text, tree_node.name, tree_node.parent.name)

    # do node parenting if needed
    if frame_parenting_text != "":
        out_text.write("    # parenting of nodes\n%s\n" % frame_parenting_text)
    # create links
    out_text.write("    # create links\n")
    if is_tree_node_group:
        out_text.write("    tree_links = new_node_group.links\n")
    else:
        out_text.write("    tree_links = material.node_tree.links\n")
    for tree_link in mat.edit_tree.links:
        from_name_num = get_node_io_name_num_for_socket(False, tree_link.from_socket)
        to_name_num = get_node_io_name_num_for_socket(True, tree_link.to_socket)
        out_text.write("    create_nodetree_link(tree_links, new_nodes[\"%s\"], \"%s\", %d, new_nodes[\"%s\"], " \
                       "\"%s\", %d)\n" % (tree_link.from_socket.node.name, tree_link.from_socket.name, from_name_num,
                                         tree_link.to_socket.node.name, tree_link.to_socket.name, to_name_num))
        

    # created nodes are selected by default so deselect them
    out_text.write("    # deselect all new nodes\n    for n in new_nodes.values(): n.select = False\n")

    if is_tree_node_group:
        out_text.write("    return new_node_group\n")
    else:
        out_text.write("    return new_nodes\n")

    # if using nodes in a group (Shader or Geometry Nodes)
    if is_tree_node_group:
        out_text.write("\n# use Python script to add nodes, and links between nodes, to new Node Group\n" \
                        "add_group_nodes('%s')\n" % mat.edit_tree.name)
    # if using World material node tree
    elif bpy.data.worlds.get(mat.id.name):
        out_text.write("\n# use Python script to create World material, including nodes and links\n" \
                        "world_mat = bpy.data.worlds.new(\"%s\")\n" \
                        "world_mat.use_nodes = True\n" \
                        "add_shader_nodes(world_mat)\n" % mat.id.name)
    # if using Compositor node tree
    elif mat.edit_tree.bl_idname == 'CompositorNodeTree':
        out_text.write("\n# use Python script to add nodes, and links between nodes, to Compositor node tree\n" \
                        "add_shader_nodes(bpy.context.scene)\n")
    # if using Linestyle node tree
    elif bpy.data.linestyles.get(mat.id.name):
        out_text.write("\n# use Python script to create Linestyle, including nodes and links\n" \
                        "linestyle_mat = bpy.data.linestyles.new(\"%s\")\n" \
                        "linestyle_mat.use_nodes = True\n" \
                        "add_shader_nodes(linestyle_mat)\n" % mat.id.name)
    # else using Object Material Shader Nodes
    else:
        out_text.write("\n# use Python script to create Material, including nodes and links\n" \
                        "mat = bpy.data.materials.new(\"%s\")\n" \
                        "mat.use_nodes = True\n" \
                        "add_shader_nodes(mat)\n" % mat.id.name)

    # scroll to top of lines of text, so user sees start of script immediately upon opening the textblock
    out_text.current_line_index = 0
    out_text.cursor_set(0)
    return out_text
