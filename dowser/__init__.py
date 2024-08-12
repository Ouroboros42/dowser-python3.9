import cgi
import html
import gc
import os
localDir = os.path.join(os.getcwd(), os.path.dirname(__file__))
from io import BytesIO
import sys
import threading
import time
from types import FrameType, ModuleType
from dataclasses import dataclass, astuple
from collections import defaultdict

from PIL import Image, ImageDraw

import cherrypy

from . import reftree, util

def get_repr(obj, limit=250):
    return html.escape(reftree.get_repr(obj, limit))

class _(object): pass
dictproxy = type(_.__dict__)

method_types = [type(tuple.__le__),                 # 'wrapper_descriptor'
                type([1].__le__),                   # 'method-wrapper'
                type(sys.getswitchinterval),         # 'builtin_function_or_method'
                type(cgi.FieldStorage.getfirst),    # 'instancemethod'
                ]

def url(path):
    try:
        return cherrypy.url(path)
    except AttributeError:
        return path


def template(name, **params):
    p = {'maincss': url("/main.css"),
         'home': url("/"),
         }
    p.update(params)
    return open(os.path.join(localDir, name)).read() % p

@dataclass
class TypeInfo:
    count: int = 0
    bytesize: int = 0

    def __iadd__(self, instance):
        self.count += 1
        self.bytesize += sys.getsizeof(instance)

    def __iter__(self):
        return iter(astuple(self))

def resolve_typename(typeobj: type):
    return typeobj.__qualname__

class Root:
    
    period = 5
    maxhistory = 300
    
    def __init__(self):
        self.history = defaultdict(lambda: self.empty_history(self.samples))
        self.samples = 0
        cherrypy.engine.subscribe('exit', self.stop)
        self.runthread = threading.Thread(target=self.start)
        self.runthread.start()

    def empty_history(self, length: int):
        return [TypeInfo()] * self.samples

    def start(self):
        self.running = True
        while self.running:
            self.tick()
            time.sleep(self.period)
    
    def tick(self):
        gc.collect()
        
        typeinfo = defaultdict(TypeInfo)

        for obj in gc.get_objects():
            info = typeinfo[type(obj)]
            info += obj
        
        for objtype, info in typeinfo.items():
            self.history[resolve_typename(objtype)].append(info)
        
        samples = self.samples + 1
        
        # Add dummy entries for any types which no longer exist
        for typename, hist in self.history.items():
            diff = samples - len(hist)
            if diff > 0:
                hist.extend(self.empty_history(diff))
        
        # Truncate history to self.maxhistory
        if samples > self.maxhistory:
            for typename, hist in self.history.items():
                hist.pop(0)
        else:
            self.samples = samples
    
    def stop(self):
        self.running = False
    
    def index(self, ref_floor=0, byte_floor=0):
        rows = []

        for typename, info_hist in sorted(self.history.items(), key=lambda kv: kv[1][-1].bytesize, reverse=True):
            min_refs, max_refs = util.minmax(info.count for info in info_hist)
            min_bytes, max_bytes = util.minmax(info.bytesize for info in info_hist)
            current_refs, current_bytes = info_hist[-1]

            if max_refs > int(ref_floor) and max_bytes > int(byte_floor):
                row = f"""
                    <div class="typecount">{html.escape(typename)}<br/>
                    Refs - Min: {min_refs} Cur: {current_refs} Max: {max_refs} <br/>
                    <img class="chart" src="{url(f'refchart/{typename}')}"/><br/>
                    Bytes - Min: {min_bytes} Cur: {current_bytes} Max: {max_bytes} <br/>
                    <img class="chart" src="{url(f'memchart/{typename}')}"/><br/>
                    <a href="{url(f'trace/{typename}')}">TRACE</a></div>
                """

                rows.append(row)
        return template("graphs.html", output="\n".join(rows))
    index.exposed = True
    
    def chart(self, typename: str, field: str):
        """Return a sparkline chart of the given type."""
        
        data = list(getattr(info, field) for info in self.history[typename])

        height = 20.0
        scale = height / max(data)
        im = Image.new("RGB", (len(data), int(height)), 'white')
        draw = ImageDraw.Draw(im)
        draw.line([(i, int(height - (v * scale))) for i, v in enumerate(data)],
                  fill="#009900")
        del draw
        
        f = BytesIO()
        im.save(f, "PNG")
        result = f.getvalue()
        
        cherrypy.response.headers["Content-Type"] = "image/png"
        return result

    def refchart(self, typename: str):
        return self.chart(typename, 'count')
    refchart.exposed = True

    def memchart(self, typename: str):
        return self.chart(typename, 'bytesize')
    memchart.exposed = True
    
    def trace(self, typename, objid=None):
        gc.collect()
        
        if objid is None:
            rows = self.trace_all(typename)
        else:
            rows = self.trace_one(typename, objid)
    
        return template("trace.html", output="\n".join(rows),
                        typename=html.escape(typename),
                        objid=str(objid or ''))
    trace.exposed = True
    
    def trace_all(self, typename):
        rows = []
        for obj in gc.get_objects():
            objtype = type(obj)
            if resolve_typename(objtype) == typename:
                rows.append("<p class='obj'>%s</p>"
                            % ReferrerTree(obj).get_repr(obj))
        if not rows:
            rows = ["<h3>The type you requested was not found.</h3>"]
        return rows
    
    def trace_one(self, typename, objid):
        rows = []
        objid = int(objid)
        all_objs = gc.get_objects()
        for obj in all_objs:
            if id(obj) == objid:
                objtype = type(obj)
                if resolve_typename(objtype) != typename:
                    rows = ["<h3>The object you requested is no longer "
                            "of the correct type.</h3>"]
                else:
                    # Attributes
                    rows.append('<div class="obj"><h3>Attributes</h3>')
                    for k in dir(obj):
                        v = getattr(obj, k)
                        if type(v) not in method_types:
                            rows.append('<p class="attr"><b>%s:</b> %s</p>' %
                                        (k, get_repr(v)))
                        del v
                    rows.append('</div>')
                    
                    # Referrers
                    rows.append('<div class="refs"><h3>Referrers (Parents)</h3>')
                    rows.append('<p class="desc"><a href="%s">Show the '
                                'entire tree</a> of reachable objects</p>'
                                % url("/tree/%s/%s" % (typename, objid)))
                    tree = ReferrerTree(obj)
                    tree.ignore(all_objs)
                    for depth, parentid, parentrepr in tree.walk(maxdepth=1):
                        if parentid:
                            rows.append("<p class='obj'>%s</p>" % parentrepr)
                    rows.append('</div>')
                    
                    # Referents
                    rows.append('<div class="refs"><h3>Referents (Children)</h3>')
                    for child in gc.get_referents(obj):
                        rows.append("<p class='obj'>%s</p>" % tree.get_repr(child))
                    rows.append('</div>')
                break
        if not rows:
            rows = ["<h3>The object you requested was not found.</h3>"]
        return rows
    
    def tree(self, typename, objid):
        gc.collect()
        
        rows = []
        objid = int(objid)
        all_objs = gc.get_objects()
        for obj in all_objs:
            if id(obj) == objid:
                objtype = type(obj)
                if resolve_typename(objtype) != typename:
                    rows = ["<h3>The object you requested is no longer "
                            "of the correct type.</h3>"]
                else:
                    rows.append('<div class="obj">')
                    
                    tree = ReferrerTree(obj)
                    tree.ignore(all_objs)
                    for depth, parentid, parentrepr in tree.walk(maxresults=1000):
                        rows.append(parentrepr)
                    
                    rows.append('</div>')
                break
        if not rows:
            rows = ["<h3>The object you requested was not found.</h3>"]
        
        params = {'output': "\n".join(rows),
                  'typename': html.escape(typename),
                  'objid': str(objid),
                  }
        return template("tree.html", **params)
    tree.exposed = True


