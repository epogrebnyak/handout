from handout.classes import Handout
"""Sometext here"""

"""starts
Multiline
comment
end"""

doc = Handout("output")
doc.add_text("More text") 
"""it is a comment"""
print(1) # handout: exclude

print(doc.current_line(), 8) 
print(doc.text())
for item in doc.show():
    print(item)