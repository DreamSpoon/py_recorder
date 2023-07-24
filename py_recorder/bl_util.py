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

addons_module_name = []

def set_addon_module_name(name):
    addons_module_name.clear()
    addons_module_name.append(name)

def get_addon_module_name():
    return addons_module_name[0]

def get_next_name(name, collection):
    if name not in collection:
        return name
    # check if '.001' (and '.002', etc.) decimal ending should be removed before searching for unused 'next name'
    r = name.rfind(".")
    if r != -1 and r != len(name)-1:
        if name[r+1:].isdecimal():
            name = name[:r]
    # search for unused 'next name' in 999 possible names
    for n in range(1, 999):
        next_name = "%s.%s" % (name, str(n).zfill(3))
        if next_name not in collection:
            return next_name
    return None

# force screen to redraw, known to work in Blender 3.3+
def do_tag_redraw():
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D' or a.type == 'TEXT_EDITOR':
            for r in a.regions:
                r.tag_redraw()
