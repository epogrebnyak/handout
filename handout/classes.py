import inspect        
import collections
from dataclasses import dataclass

class Block:
    pass

class ExtendableBlock(Block):
  def __init__(self, lines=None):
    self._lines = lines or []

  def add_line(self, line):
    self._lines.append(line)
    
  def __eq__(self, x):
    return self._lines == x._lines
    
  def __repr__(self):
     return("{}(lines={!r})".format(self.__class__.__name__, self._lines))  

    
# class Code(ExtendableBlock):
#    pass

# class Text(ExtendableBlock):
#    pass

@dataclass 
class Line:
    content : str
    exclude : bool = False

class Code(Line):
    pass

class Text(Line):
    pass

xs = [(Code, line) for line in text1.split('\n')]



text1 = "\n".join([
 "#comment"
,f"{TRIPLE_QUOTE}intext docsting{TRIPLE_QUOTE}"
,"def foo():"
,f"    {TRIPLE_QUOTE}docsting with offset{TRIPLE_QUOTE}"
,"    pass"
,f"{TRIPLE_QUOTE}"
,"Comment block"
,"(second line)"
,f"{TRIPLE_QUOTE}"
,"print(True):"])

def must_exclude(line):
    return ("handout" in line) and ("exclude" in line)
        
    
lines = text1.split('\n')
constr = Code
next_constr = Code
for line in lines:
    if constr == Code and line.startswith(TRIPLE_QUOTE):
        constr = Text
        next_constr = Text
        line = line[3:]
    if constr == Text and line.endswith(TRIPLE_QUOTE):
        line = line[:-3]
        next_constr = Code
            
    print (constr(line, must_exclude(line)))
    constr = next_constr


 



@dataclass
class Block:
    span: [int]
    lines: [str]
    
    def add(self, line):
        self.span.append(line.lineno)
        self.lines.append(line.content)
        
def make_block(line: Line):
    if isinstance(line, TextLine):
        constr = Text
    else:
        constr = Code
    return constr([line.lineno], [line.content]) 
    
class Code(Block):
    pass

class Text(Block):
    pass

TRIPLE_QUOTE = '"""'

def is_comment_start(lines, line):
    return isinstance(lines[-1], CodeLine) and line.startswith(TRIPLE_QUOTE)

def is_comment_end(lines, line):
    return isinstance(lines[-1], TextLine) and line.endswith(TRIPLE_QUOTE)

def split_text(text: str) -> [Line]:
    constr = CodeLine
    for lineno, line in enumerate(text.split('\n')):        
       lineno += 1  # Line numbers are 1-based indices.
       line = line.rstrip()
       is_start = is_comment_start(lines,line)
       is_end = is_comment_end(lines,line)
       print(lineno+1, line, is_start, is_end, we_are_inside_comment)
       if is_start and line.endswith(TRIPLE_QUOTE):
         line = line[3:-3]
         lines.append(TextLine(lineno,line))
         continue
       if is_start:
         we_are_inside_comment = True
         line = line[3:]
         lines.append(TextLine(lineno,line))
         continue
       if is_end:
         we_are_inside_comment = False  
         line = line[:-3]
         lines.append(TextLine(lineno,line))
         continue
       if not line.endswith('# handout: exclude'):                           
         constr = TextLine if we_are_inside_comment else CodeLine
         lines.append(constr(lineno,line))
    return lines[1:]




text1 = f"""#comment
{TRIPLE_QUOTE}intext docsting{TRIPLE_QUOTE}
def foo():
    {TRIPLE_QUOTE}docsting pass(){TRIPLE_QUOTE}
    pass
{TRIPLE_QUOTE}
Comment block
- second line
{TRIPLE_QUOTE}
print(True)
""" 
split_text(text=text1)    


def condense_lines(lines: [Line]) -> [Block]:
    result = []
    block = make_block(lines[0])
    for prev, line in zip(lines[:-1], lines[1:]):
        if type(line) is type(prev):
            block.add(line)
        else:
            result.append(block)
            block = make_block(line)
    result.append(block)
    return result    

condense_lines(split_text(text=text1))
        
        




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

def is_comment_start(content, line):
    return isinstance(content[-1], Code) and line.startswith(TRIPLE_QUOTE)

def is_comment_end(content, line):
    return isinstance(content[-1], Text) and line.endswith(TRIPLE_QUOTE):


def text_to_blocks_(text: str):
    for lineno, line in enumerate(text.split('\n')):        
       lineno += 1  # Line numbers are 1-based indices.
       line = line.rstrip()
       if is_comment_start(content, line):
         line = line[3:]
         content.append(Text())        
       if is_comment_end(content, line):
         line = line[:-3]
         content[-1].add_line(line)
         content.append(Code())
         continue
       if not line.endswith('# handout: exclude'):                           
         content[-1].add_line(line)


def text_to_blocks(text: str, blocks=collections.defaultdict(list)):
   content = [Code()] 
   for lineno, line in enumerate(text.split('\n')):        
      lineno += 1  # Line numbers are 1-based indices.
      line = line.rstrip()
      if is_comment_start(content, line):
        line = line[3:]
        content.append(Text())        
      if is_comment_end(content, line):
        line = line[:-3]
        content[-1].add_line(line)
        content.append(Code())
        continue
      if not line.endswith('# handout: exclude'):                           
        content[-1].add_line(line)
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
        
    def _get_current_line(self):
        return self._source.current_line()
    
    @property
    def _text(self):
        return self._source.text()
    
    def add_text(self, message, show=False):
        self._pending.append(Text(lines=[message]))
        if show:
            self.show()
        
    def show(self): 
        self._blocks[self._get_current_line()] += self._pending
        self._pending = []
        return text_to_blocks(text=self._text, blocks=self._blocks)

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