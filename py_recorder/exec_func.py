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

exec_result = {}

# returns 3-tuple of (result value, exception, exception message)
#   result value: exec of pre_exec_str, then result value is evaluation of exec_str
#   exception: boolean is True if exception was raised
def exec_get_result(pre_exec_str, exec_str, globs=None, locs=None):
    if not isinstance(exec_str, str) or exec_str == "":
        return None, True, "Invalid exec() string"
    # delete previous result if it exists
    if exec_result.get("ex_result_val") != None:
        del exec_result["ex_result_val"]
    if not isinstance(pre_exec_str, str):
        pre_exec_str = ""
    full_exec_str = "%s\nglobal exec_result\nexec_result['ex_result_val'] = %s" % (pre_exec_str, exec_str)
    is_exc, exc_msg = exec_get_exception(full_exec_str, globs, locs)
    if is_exc:
        return None, True, exc_msg
    return exec_result["ex_result_val"], False, None

# returns 2-tuple of (exception, exception message)
#   exception: boolean is True if exception was raised
def exec_get_exception(exec_str, globs=None, locs=None):
    try:
        if globs != None and locs != None:
            exec(exec_str, globs, locs)
        elif globs != None:
            exec(exec_str, globs)
        elif locs != None:
            exec(exec_str, None, locs)
        else:
            exec(exec_str)
        return False, None
    except:
        import traceback
        return True, traceback.format_exc()
