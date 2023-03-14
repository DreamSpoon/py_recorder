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

BPY_DATA_TYPE_ITEMS = [
    ('actions', "Action", "", 1),
    ('armatures', "Armature", "", 2),
    ('brushes', "Brush", "", 3),
    ('cache_files', "Cache File", "", 4),
    ('cameras', "Camera", "", 5),
    ('collections', "Collection", "", 6),
    ('curves', "Curve", "", 7),
    ('fonts', "Font", "", 8),
    ('grease_pencils', "Grease Pencil", "", 9),
    ('images', "Image", "", 10),
    ('lattices', "Lattice", "", 11),
    ('libraries', "Library", "", 12),
    ('lights', "Light", "", 13),
    ('lightprobes', "Light Probe", "", 14),
    ('linestyles', "Line Style", "", 15),
    ('masks', "Mask", "", 16),
    ('materials', "Material", "", 17),
    ('meshes', "Mesh", "", 18),
    ('metaballs', "Meta Ball", "", 19),
    ('movieclips', "Movie Clip", "", 20),
    ('node_groups', "Node Group", "", 21),
    ('objects', "Object", "", 22),
    ('paint_curves', "Paint Curve", "", 23),
    ('palettes', "Palette", "", 24),
    ('particles', "Particle Settings", "", 25),
    ('shape_keys', "Shape Key", "", 26),
    ('scenes', "Scene", "", 27),
    ('screens', "Screen", "", 28),
    ('sounds', "Sound", "", 29),
    ('speakers', "Speaker", "", 30),
    ('textures', "Texture", "", 31),
    ('texts', "Text", "", 32),
    ('volumes', "Volume", "", 33),
    ('workspaces', "Work Space", "", 34),
    ('worlds', "World", "", 35),
]
if bpy.app.version >= (3,10,0):
    BPY_DATA_TYPE_ITEMS = BPY_DATA_TYPE_ITEMS + ('pointclouds', "Point Cloud", "", len(BPY_DATA_TYPE_ITEMS)+1)
if bpy.app.version >= (3,30,0):
    BPY_DATA_TYPE_ITEMS = BPY_DATA_TYPE_ITEMS + ('hair_curves', "Hair Curve", "", len(BPY_DATA_TYPE_ITEMS)+1)

def get_node_tree_material_name(node_tree):
    for m in bpy.data.materials:
        if m.node_tree == node_tree:
            return m.name
    return ""

def bpy_value_to_string(value):
    # write attribute, if it matches a known type
    if isinstance(value, str):
        return "\"%s\"" % value
    elif isinstance(value, bool):
        return "%s" % value
    elif isinstance(value, int):
        return "%d" % value
    elif isinstance(value, float):
        return "%f" % value
    # if attribute has a length then it is a Vector, Color, etc., so write elements of attribute in a tuple,
    # unless it is a set
    elif hasattr(value, '__len__'):
        vec_str = ""
        # is it a set?
        if isinstance(value, set):
            for item in value:
                if vec_str != "":
                    vec_str = vec_str + ", "
                sub_val_str = bpy_value_to_string(item)
                if sub_val_str is None:
                    vec_str = vec_str + "None"
                else:
                    vec_str = vec_str + sub_val_str
            return "{" + vec_str + "}"
        else:
            for val_index in range(len(value)):
                if vec_str != "":
                    vec_str = vec_str + ", "
                sub_val_str = bpy_value_to_string(value[val_index])
                if sub_val_str is None:
                    vec_str = vec_str + "None"
                else:
                    vec_str = vec_str + sub_val_str
            return "(" + vec_str + ")"
    # if the attribute's value has attribute 'name', then check if it is in a Blender built-in data list
    elif hasattr(value, 'name'):
        if isinstance(value, bpy.types.Action):
            return "bpy.data.actions.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Armature):
            return "bpy.data.armatures.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Brush):
            return "bpy.data.brushes.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.CacheFile):
            return "bpy.data.cache_files.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Camera):
            return "bpy.data.cameras.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Collection):
            return "bpy.data.collections.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Curve):
            return "bpy.data.curves.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.FreestyleLineStyle):
            return "bpy.data.linestyles.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.GeometryNodeTree):
            return "bpy.data.node_groups.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.GreasePencil):
            return "bpy.data.grease_pencils.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Image):
            return "bpy.data.images.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Lattice):
            return "bpy.data.lattices.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Library):
            return "bpy.data.libraries.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Light):
            return "bpy.data.lights.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.LightProbe):
            return "bpy.data.lightprobes.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Mask):
            return "bpy.data.masks.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Material):
            return "bpy.data.materials.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Mesh):
            return "bpy.data.meshes.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.MetaBall):
            return "bpy.data.metaballs.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.MovieClip):
            return "bpy.data.movieclips.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.NodeGroup):
            return "bpy.data.node_groups.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Object):
            return "bpy.data.objects.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.PaintCurve):
            return "bpy.data.paint_curves.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Palette):
            return "bpy.data.palettes.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.ParticleSettings):
            return "bpy.data.particles.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Scene):
            return "bpy.data.scenes.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Key):
            return "bpy.data.shape_keys.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Scene):
            return "bpy.data.scenes.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Screen):
            return "bpy.data.screens.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.ShaderNodeTree):
            if value.name in bpy.data.node_groups:
                return "bpy.data.node_groups.get(\"%s\")" % value.name
            else:
                return "bpy.data.materials.get(\"%s\").node_tree" % get_node_tree_material_name(value)
        elif isinstance(value, bpy.types.Sound):
            return "bpy.data.sounds.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Speaker):
            return "bpy.data.speakers.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Text):
            return "bpy.data.texts.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Texture):
            return "bpy.data.textures.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.VectorFont):
            return "bpy.data.fonts.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.Volume):
            return "bpy.data.volumes.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.WorkSpace):
            return "bpy.data.workspaces.get(\"%s\")" % value.name
        elif isinstance(value, bpy.types.World):
            return "bpy.data.worlds.get(\"%s\")" % value.name
        elif bpy.app.version >= (3,10,0) and isinstance(value, bpy.types.PointCloud):
            return "bpy.data.pointclouds.get(\"%s\")" % value.name
        elif bpy.app.version >= (3,30,0) and isinstance(value, bpy.types.Curves):
            return "bpy.data.hair_curves.get(\"%s\")" % value.name
    # return None, because attribute type is unknown
    else:
        return None