try:
    # CherryPy 3
    from cherrypy import tools
    Root.main_css = tools.staticfile.handler(root=localDir, filename="main.css")
except ImportError:
    # CherryPy 2
    cherrypy.config.update({
        '/': {'log_debug_info_filter.on': False},
        '/main.css': {
            'static_filter.on': True,
            'static_filter.file': 'main.css',
            'static_filter.root': localDir,
            },
        })


class ReferrerTree(reftree.Tree):
    
    ignore_modules = True
    
    def _gen(self, obj, depth=0):
        if self.maxdepth and depth >= self.maxdepth:
            yield depth, 0, "---- Max depth reached ----"
            raise StopIteration
        
        if isinstance(obj, ModuleType) and self.ignore_modules:
            raise StopIteration
        
        refs = gc.get_referrers(obj)
        refiter = iter(refs)
        self.ignore(refs, refiter)
        thisfile = sys._getframe().f_code.co_filename
        for ref in refiter:
            # Exclude all frames that are from this module or reftree.
            if (isinstance(ref, FrameType)
                and ref.f_code.co_filename in (thisfile, self.filename)):
                continue
            
            # Exclude all functions and classes from this module or reftree.
            mod = getattr(ref, "__module__", "")
            if "dowser" in mod or "reftree" in mod or mod == '__main__':
                continue
            
            # Exclude all parents in our ignore list.
            if id(ref) in self._ignore:
                continue
            
            # Yield the (depth, id, repr) of our object.
            yield depth, 0, '%s<div class="branch">' % (" " * depth)
            if id(ref) in self.seen:
                yield depth, id(ref), "see %s above" % id(ref)
            else:
                self.seen[id(ref)] = None
                yield depth, id(ref), self.get_repr(ref, obj)
                
                for parent in self._gen(ref, depth + 1):
                    yield parent
            yield depth, 0, '%s</div>' % (" " * depth)
    
    def get_repr(self, obj, referent=None):
        """Return an HTML tree block describing the given object."""
        objtype = type(obj)
        typename = resolve_typename(objtype)
        prettytype = typename.replace("__builtin__.", "")
        
        name = getattr(obj, "__name__", "")
        if name:
            prettytype = "%s %r" % (prettytype, name)
        
        key = ""
        if referent:
            key = self.get_refkey(obj, referent)
        return ('<a class="objectid" href="%s">%s</a> '
                '<span class="typename">%s</span>%s<br />'
                '<span class="repr">%s</span>'
                % (url("/trace/%s/%s" % (typename, id(obj))),
                   id(obj), prettytype, key, get_repr(obj, 100))
                )
    
    def get_refkey(self, obj, referent):
        """Return the dict key or attribute name of obj which refers to referent."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if v is referent:
                    return " (via its %r key)" % k
        
        for k in dir(obj) + ['__dict__']:
            if getattr(obj, k, None) is referent:
                return " (via its %r attribute)" % k
        return ""
