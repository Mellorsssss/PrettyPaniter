import copy
d = {'test':1,'test2':2}
a = copy.copy(d)
d['test'] = 2
print(d)
d = a
print(d)