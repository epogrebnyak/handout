from handout.classes import Handout
"""
Sometext here
"""
doc = Handout("output")
doc.add_text("More text") # handout: exclude

print(doc.current_line(), 8) 
print(doc.text())
for item in doc.show():
    print(item)