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

from bpy.types import (PropertyGroup, Text)
from bpy.props import (BoolProperty, EnumProperty, PointerProperty, StringProperty)

class PYREC_PG_ContextExecOptions(PropertyGroup):
    exec_type: EnumProperty(name="Type", items=[ ("single_line", "Single Line", ""), ("textblock", "Text", "") ],
        default="single_line", description="Exec single line of code, or multi-line Text (see Text-Editor)")
    single_line: StringProperty(description="Single line of code to exec()")
    textblock: PointerProperty(description="Text to exec()", type=Text)
