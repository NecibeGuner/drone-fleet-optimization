import pytest
from astar import astar

# Test fonksiyonları
def test_zero_distance():
    assert astar((1,1),(1,1), None, type("D",( ),{"pos":(1,1),"weight":1,"priority":1})(), [], None) == [(1,1)]

def test_simple_path():
    D = type("D",( ),{"__init__":lambda s,pos: setattr(s,"pos",pos) or setattr(s,"weight",1) or setattr(s,"priority",1)})
    path = astar((0,0),(1,1), None, D((1,1)), [], None, max_x=2, max_y=2)
    assert path == [(0,0),(1,0),(1,1)] or path == [(0,0),(0,1),(1,1)]

def test_blocked_path():
    # tüm grid no-fly zone haline getir
    class Z:
        def __init__(self): self.coordinates=[(0,0),(2,2)]; self.active_time=("00:00","23:59")
        def is_active(self,_): return True
    res = astar((0,0),(2,2), None, type("D",( ),{"pos":(2,2),"weight":1,"priority":1})(), [Z()], None, max_x=2, max_y=2)
    assert res is None

if __name__=="__main__":
    pytest.main()
