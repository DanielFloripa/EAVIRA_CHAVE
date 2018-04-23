from copy import deepcopy


class Master(object):
    is_Master = "true"
    def __init__(self, nome):
        self.nome = nome

    def get_nome(self):
        return self.nome

    def change_nome(self, novo_nome):
        self.nome = novo_nome

    def __repr__(self):
        return repr("This is a class "+self.__class__.__name__+" @"+self.nome)

class Objects(Master):
    def __init__(self, result, obj_soma, nome=None, master="def"):
        Master.__init__(self, nome)
        Master.is_Master = master
        self.somas = obj_soma
        self.result = result

    def get_nomeM(self):
        return Master.get_nome(self)
        #return str(super(Soma, self).get_nome()+" override Obj")

    def set_somas(self, somas):
        self.somas = somas

    def get_somas(self):
        return self.somas


class Soma(Master):
    def __init__(self, a, b, last_result=None, nome=None):
        Master.__init__(self, nome)
        self.a = a
        self.b = b
        self.last_result = last_result
        self.results = []

    def get_nomeM(self):
        return Master.get_nome(self)

    def set_results(self, result):
        self.results.append(result)

    def get_results(self):
        return self.results

    def soma(self, a, b):
        self.set_results(a + b)
        return self.get_results()

import time

if __name__ == '__main__':
    count = 0
    start = time.time()
    while count < 24531071:
        m = Master("MASTER")
        #print "m: " + m.is_Master
        s = Soma(2, 3, 0, "SOMA")
        #print "m: " + m.is_Master + ", s: " + s.is_Master
        ss = deepcopy(s)
        o = Objects(0, ss, "OBJECTS")
        #print "m: " + m.is_Master + ", o: " + o.is_Master + ", s: " + s.is_Master
        args = (0, s, "NEW_OBJECTS", "Im not master")
        oo = Objects(*args)
        count = count + 1
    elapsed = time.time() - start
    print elapsed, count

    print "m: " + m.is_Master + ", o: " + o.is_Master + ", s: " + s.is_Master + ", oo: " + oo.is_Master
    s.is_Master = "maybe true"
    print "m: " + m.is_Master + ", o: " + o.is_Master + ", s: " + s.is_Master + ", oo: " + oo.is_Master
    print m.get_nome(), o.get_nomeM(), s.get_nomeM()
    print o.get_somas().get_results()
    print s.get_results()
    print s.soma(4, 6)
    print s.get_results()
    print "object" + str(o.get_somas().get_results())
    print "object" + str(o.get_somas().soma(100, 200))
    s.change_nome("Novo_SOMA")
    m.change_nome("NOVO MASTER")
    print s.soma(10, 20)
    print s.soma(40, 60)
    print "object" + str(o.get_somas().get_results())
    print m.get_nome(), o.get_nomeM(), s.get_nomeM()
