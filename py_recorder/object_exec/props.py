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

from bpy.props import BoolProperty
from bpy.types import PropertyGroup

class PYREC_PG_ObjectExecOptions(PropertyGroup):
    run_as_text_script: BoolProperty(name="Run in Text Editor", description="If enabled then Python code from " +
        "Textblock / Text Object will be 'run as script' in Text Editor. If disabled then Python code will be " +
        "run in current context with exec()", default=False)
    run_auto_import_bpy: BoolProperty(name="Auto 'import bpy'", description="Automatically prepend line to script, " +
        "if needed, to prevent error: \"NameError: name 'bpy' is not defined\"", default=True)
    use_operator_functions: BoolProperty(name="Operator Functions", description="Use Operator functions ('invoke', " +
        "'draw', 'execute'), if found. Notes: Operator Functions are not available if 'Run in Text Editor', and " +
        "windows will not display if 'Batch Exec' is used; only 'execute' is run during 'Batch Exec'",
        default=True)
