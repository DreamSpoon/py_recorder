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

# returns tuple (True, "") on success, returns tuple (False, error_msg) on error (exception raised)
def exec_str(script_str, globs=None):
    try:
        if globs is None:
            exec(script_str)
        else:
            exec(script_str, globs)
    except:
        import traceback
        tb = traceback.format_exc()
        print(tb)   # print(tb) replaces traceback.print_exc()
        return (False, tb)
    return (True, "")
