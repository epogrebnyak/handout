import re
from dataclasses import dataclass

TRIPLE_QUOTE = '"""'

@dataclass 
class Line:
    content : str

class CodeLine(Line):
    pass

class TextLine(Line):
    pass

class UserBlock:
    pass

class Block:
    pass
  
    def is_empty (self):
        raise NotImplementedError

class ExtendableBlock(Block, UserBlock):
  def __init__(self, lines=None):
    if isinstance(lines, str):
        lines = [lines]
    self._lines = lines or []

  def append(self, line):
    self._lines.append(line)

  def extend_with(self, x):
    self._lines = self._lines + x._lines

  def is_empty(self):
      return len(self._lines) == 0

  def __eq__(self, x):
    return self._lines == x._lines
    
  def __repr__(self):
     return("{}(lines={!r})".format(self.__class__.__name__, self._lines))  


class Html(ExtendableBlock):
    pass

class Code(ExtendableBlock):
    pass

class Text(ExtendableBlock):
    pass

@dataclass
class Image(UserBlock):
    filename : str

PRAGMA = re.compile(r'(#\s*handout:\s*exclude)')

def has_pragma(line):
    return True if PRAGMA.search(line) else False

assert PRAGMA.search('...#handout:    exclude')
assert has_pragma('... #handout:    exclude')
              
                    
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
        result[lineno+1] = [constr(line)]
        constr = next_constr
    return result 

def must_exclude(item):
    try: 
        return (not item.content) or has_pragma(item.content)
    except AttributeError:
        return False
    
def purge(items):
    return [x for x in items if not must_exclude(x)]


def merge(source_blocks: dict, foreign_blocks: dict):
    for lineno, fblocks in foreign_blocks.items():
        for fblock in fblocks:            
           source_blocks[lineno].append(fblock)
    return source_blocks    
        

def walk(blocks):
    return [block for blocklist in blocks.values() for block in blocklist]


def line_to_block(item):
    if isinstance(item, CodeLine):
        return Code([item.content])
    elif isinstance(item, TextLine):
        return Text([item.content])
    else:
        return item

def sametype(a, b):
    return type(a) is type(b)

def collapse(xs):
    result=[]
    xs = list(xs)
    xs.append(Block()) #force using last element in xs    
    a = xs[0]
    for b in xs[1:]:
       if not sametype(a, b) or not isinstance(a, ExtendableBlock):
           # situation 1 - *a* cannot be extended or *a* type ended
           result.append(a)
           a = b 
           continue             
       if isinstance(a, ExtendableBlock) and sametype(a, b):
           # situation 2 - can accumulate *a*
           a.extend_with(b)
           continue          
    return result   

def process(source_text: str, foreign_blocks):
    xs = merge(split(source_text), foreign_blocks)
    xs = walk(xs)
    xs = list(map(line_to_block, xs))
    xs = collapse(xs)
    return xs

text1 = "\n".join([
    f"{TRIPLE_QUOTE}one-line docsting at start{TRIPLE_QUOTE}"
    ,"def foo():"
    ,f"    {TRIPLE_QUOTE}docsting with offset{TRIPLE_QUOTE}"
    ,"    pass"
    ,"doc = Handout('.')"    
    ,"doc.add_text('abc'); doc.add_text('def'); doc.html('<pre>foo</pre>')"
    ,"# some code here"
    ,f"{TRIPLE_QUOTE}"
    ,"Triple quoted string"
    ,"(on several lines)"
    ,f"{TRIPLE_QUOTE}"
    ,"print(True) #handout:exclude"])

foreign_blocks1 = {6: [Text('abc'), Text('def'), Html('<pre>foo</pre>'), Image("pic.png")]}
xs = merge(split(text1), foreign_blocks1)
xs = walk(xs)
xs = list(map(line_to_block, xs))
ms = process(text1, foreign_blocks1)
    
ref = [
        Text(lines=['one-line docsting at start']),
        Code(lines=['def foo():', 
                    '    """docsting with offset"""', 
                    '    pass', 
                    "doc = Handout('.')",
                    "doc.add_text('abc'); doc.add_text('def'); doc.html('<pre>foo</pre>')"
                    ]),
        Text(lines=['abc', 'def']),
        Html(lines=['<pre>foo</pre>']),
        Image(filename='pic.png'),
        Code(lines=['# some code here']),
        Text(lines=['', 
                    'Triple quoted string', 
                    '(on several lines)', 
                    '']),
        Code(lines=['print(True) #handout:exclude'])
    ]

assert ref == ms
       
small1 = [Image(filename='pic.png'),
 Code(lines=['# some code here']),
 Text(lines=[''])]    
assert collapse(small1) == [Image(filename='pic.png'), Code(lines=['# some code here']), Text(lines=[''])]


small2 = [Text(lines=['one-line docsting at start']),
  Code(lines=['def foo():']),
  Code(lines=['    pass']),
  ]
assert collapse(small2) == [Text(lines=['one-line docsting at start']), Code(lines=['def foo():', '    pass'])]
