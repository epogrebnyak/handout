# String -> [(Int, Line)] -> [(Int, Block)] -> [(Int, Block)] -> [Block]
import re
from typing import List, Dict
from dataclasses import dataclass


TRIPLE_QUOTE = '"""'

@dataclass 
class Line:
    """Represents single line from script soucre file."""    
    content : str

    def has_pragma(self, tag: str):
        found = re.search('#\s*handout:\s*{}'.format(tag), self.content)
        return (True if found else False)
                         
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

class TextBasedBlock(Block):
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


class Html(TextBasedBlock):
    pass

class Message(TextBasedBlock):
    pass

class Code(TextBasedBlock):
    pass

class Text(TextBasedBlock):
    pass

@dataclass
class GraphicBlock(Block):
    filename : str
    width: float = 1

class Image(GraphicBlock):
    pass

class Video(GraphicBlock):
    pass

Lines = Dict[int, Line]
UserBlocks = Dict[int, List[Block]]
Blocks = List[Block]


def split(text: str) -> Lines:
    result = {} 
    constr = CodeLine
    next_constr = CodeLine
    for lineno, line in enumerate(text.split('\n')):
        line = line.rstrip()
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


def purge_comment(line_dict: Lines) -> Lines:
    result = {}
    include = True
    for n, line in line_dict.items():        
        if line.has_pragma('exclude'):
            continue
        if line.has_pragma('start-exclude'):
            include = False
        if include:
            result[n] = line
        if line.has_pragma('end-exclude'):
            include = True
    return result


def merge(lines: Lines, user_blocks: UserBlocks) -> [Block]:    
    result = []
    previous_lineno = 0
    for lineno, line in lines.items():
        result.append(line.to_block())
        matching_blocks = [block for i, block in user_blocks.items()
                           if previous_lineno < i <= lineno]
        if matching_blocks:
            result.extend(matching_blocks)
        previous_lineno = lineno        
    return result


def sametype(a, b):
    return type(a) is type(b)


def collapse(xs: [Block]) -> [Block]:
    result = []
    xs.append(Block()) #force using last element in xs    
    a = xs[0]
    for b in xs[1:]:
       if sametype(a, b) and isinstance(a, TextBasedBlock):
           # We can further accumulate *a*.
           a.merge(b)
       else:
           result.append(a)
           a = b
    return result   

    
def get_blocks(source_text: str, user_blocks: UserBlocks) -> Blocks:
    lines = split(source_text)
    lines = purge_comment(lines)
    blocks = merge(lines, user_blocks)
    return collapse(blocks)


TC = '"""' 
source_text = "\n".join([
    TC + "Docstring text" + TC,
    "doc=Handout('tmp')",
    "doc.add_text('My comment')"
]) 
user_blocks = {3: [Message('My comment')]}
x = get_blocks(source_text, user_blocks)

def sample_text():
    return '\n'.join([
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
    ,'# handout: end-exclude'
    ,"print('I am back again)"]
    )


user_blocks = {7: [Text('abc'), Text('zzz')],
               8: [Html('<pre>foo</pre>')],
               9: [Image("pic.png")]}

source_text = sample_text()
assert get_blocks(source_text, user_blocks) == [
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
        Code(lines=['', "print('I am back again)"])
    ]