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

# returns dir(val) without duplicates (e.g. '__doc__' duplicates)
def get_dir(val):
    temp_dict = {}
    for attr in dir(val):
        temp_dict[attr] = True
    return temp_dict.keys()

def get_inspect_context_collection(context_name, inspect_context_collections):
    for coll in inspect_context_collections:
        if coll.name == context_name:
            return coll
    return None

def get_inspect_context_panel(panel_num, context_name, inspect_context_collections):
    coll = get_inspect_context_collection(context_name, inspect_context_collections)
    if coll != None:
        return coll.inspect_context_panels.get(str(panel_num))
    return None
