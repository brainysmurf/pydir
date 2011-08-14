class compare:
      def __init__(self, name):
      	  self.name = name

      def __eq__(self, what):
          return self.name == what.name

c = compare('hi')
d = compare('hello')
e = compare('hi')

if c in [d, e]:
    print('success')
else:
    print('whoa')
