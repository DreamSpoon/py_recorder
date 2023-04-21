# Py Recorder: Python record, run, and inspect add-on for Blender

[Download Latest Release](https://github.com/DreamSpoon/py_recorder/releases/latest)

Python integration with Blender is amazing!

And difficult - but not by design. Blender includes great features to make it easier to use Python in Blender:
  - Info context - switch Timeline area to Info, then see Python code generate when Suzanne is added:
    - 'bpy.ops.mesh.primitive_monkey_add(...'
  - Python Console - run any Python code immediately, easily test coding ideas
  - Text Editor - 'run script' button always available to test entire Python files
  - StackExchange has a website address just for (Blender/Python questions)[https://blender.stackexchange.com/]

WARNING: Python code can potentially contain malware, use at own risk
 - see [GPL License](https://github.com/DreamSpoon/py_recorder/LICENSE)
 - [Anti-Malware on Wikipedia](https://en.wikipedia.org/wiki/Malware#Antivirus_/_Anti-malware_software)

Python Recorder's functions add to any Python user's toolset in Blender:
  - inspect Blender's data in real-time, with ability to 'drill-down' to sub-attributes
    - 'drill-down' with arrays and collections by selecting number / name from dropdown list
  - copy/paste from Info context, with filters, to automatically remove non-Python / redundant lines
  - run Python code in any context with Py Exec, to avoid 'out-of-context' errors when running context-aware code
    - e.g. running code in Python Console area will not allow easy access to active Material being displayed in Node Editor area
	- solution: use Py Exec panel in Node Editor (e.g. Shader Node Editor), to run Python code in Node Editor context

Some ways that Blender stores and uses data can be mysterious to new Blender users, even if they know Python.
Problem:
  - how to access the location of each vertice in 'Cube' object?
  - why isn't it in bpy.data.objects['Cube'] ?
Solution:
  - use 'data' attribute, bpy.data.objects['Cube'].data - to get reference to Mesh, which is bpy.data.meshes['Cube']
  - type Mesh stores data for vertices, edges, etc.
    - *bpy.data.meshes['Cube']*
  - type Object stores data for location, rotation, scale, etc. - including links to other bpy.data collections
    - *bpy.data.objects['Cube']*

Py Inspect makes it easy to find attributes of bpy.data.objects['Cube'], drill down to 'data' attribute, see Mesh data.

# Installation
Download [latest release](https://github.com/DreamSpoon/py_recorder/releases/latest)

Start Blender, then look in menu near top of Blender window.

`Edit -> User Preferences -> Add-ons -> Install from File...`

Choose the downloaded PyRecorder release zip file and press the Install Addon button.

Enable the add-on while still in User Preferences menu
  - if the add-on is not already visible, then search add-ons for 'Python Recorder'

Once installed and enabled, the add-on can be found in these places:
  1) *3DView* window, tools menu on right side of 3D view window
  2) *Node Editor* window, tools menu on right side of node editor window
  3) *Drivers* window, the tools menu on right side of drivers editor window
  4) Right-click in *almost* any context to show right-click menu with 'Py Inspect' at bottom
  5) Py Exec is available in *almost* any context, to allow running code in that specific context
    - e.g. bpy.context.space_data is different in each Context type
	- fast way to test code in a specific context, without needing to create menu/button in a specific context

Each context has Python Recorder tabs to use its functions, look for panels with names that start with 'Py', e.g.:
  - 'Py Record Info' in 3DView -> Tools -> Tool
  - 'Py Record Drivers' in Drivers Editor -> Tool
  - 'Py Exec' in Geometry Node Editor -> Tool

# Usage Docs (Work In Progress)

## [General Info](docs/GENERAL_INFO.md)

# See Also
Blender
https://blender.org/

Blender Docs
https://docs.blender.org/

Python
https://python.org/

StackExchange (Blender Python code questions and answers)
https://blender.stackexchange.com/

If all else fails, type your question into a search engine (e.g. Google, Bing), preceded with 'blender python', example:
  - blender python create ui button
  - blender python addon template
  - blender python create mesh object

'Don't re-invent the wheel' - many addons already exist to do something and can be downloaded (not all are free!):

https://github.com/topics/blender-addon

https://github.com/topics/blender-plugin

https://github.com/agmmnn/awesome-blender

https://blendermarket.com/

https://discover.gumroad.com/?query=blender+addon
