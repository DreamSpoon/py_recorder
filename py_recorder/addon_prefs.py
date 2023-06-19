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

from bpy.types import (AddonPreferences, PropertyGroup)
from bpy.props import (BoolProperty, CollectionProperty, PointerProperty, StringProperty)

from .exec_panel import (append_exec_context_panel_all, remove_exec_context_panel_all)
from .preset.preset_prop import PYREC_PG_PresetTypeCollection

def set_draw_exec_context_panels(self, value):
    self["draw_context_exec"] = value
    if value == True:
        append_exec_context_panel_all()
    else:
        remove_exec_context_panel_all()

def get_draw_exec_context_panels(self):
    return self.get("draw_context_exec", False)

class PYREC_PG_LogAddonPrefs(PropertyGroup):
    enable_timestamp: BoolProperty(name="Timestamp", description="Prepend timestamp to each log entry")
    output_text_name: StringProperty(name="Log Text Name", description="Name of Text to receive log entries (see" \
        "builtin Text-Editor)")

class PYREC_PG_InterfaceAddonPrefs(PropertyGroup):
    draw_context_exec: BoolProperty(name="Context Exec", description="Exec panel for every available Context type, " \
        "to allow easy exec() of any code in any Context type", set=set_draw_exec_context_panels,
        get=get_draw_exec_context_panels)

class PYREC_AddonPreferences(AddonPreferences):
    bl_idname = __package__

    log: PointerProperty(type=PYREC_PG_LogAddonPrefs)
    interface: PointerProperty(type=PYREC_PG_InterfaceAddonPrefs)
    preset_collections: CollectionProperty(type=PYREC_PG_PresetTypeCollection)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Interface")
        box.prop(self.interface, "draw_context_exec")
        box = layout.box()
        box.label(text="Log")
        box.prop(self.log, "enable_timestamp")
        box.prop(self.log, "output_text_name")
