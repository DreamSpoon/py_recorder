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

from ..exec_func import exec_get_exception
from ..log_text import log_text_append

def context_exec_single_line(single_line, enable_log):
    is_exc, exc_msg = exec_get_exception(single_line)
    if is_exc:
        if enable_log:
            log_text_append("Exception raised by Exec of single line:\n%s\nException:\n%s" % (single_line, exc_msg))
        return False
    return True

def context_exec_textblock(textblock, enable_log):
    is_exc, exc_msg = exec_get_exception(textblock.as_string())
    if is_exc:
        if enable_log:
            log_text_append("Exception raised by Exec of Text named: %s\n%s" % (textblock.name, exc_msg))
        return False
    return True
