Dowser for Python 3+
=========

This is a fork of Dowser, and these README is a copy of their site here: <http://aminus.net/wiki/Dowser>

Dowser is a CherryPy application that displays sparklines of Python object counts, and allows you to trace their referents. This helps you track memory usage and leaks in any Python program, but especially CherryPy sites.

Requirements
------------
+ CherryPy
+ Pillow (for the sparkline images)

Installation
------------

git clone git@github.com:nickburns2006/dowser-python3.git dowser

Testing
-------

```
python dowser\__init__.py, then browse to http://localhost:8080/
```

Screenshots
-----------

Mount dowser alongside your app via `cherrypy.tree.mount(dowser.Root(), '/dowser')`. Pick a different script name if you like. Then browse to it and you'll see the index page, with sparklines for all objects the 'gc' module can find. Hit 'refresh' every 5 seconds (`dowser.Root.period`) and each sparkline will add another pixel.

![Dowser Type Screenshot](http://www.aminus.net/attachment/wiki/Dowser/dowserindex.gif?format=raw "Dowser Type Screenshot")

You can view only objects above a given number of instances by supplying the 'floor' argument to this page; for example, to see only objects which have more than 10 instances, visit <http://localhost:8080/?floor=10>

Click on any TRACE link to see a list of all instances of the given class. Be careful with large lists--there's no paging feature yet.

![Dowser Trace Screenshot](http://www.aminus.net/attachment/wiki/Dowser/dowserlist.gif?format=raw "Dowser Trace Screenshot")

Click on one of the object id()'s to get more information about that object:

![Dowser Object Screenshot](http://www.aminus.net/attachment/wiki/Dowser/dowserobject.gif?format=raw "Dowser Object Screenshot")

Click the 'Show the entire tree' to see all the object's parents, grandparents, etc. Again, this tree can be quite large (but at least circular references are nipped in the bud):

![Dowser Entire Tree Screenshot](http://www.aminus.net/attachment/wiki/Dowser/dowsertree.gif?format=raw "Dowser Entire Tree Screenshot")
