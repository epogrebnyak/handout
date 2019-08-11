import inspect        
import collections
from dataclasses import dataclass

class Block:
    pass

class ExtendableBlock(Block):
  def __init__(self, lines=None):
    self._lines = lines or []

  def append_line(self, line):
    self._lines.append(line)
    
  def __eq__(self, x):
    return self._lines == x._lines
    
  def __repr__(self):
     return("{}(lines={!r})".format(self.__class__.__name__, self._lines))  

    
class Code(ExtendableBlock):
   pass

class Text(ExtendableBlock):
   pass


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


TRIPLE_QUOTE = '"""'
def text_to_blocks(text: str, blocks=collections.defaultdict(list)):
   content = [Code()] 
   in_comment = False
   for lineno, line in enumerate(text.split('\n')):        
      lineno += 1  # Line numbers are 1-based indices.
      line = line.rstrip()
      if not in_comment and line.startswith(TRIPLE_QUOTE):
        line = line[3:]
        in_comment = True        
        content.append(Text(line))        
        continue
      if in_comment and line.endswith(TRIPLE_QUOTE):
        line = line[:-3]
        in_comment = False
        content[-1].append_line(line)
        content.append(Code())
        continue
      if not line.endswith('# handout: exclude'):
        content[-1].append_line(line)
      # Add other blocks for current line, if any found.
      blocks_ = blocks[lineno]
      if blocks_:
        for block in blocks_:
          content.append(block)
        content.append(Code())
   return content


assert text_to_blocks("abc\ndef") == [Code(['abc', 'def'])]
assert text_to_blocks("aaa", {1: [Code("img")]}) == [Code(lines=['aaa']), Code(lines='img'), Code(lines=[])] 


class Handout:
    def __init__(self, directory, title="Handout"):
        self._source = trace_init()
        self._pending = []
        self._blocks = collections.defaultdict(list) 
        
    def current_line(self):
        return self._source.current_line()
    
    def text(self):
        return self._source.text()
    
    def add_text(self, message, show=True):
        self._pending.append(Text(lines=[message]))
        if show:
            self.show()
        return self
        
    def flush(self):    
        self._blocks[self.current_line()] += self._pending
        self._pending = []
        return self
    
    def show(self): 
        self.flush()
        return text_to_blocks(text=self.text(), 
                              blocks=self._blocks)

@dataclass
class Message(Block):
  string: str

  def html(self):
     return '<pre class="message">' + self.string + '</pre>'
 
  def markdown(self):
     return self.string

  def latex(self):
     pass


#@dataclass
#class Document: # internal representation of exportable document contents
#    title: str
#    blocks: [Block]


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
    
# test message
assert Message('Some text').html() == '<pre class="message">Some text</pre>'

# test HtmlExporter
#doc1 = Document(title="My report")
#doc1.append(Message("This is line one"))
#doc1.append(Message("Another line here"))
#output1 = '<html><body>\n<pre class="message">This is line one</pre>\n<pre class="message">Another line here</pre>\n</body></html>'
#assert HtmlExporter(".", doc1).render() == output1 