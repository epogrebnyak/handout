import re
from dataclasses import dataclass

TRIPLE_QUOTE = '"""'

@dataclass 
class Line:
    """Represents single line from script soucre file."""    
    content : str

    def search_tag(self, tag: str):
        found = re.search('#\s*handout:\s*{}'.format(tag), self.content)
        return (True if found else False)
                         
    def must_exclude(self):
        return self.search_tag('exclude')

    def is_pragma_start(self):
        return self.search_tag('start-exclude')
                                 
    def is_pragma_end(self):
        return self.search_tag('end-exclude')

    def to_block(self):
        raise NotImplementedError                                   

class CodeLine(Line):
    def to_block(self):
        return Code(self.content)
        
class TextLine(Line):
    def to_block(self):
        return Text(self.content)


class Block:
    """Represents a node in report."""    
    pass

class ExtendableBlock(Block):
  def __init__(self, lines=None):
    if isinstance(lines, str):
        lines = [lines]
    self._lines = lines or []

  def append(self, line):
    self._lines.append(line)

  def merge(self, x): #x is ExtendableBlock
    self._lines = self._lines + x._lines

  def is_empty(self):
    return len(self._lines) == 0

  def __eq__(self, x):
    return self._lines == x._lines
    
  def __repr__(self):
     return '{}(lines={!r})'.format(self.__class__.__name__, self._lines) 


class Html(ExtendableBlock):
    pass

class Message(ExtendableBlock):
    pass

class Code(ExtendableBlock):
    pass

class Text(ExtendableBlock):
    pass

@dataclass
class GraphicBlock(Block):
    filename : str
    width: float = 1

class Image(GraphicBlock):
    pass

class Video(GraphicBlock):
    pass

def split(text: str) -> dict:
    result = {} 
    constr = CodeLine
    next_constr = CodeLine
    for lineno, line in enumerate(text.split('\n')):
        if constr == CodeLine and line.startswith(TRIPLE_QUOTE):
            constr = TextLine
            next_constr = TextLine
            line = line[3:]
        if constr == TextLine and line.endswith(TRIPLE_QUOTE):
            line = line[:-3]
            next_constr = CodeLine
        result[lineno+1] = constr(line)
        constr = next_constr
    return result 


def purge_comment(line_dict):
    result = {}
    include = True
    for n, line in line_dict.items():        
        if line.must_exclude():
            continue
        if line.is_pragma_start():
            include = False
        if include:
            result[n] = line
        if line.is_pragma_end():
            include = True
    return result
    

def to_blocks(line_dict):
     return {n:[line.to_block()] for n, line in line_dict.items()}    


def merge(source_line_dict: dict, foreign_blocks: dict):
    source_blocks = to_blocks(source_line_dict)
    for lineno, fblocks in foreign_blocks.items():
        for fblock in fblocks:            
           source_blocks[lineno].append(fblock)
    return source_blocks    
        

def walk(blocks):
    """Convert nested blocks to list of blocks."""
    return [block for blocklist in blocks.values() for block in blocklist]


def sametype(a, b):
    return type(a) is type(b)


def collapse(xs):
    result = []
    xs.append(Block()) #force using last element in xs    
    a = xs[0]
    for b in xs[1:]:
       if not sametype(a, b) or not isinstance(a, ExtendableBlock):
           # situation 1 - *a* cannot be extended or *a* type ended
           result.append(a)
           a = b 
           continue             
       if isinstance(a, ExtendableBlock) and sametype(a, b):
           # situation 2 - we can further accumulate *a*
           a.merge(b)
           continue          
    return result   

def process(source_text: str, foreign_blocks):
    # source-level    
    lines = split(source_text)
    lines = purge_comment(lines)
    # block-level
    xs = merge(lines, foreign_blocks)
    xs = walk(xs)
    xs = collapse(xs)
    return xs

def text():
    text_lines = [
    f"{TRIPLE_QUOTE}One-line docsting at start{TRIPLE_QUOTE}"
    ,"def foo():"
    ,f"    {TRIPLE_QUOTE}Docsting with offset{TRIPLE_QUOTE}"
    ,"    pass"
    ,""
    ,"doc = Handout('.')"    
    ,"doc.add_text('abc'); doc.add_text('zzz')"
    ,"doc.html('<pre>foo</pre>')"
    ,"doc.image('pic.png')" 
    ,"# Single comment in code"
    ,f"{TRIPLE_QUOTE}"
    ,"Triple quoted string"
    ,"(on several lines)"
    ,f"{TRIPLE_QUOTE}"
    ,"print(True) #handout:exclude"
    ,''
    ,'# handout: start-exclude'
    ,'a=1'
    ,"doc.add_text('won't print this')"
    ,'# comment - not in handout'
    ,f"{TRIPLE_QUOTE}Not in handout{TRIPLE_QUOTE}"
    ,'# handout: end-exclude']
    return '\n'.join(text_lines)


foreign_blocks1 = {7: [Text('abc'), Text('zzz')],
                   8: [Html('<pre>foo</pre>')],
                   9: [Image("pic.png")]}
   
ref = [
        Text(lines=['One-line docsting at start']),
        Code(lines=['def foo():', 
                    '    """Docsting with offset"""', 
                    '    pass', 
                    '',
                    "doc = Handout('.')",
                    "doc.add_text('abc'); doc.add_text('zzz')"]),
        Text(lines=['abc', 'zzz']),
        Code(lines=["doc.html('<pre>foo</pre>')"]),
        Html(lines=['<pre>foo</pre>']),
        Code(lines=["doc.image('pic.png')"]),
        Image(filename='pic.png'),
        Code(lines=['# Single comment in code']),
        Text(lines=['', 
                    'Triple quoted string', 
                    '(on several lines)', 
                    '']),
        Code(lines=['']),
        #Code(lines=['print(True) #handout:exclude'])
    ]

from itertools import zip_longest

text1 = text()
ms = process(text1, foreign_blocks1)    
try:
    assert ref == ms
except AssertionError:    
    for i, (m, r) in enumerate(zip_longest(ms, ref)):        
        try:
            flag = (m == r)
        except AttributeError:
            flag = False
        print(i, flag)    
        if not flag:
            print(" Result:", m)
            print("Compare:", r)
    print ("Lengths:", len(ms), len(ref))
       
small1 = [Image(filename='pic.png'),
 Code(lines=['# some code here']),
 Text(lines=[''])]    
assert collapse(small1) == [Image(filename='pic.png'), Code(lines=['# some code here']), Text(lines=[''])]


small2 = [Text(lines=['One-line docsting at start']),
  Code(lines=['def foo():']),
  Code(lines=['    pass']),
  ]
assert collapse(small2) == [Text(lines=['One-line docsting at start']), Code(lines=['def foo():', '    pass'])]

assert Line('... # handout: exclude').must_exclude() is True