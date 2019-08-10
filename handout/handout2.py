from dataclasses import dataclass

class Block:
    pass

@dataclass
class Message(Block):
  string: str

  def html(self):
     return '<pre class="message">' + self.string + '</pre>'
 
  def markdown(self):
     return self.string

  def latex(self):
     pass


@dataclass
class Document:
    title: str
    blocks: [Block]


class Exporter:    
    def __init__(self, directory, document):
        self._directory = directory
        self._document = document
    

class HtmlExporter(Exporter):        
    def header(self):
        # will use self.doc.title        
        return "<html><body>"
        
    def body(self): # can be templated
        return "\n".join([block.html() for block in self._document.blocks]) 
    
    def footer(self):
        return "</body></html>"

    def render(self):
        return "\n".join([self.header(), self.body(), self.footer()])

    def save(self):
        # html will save a ton of files - must work in a directory
        pass
    
# test message
assert Message('Some text').html() == '<pre class="message">Some text</pre>'

# test HtmlExporter
doc1 = Document(title="My report", blocks=[Message("This is line one"),
                                           Message("Another line here")])
output1 = '<html><body>\n<pre class="message">This is line one</pre>\n<pre class="message">Another line here</pre>\n</body></html>'
assert HtmlExporter(".", doc1).render() == output1 