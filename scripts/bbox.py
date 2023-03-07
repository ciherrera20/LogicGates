class Bbox():
    def __init__(self, *args):
        if len(args) == 1:
            self._bbox = args[0]
        elif len(args) == 2 or len(args) == 3:
            if len(args) == 2:
                xc, yc = 0, 0
                width, height = args
            else:
                (xc, yc), width, height = args
            self._bbox = (xc - width / 2, yc - height / 2, xc + width / 2, yc + height / 2)
        else:
            ValueError('Invalid arguments')
    
    @property
    def xc(self):
        return (self._bbox[0] + self._bbox[2]) / 2
    
    @property
    def yc(self):
        return (self._bbox[1] + self._bbox[3]) / 2

    @property
    def x1(self):
        return self._bbox[0]

    @property
    def y1(self):
        return self._bbox[1]
    
    @property
    def x2(self):
        return self._bbox[2]

    @property
    def y2(self):
        return self._bbox[3]

    @property
    def width(self):
        return (self.x2 - self.x1)

    @property
    def height(self):
        return (self.y2 - self.y1)
    
    @property
    def hwidth(self):
        return self.width / 2

    @property
    def hheight(self):
        return self.height / 2

    @property
    def center(self):
        return (self.xc, self.yc)

    @property
    def bbox(self):
        return self._bbox

    def pad(self, padx, pady):
        bbox = (self.x1 - padx, self.y1 - pady, self.x2 + padx, self.y2 + pady)
        return Bbox(bbox)
    
    def scalex(self, scalar):
        return Bbox(self.center, self.width * scalar, self.height)

    def scaley(self, scalar):
        return Bbox(self.center, self.width, self.height * scalar)

    def contains(self, x, y):
        return (self.x1 <= x and x <= self.x2) and (self.y1 <= y and y <= self.y2)

    def __getitem__(self, *args, **kwargs):
        return self._bbox.__getitem__(*args, *kwargs)
    
    def __setitem__(self, *args, **kwargs):
        return self._bbox.__setitem__(*args, *kwargs)
    
    def __add__(self, point):
        bbox = (self.x1 + point[0], self.y1 + point[1], self.x2 + point[0], self.y2 + point[1])
        return Bbox(bbox)

    def __sub__(self, point):
        bbox = (self.x1 - point[0], self.y1 - point[1], self.x2 - point[0], self.y2 - point[1])
        return Bbox(bbox)
    
    def __repr__(self):
        return str(self._bbox)