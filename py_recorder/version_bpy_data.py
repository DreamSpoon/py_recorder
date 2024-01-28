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
    ANIMDATA_SOURCES += [ ( "Point Cloud", ["pointclouds"] ) ]
if bpy.app.version >= (3,30,0):
    ANIMDATA_SOURCES += [ ( "Hair Curve", ["hair_curves"] ) ]
# sort alphabetically by first value in each tuple
ANIMDATA_SOURCES = sorted(ANIMDATA_SOURCES, key = lambda x: x[0])

# get names to show with 'enable data source' boolean values
ANIMDATA_BOOL_NAMES = [ dst[0] for dst in ANIMDATA_SOURCES ]

BPY_DATA_TYPE_ITEMS = [
    ('actions', "Action", ""),
    ('armatures', "Armature", ""),
    ('brushes', "Brush", ""),
    ('cache_files', "Cache File", ""),
    ('cameras', "Camera", ""),
    ('collections', "Collection", ""),
    ('curves', "Curve", ""),
    ('fonts', "Font", ""),
    ('grease_pencils', "Grease Pencil", ""),
    ('images', "Image", ""),
    ('lattices', "Lattice", ""),
    ('libraries', "Library", ""),
    ('lights', "Light", ""),
    ('lightprobes', "Light Probe", ""),
    ('linestyles', "Line Style", ""),
    ('masks', "Mask", ""),
    ('materials', "Material", ""),
    ('meshes', "Mesh", ""),
    ('metaballs', "Meta Ball", ""),
    ('movieclips', "Movie Clip", ""),
    ('node_groups', "Node Group", ""),
    ('objects', "Object", ""),
    ('paint_curves', "Paint Curve", ""),
    ('palettes', "Palette", ""),
    ('particles', "Particle Settings", ""),
    ('scenes', "Scene", ""),
    ('screens', "Screen", ""),
    ('shape_keys', "Shape Key", ""),
    ('sounds', "Sound", ""),
    ('speakers', "Speaker", ""),
    ('texts', "Text", ""),
    ('textures', "Texture", ""),
    ('volumes', "Volume", ""),
    ('window_managers', "Window Manager", ""),
    ('workspaces', "Work Space", ""),
    ('worlds', "World", ""),
    ]
if bpy.app.version >= (3,10,0):
    BPY_DATA_TYPE_ITEMS += [ ('pointclouds', "Point Cloud", "") ]
if bpy.app.version >= (3,30,0):
    BPY_DATA_TYPE_ITEMS += [  ('hair_curves', "Hair Curve", "") ]
# sort alphabetically by first value in each tuple
BPY_DATA_TYPE_ITEMS = sorted(BPY_DATA_TYPE_ITEMS,  key=lambda x: x[0] )

DATABLOCK_DUAL_TYPES = [
    (bpy.types.Action, "actions"),
    (bpy.types.Armature, "armatures"),
    (bpy.types.Brush, "brushes"),
    (bpy.types.CacheFile, "cache_files"),
    (bpy.types.Camera, "cameras"),
    (bpy.types.Collection, "collections"),
    (bpy.types.Curve, "curves"),
    (bpy.types.VectorFont, "fonts"),
    (bpy.types.GreasePencil, "grease_pencils"),
    (bpy.types.Image, "images"),
    (bpy.types.Lattice, "lattices"),
    (bpy.types.Library, "libraries"),
    (bpy.types.Light, "lights"),
    (bpy.types.LightProbe, "lightprobes"),
    (bpy.types.FreestyleLineStyle, "linestyles"),
    (bpy.types.Mask, "masks"),
    (bpy.types.Material, "materials"),
    (bpy.types.Mesh, "meshes"),
    (bpy.types.MetaBall, "metaballs"),
    (bpy.types.MovieClip, "movieclips"),
    (bpy.types.NodeGroup, "node_groups"),
    (bpy.types.Object, "objects"),
    (bpy.types.PaintCurve, "paint_curves"),
    (bpy.types.Palette, "palettes"),
    (bpy.types.ParticleSettings, "particles"),
    (bpy.types.ShapeKey, "shape_keys"),
    (bpy.types.Scene, "scenes"),
    (bpy.types.Screen, "screens"),
    (bpy.types.Sound, "sounds"),
    (bpy.types.Speaker, "speakers"),
    (bpy.types.Text, "texts"),
    (bpy.types.Texture, "textures"),
    (bpy.types.Volume, "volumes"),
    (bpy.types.WindowManager, "window_managers"),
    (bpy.types.WorkSpace, "workspaces"),
    (bpy.types.World, "worlds"),
]
if bpy.app.version >= (3,10,0):
    DATABLOCK_DUAL_TYPES += [ (bpy.types.PointCloud, "pointclouds") ]
if bpy.app.version >= (3,30,0):
    DATABLOCK_DUAL_TYPES += [ (bpy.types.Curves, "hair_curves") ]
