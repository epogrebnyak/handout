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

class Block:
    pass

class ExtendableBlock(Block):
  def __init__(self, lines=None):
    self._lines = lines or []

  def add(self, line):
    self._lines.append(line)
    
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
    for lineno, block in foreign_blocks.items():        
        source_blocks[lineno].append(block)
    return source_blocks    
        

def walk(blocks):
    return [block for blocklist in blocks.values() for block in blocklist]


def separate(items):
    result = []
    block = [items[0]]
    for prev, item in zip(items[:-1], items[1:]):
        if isinstance(item, type(prev)):
            block.append(item)
        else:
            result.append(block)
            block = [item]
    result.append(block)        
    return result    


def collect(group):
    if isinstance(group[0], CodeLine):
        return Code([g.content for g in group])
    elif isinstance(group[0], TextLine):
        return Text([g.content for g in group])
    else:
        return group[0]
   
text1 = "\n".join([
     "#comment"
    ,f"{TRIPLE_QUOTE}intext docsting{TRIPLE_QUOTE}"
    ,"def foo():"
    ,f"    {TRIPLE_QUOTE}docsting with offset{TRIPLE_QUOTE}"
    ,"    pass"
    ,"doc.add_text(abc)"
    ,"#some code"
    ,"#here"
    ,f"{TRIPLE_QUOTE}"
    ,"Triple quoted string"
    ,"(another line)"
    ,f"{TRIPLE_QUOTE}"
    ,"print(True) #handout:exclude"])

split(text1)    
blocks = split(text1)
foreign_blocks1 = {6: Html(['<b>abc</b>'])}
xs1 = merge(split(text1), foreign_blocks1)
xs2 = walk(xs1)
xs3 = purge(xs2)    
xs4 = list(map(collect, separate(xs3)))

xs4