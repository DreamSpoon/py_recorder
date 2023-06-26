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

# Animation Data sources, where drivers can exist - with rows added, as needed, for each new version
# [
#     ( data_source_name, (attribute_name1, attribute_name2, ...) ),
# ]
ANIMDATA_SOURCES = [
    # TODO: add bpy.data.images? or add comment explaining absence of bpy.data.images
    # TODO: sort alphabetically?
    ( "Armature", ["armatures"] ),
    ( "Cache File", ["cache_files"] ),
    ( "Camera", ["cameras"] ),
    ( "Curve", ["curves"] ),
    ( "Grease Pencil", ["grease_pencils"] ),
    ( "Lattice", ["lattices"] ),
    ( "Light", ["lights"] ),
    ( "Light Probe", ["lightprobes"] ),
    ( "Linestyle", ["linestyles"] ),
    ( "Linestyle Nodes", ["linestyles", "node_tree"] ),
    ( "Mask", ["masks"] ),
    ( "Material", ["materials"] ),
    ( "Material Nodes", ["materials", "node_tree"] ),
    ( "Geometry Nodes / Node Group", ["node_groups"] ),
    ( "Shape Key", ["shape_keys"] ),
    ( "Mesh", ["meshes"] ),
    ( "Metaball", ["metaballs"] ),
    ( "Movie Clip", ["movieclips"] ),
    ( "Object", ["objects"] ),
    ( "Particle Settings", ["particles"] ),
    ( "Scene", ["scenes"] ),
    ( "Compositor Nodes", ["scenes", "node_tree"] ),
    ( "Speaker", ["speakers"] ),
    ( "Texture", ["textures"] ),
    ( "Texture Nodes", ["textures", "node_tree"] ),
    ( "Volume", ["volumes"] ),
    ( "World", ["worlds"] ),
    ( "World Material Nodes", ["worlds", "node_tree"] ),
]
if bpy.app.version >= (3,10,0):
    ANIMDATA_SOURCES.append( ( "Point Cloud", ["pointclouds"] ) )
if bpy.app.version >= (3,30,0):
    ANIMDATA_SOURCES.append( ( "Hair Curve", ["hair_curves"] ) )

# sort tuples alphabetically by first value in each tuple
def sort_tup(tup):
    return(sorted(tup, key = lambda x: x[0]))

# sort alphabetically by first value in each tuple
ANIMDATA_SOURCES = sort_tup(ANIMDATA_SOURCES)

def get_animdata_bool_names():
    names = []
    for dst in ANIMDATA_SOURCES:
        names.append(dst[0])
    return names

ANIMDATA_BOOL_NAMES = get_animdata_bool_names()

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
