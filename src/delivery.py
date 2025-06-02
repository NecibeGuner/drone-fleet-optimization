# delivery.py
class Delivery:
    def __init__(self, id, x, y, weight, priority, time_window=None, is_urgent=False):
        self.id = id
        # x ve y koordinatlarını bir _pos (veya pos) niteliği olarak saklayın
        # Python'da _ ile başlayan nitelikler genellikle "dahili" olduğu sinyalini verir.
        self._pos = (x, y) 
        self.weight = weight
        self.priority = priority
        self.time_window = time_window # (başlangıç_dakika, bitiş_dakika) tuple'ı
        self.is_urgent = is_urgent

    @property
    def x(self):
        """Teslimatın x koordinatını döndürür."""
        return self._pos[0]

    @property
    def y(self):
        """Teslimatın y koordinatını döndürür."""
        return self._pos[1]
    
    # İsteğe bağlı: Eğer dışarıdan Delivery objesinin x veya y koordinatlarını değiştirmek isterseniz,
    # setter'ları da ekleyebilirsiniz. Ancak bu durumda _pos'u da güncellemeniz gerekir.
    # Örneğin:
    # @x.setter
    # def x(self, value):
    #     self._pos = (value, self._pos[1])
    #
    # @y.setter
    # def y(self, value):
    #     self._pos = (self._pos[0], value)

    def __repr__(self):
        return f"Delivery(ID:{self.id}, Loc:({self.x:.1f},{self.y:.1f}), W:{self.weight:.1f}, P:{self.priority}, TW:{self.time_window}, Urgent:{self.is_urgent})"