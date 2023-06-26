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

from numpy import ones as numpy_ones

from bpy.types import PropertyGroup
from bpy.props import (BoolProperty, BoolVectorProperty, IntProperty)

from ...version_bpy_data import ANIMDATA_BOOL_NAMES

class PYREC_PG_DriverRecordOptions(PropertyGroup):
    num_space_pad: IntProperty(name="Num Space Pad", description="Number of spaces to prepend to each " +
        "line of code output in text-block", default=4, min=0)
    make_function: BoolProperty(name="Make into Function", description="Add lines of Python code to " +
        "create runnable script (instead of just the bare essential code)", default=True)
    animdata_bool_vec: BoolVectorProperty(size=len(ANIMDATA_BOOL_NAMES),
                                           default=tuple(numpy_ones((len(ANIMDATA_BOOL_NAMES)), dtype=int)))
