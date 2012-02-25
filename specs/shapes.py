"""Contrived API for test purposes"""

class Square(object):
    def __init__(self, length=None):
        self.set_length(length)
    
    def set_length(self, length):
        self.length = length
    
    def area(self):
        return self.length * self.length

class Rectangle(object):
    def __init__(self, width=None, length=None):
        self.set_width(width)
        self.set_length(length)
    
    def set_length(self, length):
        self.length = length
    
    def set_width(self, width):
        self.width = width
    
    def area(self):
        return self.length * self.width
    
class Triangle(object):
    def __init__(self, base=None, height=None):
        self.set_base(base)
        self.set_height(height)
    
    def set_base(self, base):
        self.base = base
    
    def set_height(self, height):
        self.height = height
    
    def area(self):
        return self.base * 0.5 * self.height

class Shapes(object):
    def __init__(self):
        self.shapes = []
    
    def add_shape(self, shape):
        self.shapes.append(shape)
    
    def total_area(self):
        return sum(s.area() for s in self.shapes)
        
    def create(self, key, *args, **kwargs):
        mapped = {'square' : Square, 'rectangle' : Rectangle, 'triangle' : Triangle}
        shape = mapped[key](*args, **kwargs)
        self.shapes.append(shape)
        return shape