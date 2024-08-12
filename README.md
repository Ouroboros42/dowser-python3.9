Dowser for Python 3+
=========

This is a fork of a fork of Dowser, and these README is a modified copy of their site here: <http://aminus.net/wiki/Dowser>

Dowser is a CherryPy application that displays sparklines of Python object counts, and allows you to trace their referents. This helps you track memory usage and leaks in any Python program, but especially CherryPy sites.

Requirements
------------
+ CherryPy
+ Pillow (for the sparkline images)

Installation
------------

`git clone` this repo,
`pip install <path-to-repo>`

Testing
-------

**TODO**

Screenshots
-----------

Run dowser alongside your process by using `app.MemoryApp` as a context manager.

You can view only objects above a given number of instances by supplying the 'floor' argument to this page; for example, to see only objects which have more than 10 instances, visit <http://localhost:8080/?floor=10>

Click on any TRACE link to see a list of all instances of the given class. Be careful with large lists--there's no paging feature yet.

Click on one of the object id()'s to get more information about that object.

Click the 'Show the entire tree' to see all the object's parents, grandparents, etc. Again, this tree can be quite large (but at least circular references are nipped in the bud).

