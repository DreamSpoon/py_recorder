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

from datetime import datetime as dt

import bpy

PREFS_ADDONS_NAME = "py_recorder"

def log_text_append(log_str):
    addon_prefs_log = bpy.context.preferences.addons[PREFS_ADDONS_NAME].preferences.log
    output_text_name = addon_prefs_log.output_text_name
    # use default name if custom name is not available
    if output_text_name == "":
        output_text_name = "py_rec_log"
    # get log Text, or create if needed
    text = bpy.data.texts.get(output_text_name)
    if text is None:
        text = bpy.data.texts.new(name=output_text_name)
    # set current/select line/character to end line/character of text, before writing 'log_str'
    end_line = len(text.lines) - 1
    end_char = len(text.lines[end_line].body) - 1
    text.cursor_set(end_line, character=end_char, select=False)
    if addon_prefs_log.enable_timestamp:
        date_time = dt.now().strftime("Exception date: %m/%d/%Y\nException time: %H:%M:%S")
        text.write("\n%s" % date_time)
    text.write("\n%s\n" % (log_str))
    return text

def log_text_name():
    addon_prefs_log = bpy.context.preferences.addons[PREFS_ADDONS_NAME].preferences.log
    output_text_name = addon_prefs_log.output_text_name
    # use default name if custom name is not available
    if output_text_name == "":
        return "py_rec_log"
    else:
        return output_text_name
