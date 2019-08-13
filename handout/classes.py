import inspect        
import collections

import script

def trace_init():
    # The loop walks through the call stack, skips 
    # internal entries in handout.py, and breaks at 
    # the first external Python file. We assume this 
    # is the file is where a Handout instance was created.
    for info in inspect.stack():
        if info.filename == __file__:
                continue
        break    
    return Source(info)
    
class Source:
    def __init__(self, info: inspect.FrameInfo):  
        self._info = info
        
    def filename(self) -> str:
       """Return path to a file where Handout object was created.""" 
       return self._info.filename
   
    def text(self) -> str:
        """Return contents of a file where Handout object was created."""
        module = inspect.getmodule(self._info.frame)
        return inspect.getsource(module)   
    
    def current_line(self) -> int:
        """Return current line in a file where Handout object was created."""
        for info in inspect.stack():
          if info.filename == self.filename():
            return info.lineno
        message = (
            "Handout object was created in '{}' and accessed in '{}'. The file in "
            "which you create the handout will be rendered. Thus, it only makes "
            "sense to add to the handout from this file or functions called from "
            "this file. You shou0ld not pass the handout object to a parent file.")
        raise RuntimeError(message.format(self.filename(), info.filename))


class Handout:
    def __init__(self, directory, title="Handout"):
        self._source = trace_init()
        self._pending = []
        self._blocks = collections.defaultdict(list) 
        
    def _get_current_line(self):
        return self._source.current_line()
    
    @property
    def _text(self):
        return self._source.text()
    
    def add_text(self, message, show=False):
        self._pending.append(script.Text(message))
        if show:
            self.show()
        
    def show(self): 
        self._blocks[self._get_current_line()] += self._pending
        self._pending = []
        return script.process(source_text=self._text, 
                              foreign_blocks=self._blocks)

class Exporter:    
    def __init__(self, directory, document):
        self._directory = directory
        self._document = document

    def render(self):
        raise NotImplementedError

    def save(self):
        raise NotImplementedError
    

class HtmlExporter(Exporter):        
    def _header(self):
        # will use self.doc.title        
        return "<html><body>"
        
    def _body(self): # can be templated
        return "\n".join([block.html() for block in self._document._pending]) 
    
    def _footer(self):
        return "</body></html>"

    def render(self):
        return "\n".join([self._header(), self._body(), self._footer()])

    def save(self):
        # html will save a ton of files - must work in a directory
        pass 

