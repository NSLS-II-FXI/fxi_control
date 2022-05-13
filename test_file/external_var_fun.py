a = 1
b = a + 2

def test_fun1(a, b):
    return a + b

def test_fun2(a, b):
    return a * b

class test_class():
    def __init__(self, a, b):
        self.a = a
        self.b = b
    def cal(self):
        return self.a - self.b