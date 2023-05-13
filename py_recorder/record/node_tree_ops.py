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
from bpy.types import (Operator, Panel, PropertyGroup)
from bpy.props import (BoolProperty, IntProperty)

from ..bpy_value_string import bpy_value_to_string

RECORD_NODETREE_TEXT_NAME = "pyrec_nodetree.py"

uni_attr_default_list = {
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

WRITE_DEFAULTS_UNI_NODE_OPT = "write_defaults"
WRITE_LINKED_DEFAULTS_UNI_NODE_OPT = "write_linked_defaults"
LOC_DEC_PLACES_UNI_NODE_OPT = "loc_decimal_places"
WRITE_ATTR_NAME_UNI_NODE_OPT = "write_attr_name"
WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT = "write_attr_width_height"
WRITE_ATTR_SELECT_UNI_NODE_OPT = "write_attr_select"

FILTER_OUT_ATTRIBS = ['color', 'dimensions', 'height', 'hide', 'inputs', 'internal_links', 'label', 'location',
                         'mute', 'name', 'outputs', 'parent', 'rna_type', 'select', 'show_options', 'show_preview',
                         'show_texture', 'type', 'use_custom_color', 'width', 'width_hidden',
                         'is_active_output', 'interface']

NODES_WITH_WRITE_OUTPUTS = ['ShaderNodeValue', 'ShaderNodeRGB', 'CompositorNodeValue', 'CompositorNodeRGB']

class PYREC_PG_NodetreeRecordOptions(PropertyGroup):
    num_space_pad: IntProperty(name="Num Space Pad", description="Number of spaces to prepend to each " +
        "line of code output in text-block", default=4, min=0)
    keep_links: BoolProperty(name="Keep Links List", description="Add created links to a list variable",
        default=False)
    make_function: BoolProperty(name="Make into Function", description="Add lines of Python code to " +
        "create runnable script (instead of just the bare essential code)", default=True)
    delete_existing: BoolProperty(name="Delete Existing Nodes",
        description="Include code in the output that deletes all nodes in Shader Material / Geometry Node Setup " +
        "before creating new nodes", default=True)
    write_loc_decimal_places: IntProperty(name="Location Decimal Places", description="Number of " +
        "decimal places to use when writing location values", default=0)
    write_default_values: BoolProperty(name="Write Defaults", description="Write node attributes " +
        "that are set to default values (e.g. node attributes: label, name)", default=False)
    write_linked_default_values: BoolProperty(name="Linked Default Values", description="Write default " +
        "values, of node inputs and outputs, where the input/output is linked to another node", default=False)
    write_attrib_name: BoolProperty(name="Name", description="Include node attribute 'name'", default=False)
    write_attrib_width_and_height: BoolProperty(name="Width and Height", description="Include node " +
        "attributes for width and height", default=False)
    write_attrib_select: BoolProperty(name="Select", description="Include node " +
        "attribute for select state (e.g. selected nodes can be 'marked' for easy search later)", default=False)
    ng_output_min_max_def: BoolProperty(name="Output Min/Max/Default", description="Include Minimum, Maximum, " +
        "and Default value for each node group output", default=False)

class PYREC_PT_RecordNodetree(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"
    bl_label = "Py Record Nodetree"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ntr = context.window_manager.py_rec.record_options.nodetree
        layout = self.layout
        box = layout.box()
        box.operator(PYREC_OT_RecordNodetree.bl_idname)
        box = layout.box()
        box.label(text="General Options")
        box.prop(ntr, "num_space_pad")
        box.prop(ntr, "keep_links")
        box.prop(ntr, "make_function")
        box.prop(ntr, "delete_existing")
        box.prop(ntr, "ng_output_min_max_def")
        box = layout.box()
        box.label(text="Node Attribute Options")
        box.prop(ntr, "write_attrib_name")
        box.prop(ntr, "write_attrib_select")
        sub_box = box.box()
        sub_box.prop(ntr, "write_attrib_width_and_height")
        sub_box.prop(ntr, "write_loc_decimal_places")
        box = layout.box()
        box.label(text="Write Defaults Options")
        box.prop(ntr, "write_default_values")
        box.prop(ntr, "write_linked_default_values")

# add escape characters to backslashes and double-quote chars in given string
def esc_char_string(in_str):
    return in_str.replace('\\', '\\\\').replace('"', '\\"')

def get_input_num_for_link(tr_link):
    for c in range(0, len(tr_link.to_socket.node.inputs)):
        if tr_link.to_socket.node.inputs[c] == tr_link.to_socket:
            return c
    return None

def get_output_num_for_link(tr_link):
    for c in range(0, len(tr_link.from_socket.node.outputs)):
        if tr_link.from_socket.node.outputs[c] == tr_link.from_socket:
            return c
    return None

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

def write_filtered_attribs(out_text, line_prefix, node, ignore_attribs):
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
            out_text.write("%snode.%s.color_mode = \"%s\"\n" % (line_prefix, attr_name, the_attr.color_mode))
            out_text.write("%snode.%s.interpolation = \"%s\"\n" % (line_prefix, attr_name, the_attr.interpolation))
            # remove one element before adding any new elements, leaving the minimum of one element in list
            # (deleting last element causes Blender error, but one elements needs to be deleted in case only 1 is used)
            out_text.write("%snode.%s.elements.remove(node.%s.elements[0])\n" % (line_prefix, attr_name, attr_name))
            # add new elements, as needed
            elem_index = -1
            for el in the_attr.elements:
                elem_index = elem_index + 1
                # if writing first element then don't create new element
                if elem_index < 1:
                    out_text.write("%selem = node.%s.elements[0]\n" % (line_prefix, attr_name))
                    out_text.write("%selem.position = %f\n" % (line_prefix, el.position))
                # else create new element
                else:
                    out_text.write("%selem = node.%s.elements.new(%f)\n" % (line_prefix, attr_name, el.position))
                out_text.write("%selem.color = (%f, %f, %f, %f)\n" %
                               (line_prefix, el.color[0], el.color[1], el.color[2], el.color[3]))
        # if type is Curve Mapping, e.g. nodes Float Curve (Shader), RGB Curve (Shader), Time Curve (Compositor)
        elif type(the_attr) == bpy.types.CurveMapping:
            out_text.write("%snode.%s.use_clip = %s\n" % (line_prefix, attr_name, the_attr.use_clip))
            out_text.write("%snode.%s.clip_min_x = %f\n" % (line_prefix, attr_name, the_attr.clip_min_x))
            out_text.write("%snode.%s.clip_min_y = %f\n" % (line_prefix, attr_name, the_attr.clip_min_y))
            out_text.write("%snode.%s.clip_max_x = %f\n" % (line_prefix, attr_name, the_attr.clip_max_x))
            out_text.write("%snode.%s.clip_max_y = %f\n" % (line_prefix, attr_name, the_attr.clip_max_y))
            out_text.write("%snode.%s.extend = \"%s\"\n" % (line_prefix, attr_name, the_attr.extend))
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
                        out_text.write("%spoint = node.%s.curves[%d].points[%d]\n" %
                                       (line_prefix, attr_name, curve_index, point_index))
                        out_text.write("%spoint.location = (%f, %f)\n" % (line_prefix, p.location[0], p.location[1]))
                    # create new point
                    else:
                        out_text.write("%spoint = node.%s.curves[%d].points.new(%f, %f)\n" %
                                       (line_prefix, attr_name, curve_index, p.location[0], p.location[1]))
                    out_text.write("%spoint.handle_type = \"%s\"\n" % (line_prefix, p.handle_type))
            # reset the clipping view
            out_text.write("%snode.%s.reset_view()\n" % (line_prefix, attr_name))
            # update the view of the mapping (trigger UI update)
            out_text.write("%snode.%s.update()\n" % (line_prefix, attr_name))
        # remaining types are String, Integer, Float, etc. (including bpy.types, e.g. bpy.types.Collection)
        else:
            val_str = bpy_value_to_string(the_attr)
            # do not write attributes that have value None
            # e.g. an 'object' attribute, that is set to None to indicate no object
            if val_str != None:
                out_text.write("%snode.%s = %s\n" % (line_prefix, attr_name, val_str))

def get_node_io_value_str(node_io_element, write_linked):
    # ignore virtual sockets and shader sockets, no default
    if node_io_element.bl_idname == 'NodeSocketVirtual' or node_io_element.bl_idname == 'NodeSocketShader':
        return None
    # if node doesn't have attribute 'default_value', then cannot save the value - so continue
    if not hasattr(node_io_element, 'default_value'):
        return None
    # if 'do not write linked default values', and this input socket is linked then skip
    if not write_linked and node_io_element.is_linked:
        return None
    return bpy_value_to_string(node_io_element.default_value)

def create_code_text(context, space_pad, keep_links, make_into_function, delete_existing, ng_output_min_max_def,
                     uni_node_options):
    line_prefix = ""
    if isinstance(space_pad, int):
        line_prefix = " " * space_pad
    elif isinstance(space_pad, str):
        line_prefix = space_pad

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
        if make_into_function:
            out_text.write("import bpy\n\n" +
                           "# add nodes and links to node group\n" +
                           "def add_group_nodes(node_group_name):\n")
    # if using Compositor node tree
    elif mat.edit_tree.bl_idname == 'CompositorNodeTree':
        out_text.write("Compositor node tree\n\n")
        if make_into_function:
            out_text.write("import bpy\n\n" +
                           "# add nodes and links to compositor node tree\n" +
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
        if make_into_function:
            out_text.write("import bpy\n\n" +
                           "# add nodes and links to material\n" +
                           "def add_shader_nodes(material):\n")
    if is_tree_node_group:
        out_text.write("%snew_node_group = bpy.data.node_groups.new(name=node_group_name, type='%s')\n" %
                       (line_prefix, mat.edit_tree.bl_idname))
        out_text.write(line_prefix + "# remove old group inputs and outputs\n")
        out_text.write(line_prefix + "new_node_group.inputs.clear()\n")
        out_text.write(line_prefix + "new_node_group.outputs.clear()\n")
        if len(node_group.inputs) > 0 or len(node_group.outputs) > 0:
            out_text.write(line_prefix + "# create new group inputs and outputs\n")
        # write group inputs
        for ng_input in node_group.inputs:
            # collect lines to be written before writing, to allow for checking if input attributes need to be written
            lines_to_write = []
            # check/write the min, max, default, and 'hide value' data
            if hasattr(ng_input, "min_value") and ng_input.min_value != -340282346638528859811704183484516925440.0:
                lines_to_write.append("%snew_input.min_value = %s\n" %
                                      (line_prefix, bpy_value_to_string(ng_input.min_value)))
            if hasattr(ng_input, "max_value") and ng_input.max_value != 340282346638528859811704183484516925440.0:
                lines_to_write.append("%snew_input.max_value = %s\n" %
                                      (line_prefix, bpy_value_to_string(ng_input.max_value)))
            if hasattr(ng_input, "default_value") and ng_input.default_value != None and \
                    ng_input.default_value != 0.0 and \
                    not bpy_compare_to_value(ng_input.default_value, (0.0, 0.0, 0.0)) and \
                    not ( ng_input.bl_socket_idname == 'NodeSocketColor' and \
                          bpy_compare_to_value(ng_input.default_value, (0.0, 0.0, 0.0, 1.0)) ):
                lines_to_write.append("%snew_input.default_value = %s\n" %
                                      (line_prefix, bpy_value_to_string(ng_input.default_value)))
            if ng_input.hide_value:
                lines_to_write.append(line_prefix + "new_input.hide_value = True\n")
            # create new_input variable only if necessary, i.e. if input attribute values differ from default values
            if len(lines_to_write) > 0:
                out_text.write("%snew_input = new_node_group.inputs.new(type='%s', name=\"%s\")\n" %
                               (line_prefix, ng_input.bl_socket_idname, ng_input.name))
                for l in lines_to_write:
                    out_text.write(l)
            else:
                out_text.write("%snew_node_group.inputs.new(type='%s', name=\"%s\")\n" %
                               (line_prefix, ng_input.bl_socket_idname, ng_input.name))
        # write group outputs
        for ng_output in node_group.outputs:
            # collect lines to be written before writing, to allow for checking if input attributes need to be
            # written
            lines_to_write = []
            # write values for node group output min/max/default if needed
            if ng_output_min_max_def:
                # check/write the min, max, default, and 'hide value' data
                if hasattr(ng_output, "min_value") and ng_output.min_value !=-340282346638528859811704183484516925440.0:
                    lines_to_write.append("%snew_output.min_value = %s\n" %
                                          (line_prefix, bpy_value_to_string(ng_output.min_value)))
                if hasattr(ng_output, "max_value") and ng_output.max_value != 340282346638528859811704183484516925440.0:
                    lines_to_write.append("%snew_output.max_value = %s\n" %
                                          (line_prefix, bpy_value_to_string(ng_output.max_value)))
                if hasattr(ng_output, "default_value")and ng_output.default_value != None and \
                        ng_output.default_value != 0.0 and \
                        not bpy_compare_to_value(ng_output.default_value, (0.0, 0.0, 0.0)) and \
                        not ( ng_output.bl_socket_idname == 'NodeSocketColor' and \
                              bpy_compare_to_value(ng_output.default_value, (0.0, 0.0, 0.0, 1.0)) ):
                    lines_to_write.append("%snew_output.default_value = %s\n" %
                                          (line_prefix, bpy_value_to_string(ng_output.default_value)))
            if ng_output.hide_value:
                lines_to_write.append(line_prefix + "new_output.hide_value = True\n")
            if hasattr(ng_output, "attribute_domain") and ng_output.attribute_domain != "POINT":
                lines_to_write.append("%snew_output.attribute_domain = '%s'\n" %
                                      (line_prefix, ng_output.attribute_domain))
            if hasattr(ng_output, "default_attribute_name") and ng_output.default_attribute_name != "":
                lines_to_write.append("%snew_output.default_attribute_name = %s\n" %
                                      (line_prefix, ng_output.default_attribute_name))
            # create new_output variable only if necessary, i.e. if output attribute values differ from default
            # values
            if len(lines_to_write) > 0:
                out_text.write("%snew_output = new_node_group.outputs.new(type='%s', name=\"%s\")\n" %
                               (line_prefix, ng_output.bl_socket_idname, ng_output.name))
                for l in lines_to_write:
                    out_text.write(l)
            else:
                out_text.write("%snew_node_group.outputs.new(type='%s', name=\"%s\")\n" %
                               (line_prefix, ng_output.bl_socket_idname, ng_output.name))

        out_text.write(line_prefix + "tree_nodes = new_node_group.nodes\n")
    else:
        out_text.write(line_prefix + "tree_nodes = material.node_tree.nodes\n")
    if delete_existing:
        out_text.write(line_prefix + "# delete all nodes\n")
        out_text.write(line_prefix + "tree_nodes.clear()\n")
    out_text.write(line_prefix + "# create nodes\n")
    out_text.write(line_prefix + "new_nodes = {}\n")
    # set parenting order of nodes (e.g. parenting to frames) after creating all the nodes in the tree,
    # so that parent nodes are referenced only after parent nodes are created
    frame_parenting_text = ""
    # write info about the individual nodes
    for tree_node in mat.edit_tree.nodes:
        out_text.write("%s# %s\n" % (line_prefix, tree_node.bl_label))
        out_text.write("%snode = tree_nodes.new(type=\"%s\")\n" % (line_prefix, tree_node.bl_idname))
        ignore_attribs = []
        for attr in uni_attr_default_list:
            # Input Color node will write this value, so ignore it for now
            if tree_node.bl_idname == 'FunctionNodeInputColor' and attr == 'color':
                continue
            if hasattr(tree_node, attr):
                gotten_attr = getattr(tree_node, attr)
                # if write defaults is not enabled, and a default value is found, then skip the default value
                if not uni_node_options[WRITE_DEFAULTS_UNI_NODE_OPT] and gotten_attr == uni_attr_default_list[attr]:
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

                out_text.write("%snode.%s = %s\n" % (line_prefix, attr, bpy_value_to_string(gotten_attr)))
        # node with parent is special, this node is offset by their parent frame's location
        parent_loc = Vector((0, 0))
        if tree_node.parent != None:
            parent_loc = tree_node.parent.location
        # do rounding of location values, if needed, and write the values
        precision = uni_node_options[LOC_DEC_PLACES_UNI_NODE_OPT]
        loc_x = tree_node.location.x + parent_loc.x
        loc_y = tree_node.location.y + parent_loc.y
        out_text.write("%snode.location = (%0.*f, %0.*f)\n" % (line_prefix, precision, loc_x, precision, loc_y))
        # Input Color, this attribute is special because this node type's Color attribute is swapped - very strange!
        # (maybe a dinosaur left over from old versions of Blender)
        if tree_node.bl_idname == 'FunctionNodeInputColor':
            out_text.write("%snode.color = %s\n" % (line_prefix, bpy_value_to_string(tree_node.color)))
            ignore_attribs.append("color")

        write_filtered_attribs(out_text, line_prefix, tree_node, ignore_attribs)

        # get node input(s) default value(s), each input might be [ float, (R, G, B, A), (X, Y, Z), shader ]
        # TODO: this part needs more testing re: different node input default value(s) and type(s)
        input_count = -1
        for node_input in tree_node.inputs:
            input_count = input_count + 1
            if node_input.hide_value:
                continue
            value_str = get_node_io_value_str(node_input, uni_node_options[WRITE_LINKED_DEFAULTS_UNI_NODE_OPT])
            if value_str != None:
                out_text.write("%snode.inputs[%s].default_value = %s\n" % (line_prefix, str(input_count), value_str))
        # get node output(s) default value(s), each output might be [ float, (R, G, B, A), (X, Y, Z), shader ]
        # TODO: this part needs more testing re: different node output default value(s) and type(s)
        output_count = -1
        for node_output in tree_node.outputs:
            output_count = output_count + 1
            if tree_node.bl_idname not in NODES_WITH_WRITE_OUTPUTS:
                continue
            # always write the value, even if linked, because this node is special
            value_str = get_node_io_value_str(node_output, True)
            if value_str != None:
                out_text.write("%snode.outputs[%s].default_value = %s\n" % (line_prefix, str(output_count), value_str))

        out_text.write("%snew_nodes[\"%s\"] = node\n" % (line_prefix, tree_node.name))
        # save a reference to parent node for later, if parent node exists
        if tree_node.parent != None:
            frame_parenting_text = "%s%snew_nodes[\"%s\"].parent = new_nodes[\"%s\"]\n" % \
                                   (frame_parenting_text, line_prefix, tree_node.name, tree_node.parent.name)

    # do node parenting if needed
    if frame_parenting_text != "":
        out_text.write("%s# parenting of nodes\n%s\n" % (line_prefix, frame_parenting_text))
    # create links, keeping list of created links if needed
    out_text.write(line_prefix + "# create links\n")
    if keep_links:
        out_text.write(line_prefix + "new_links = []\n")
    if is_tree_node_group:
        out_text.write(line_prefix + "tree_links = new_node_group.links\n")
    else:
        out_text.write(line_prefix + "tree_links = material.node_tree.links\n")
    for tree_link in mat.edit_tree.links:
        flint = ""
        if keep_links:
            flint = "link = "
        out_text.write("%s%stree_links.new(new_nodes[\"%s\"].outputs[%d], new_nodes[\"%s\"].inputs[%d])\n" %
        (line_prefix, flint, tree_link.from_socket.node.name, get_output_num_for_link(tree_link),
         tree_link.to_socket.node.name, get_input_num_for_link(tree_link)))
        if keep_links:
            out_text.write(line_prefix + "new_links.append(link)\n")
    # created nodes are selected by default so deselect them
    out_text.write("%s# deselect all new nodes\n%sfor n in new_nodes.values(): n.select = False\n" %
                   (line_prefix, line_prefix))

    if is_tree_node_group:
        out_text.write(line_prefix + "return new_node_group\n")
    else:
        out_text.write(line_prefix + "return new_nodes\n")

    # add function call, if needed
    if make_into_function:
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

class PYREC_OT_RecordNodetree(Operator):
    bl_idname = "py_rec.node_editor_record_nodetree"
    bl_label = "Record Nodetree"
    bl_description = "Make Python text-block from current node tree"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        s = context.space_data
        if s.type == 'NODE_EDITOR' and s.node_tree != None and \
            s.tree_type in ('CompositorNodeTree', 'ShaderNodeTree', 'TextureNodeTree', 'GeometryNodeTree'):
            return True
        return False

    def execute(self, context):
        ntr = context.window_manager.py_rec.record_options.nodetree
        uni_node_options = {
            LOC_DEC_PLACES_UNI_NODE_OPT: ntr.write_loc_decimal_places,
            WRITE_DEFAULTS_UNI_NODE_OPT: ntr.write_default_values,
            WRITE_LINKED_DEFAULTS_UNI_NODE_OPT: ntr.write_linked_default_values,
            WRITE_ATTR_NAME_UNI_NODE_OPT: ntr.write_attrib_name,
            WRITE_ATTR_WIDTH_HEIGHT_UNI_NODE_OPT: ntr.write_attrib_width_and_height,
            WRITE_ATTR_SELECT_UNI_NODE_OPT: ntr.write_attrib_select,
        }
        text = create_code_text(context, ntr.num_space_pad, ntr.keep_links, ntr.make_function, ntr.delete_existing,
                                ntr.ng_output_min_max_def, uni_node_options)
        self.report({'INFO'}, "Nodetree recorded to Python in Text named '%s'" % text.name)
        return {'FINISHED'}
