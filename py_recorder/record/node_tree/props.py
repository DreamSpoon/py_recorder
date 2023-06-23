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

from bpy.types import PropertyGroup
from bpy.props import (BoolProperty, IntProperty)

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
