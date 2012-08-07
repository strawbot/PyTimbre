# Timbre written in Python	Robert Chapman III	Jul 30, 2011

# stack is a list with append to push and pop to pop

# declarations and settings
cellmask = 0xFFFFFFFF
CELLSIZE = 4
LINELENGTH = 80
MSIZE = 1000

# number conversions
def int2base(integer, base=10):
	import string
	if not integer: return '0'
	sign = 1 if integer > 0 else -1
	alphanum = string.digits + string.ascii_uppercase
	nums = alphanum[:base]
	res = ''
	integer *= sign
	while integer:
			integer, mod = divmod(integer, base)
			res += nums[mod]
	if base == 10:
		return ('' if sign == 1 else '-') + res[::-1]
	else:
		return res[::-1]

# states of interpretation
EXECUTING = 1
COMPILING = 2
BUILDING = 3

class Timbre(): # a Timbre interpreter
	def __init__(self):
		import sys, os
		self.state = EXECUTING
		self.dataStack = []
		self.returnStack = []
		self.dictionary = {}
		self.macros = {}
		self.compilers = {}
		self.dictionaries = [self.dictionary, self.macros, self.compilers]
		self.emptyDict()
		self.memory = [0]*MSIZE
		self.eol = '\n'
		self.output = sys.stdout.write
		self.ip = 0 # for macro execution
#		if sys.stdout.name == '<stdout>':
#			sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
#		def output(string):
#			print string
		self.firstAddress = 0
		self.basev = self.nextLocation()
		self.tib = [0]*LINELENGTH
		self.dp = self.firstAddress
		self.reset()

	def nextLocation(self, size=1): # allocation a location in dictionary
		a = self.firstAddress
		self.firstAddress += size
		return a
		
	def reset(self): # ...-	 reset all data sets
		del(self.dataStack[:])
		del(self.returnStack[:])
		self.emptyDict()
		self.dp = self.firstAddress
		self.decimal()
		self.inp = 0
		self.tib[self.inp] = 0
		self.state = EXECUTING

	def emptyDict(self):
		self.dictionary.clear()
		self.macros.clear()
		self.compilers.clear()
		dictionary = {
			#data stack
			'dup': self.dup,
			'drop': self.drop,
			'swap': self.swap,
			'over': self.over,
			'?dup': self.qdup,
			'sp!': self.spStore,
			#return stack
			'>r': self.tor,
			'r>': self.rfrom,
			'r': self.r,
			#operations
			'and': self.bitand,
			'or': self.bitor,
			'xor': self.xor,
			'not': self.bitnot,
			'shift': self.shift,
			'negate': self.negate,
			'+': self.plus,
			'-': self.minus,
			'/': self.slash,
			'mod': self.mod,
			'/mod': self.slashMod,
			'*': self.star,
			#compares
			'=': self.equals,
			'<': self.lessthan,
			'>': self.greaterthan,
			'u<': self.ulessthan,
			'u>': self.ugreaterthan,
			'abs': self.absv,
			'min': self.minv,
			'max': self.maxv,
			#memory
			'@': self.fetch,
			'!': self.store,
			'c@': self.cfetch,
			'c!': self.cstore,
			'+b': self.plusbits,
			'-b': self.minusbits,
			'cmove': self.cmove,
			'fill': self.fill,
			'erase': self.erase,
			#dictionary
			'here': self.here,
			'allot': self.allot,
			'c,': self.ccomma,
			',': self.comma,
			'find': self.find,
			'execute': self.execute,
			#output
			'emit': self.emit,
			'cr': self.cr,
			'count': self.count,
			'type': self.emits,
			'base': self.base,
			'hex': self.hexBase,
			'decimal': self.decimal,
			'.': self.dot,
			'.r': self.dotr,
			'.b': self.dotb,
			'.d': self.dotd,
			'.h': self.doth,
			'.s': self.dots,
		   # macro makers
		   'constant': self.constant,
		   'variable': self.variable,
		   ':': self.colon,
		   ']': self.startmacro,
		   #tools
			'words': self.words,
			'reset': self.reset}
		compilers = {
		   ';': self.semicolon,
		   '[': self.endmacro,
		   'literal': self.literal,
		   'ahead': self.ahead,
		   'if': self.ifThen,
		   'else': self.otherwise,
		   'endif': self.endif,
		   'begin': self.begin,
		   'again': self.again,
		   'while': self.whileThen,
		   'until': self.until,
		   'repeat': self.repeat,
		   'for': self.forDo,
		   'next': self.next,
		   'exit': self.exit,
		   "'": self.tick
		   }

		for key in dictionary.keys(): self.dictionary[key] = dictionary[key]
		for key in compilers.keys(): self.compilers[key] = compilers[key]
			

	# data stack activities
	def lit(self, n): # - n	 push a literal to the data stack
		self.dataStack.append(n)

	def drop(self): # n -  throw away the top data stack item
		del(self.dataStack[-1])

	def dup(self): # n - n n  make a copy of the top data stack item
		self.lit(self.dataStack[-1])

	def swap(self): # n m - m n	 swap top two items on the data stack
		self.dataStack[-1], self.dataStack[-2] = self.dataStack[-2], self.dataStack[-1]

	def over(self): # n m - n m n  copy 2nd data stack item to top of data stack
		self.lit(self.dataStack[-2])

	def qdup(self): # n - n n | - 0	 duplicate top data stack item if not 0
		if self.dataStack[-1]:
			self.dataStack.append(self.dataStack[-1])

	def spStore(self): # ... -	empty the data stack
		del(self.dataStack[:])

	# return stack activities
	def tor(self): # n -  (R - n  push the top item of the data stack onto the return stack
		self.returnStack.append(self.dataStack.pop())

	def rfrom(self): # - n	(R n -	move top item on return stack to data stack
		self.dataStack.append(self.returnStack.pop())

	def r(self): # - n	(R n - n  copy the top item of the return stack onto the data stack
		self.dataStack.append(self.returnStack[-1])

	# operations
	def bitand(self): # n m - p	 bitwise AND top two data stack items and leave on top
		tmp = self.dataStack.pop()
		self.dataStack[-1] &= tmp

	def bitor(self): # n m - p	bitwise OR top two data stack items and leave on top
		tmp = self.dataStack.pop()
		self.dataStack[-1] |= tmp

	def xor(self): # n m - p  bitwise XOR top two data stack items and leave on top
		tmp = self.dataStack.pop()
		self.dataStack[-1] ^= tmp

	def bitnot(self): # n - n'	invert all bits on the top data stack item
		self.dataStack[-1] = ~self.dataStack[-1]

	def shift(self): # n m - p	shift n by m bit left for minus and right for positive
		m = self.dataStack.pop()
		n = self.dataStack[-1]
		self.dataStack[-1] = n << m if m > 0 else n >> -m

	def negate(self): # n - -n	complement of top data stack item
		self.dataStack[-1] = -self.dataStack[-1]

	def plus(self): # n m - p  add top two data stack items and leave on top
		tmp = self.dataStack.pop()
		self.dataStack[-1] += tmp

	def minus(self): # n m - p	subtract top data stack item from next item and leave on top
		tmp = self.dataStack.pop()
		self.dataStack[-1] -= tmp

	def slash(self): # n m - p	divide next data stack item by top and leave on top
		tmp = self.dataStack.pop()
		self.dataStack[-1] /= tmp

	def mod(self): # n m - p  modulus next data stack item by top and leave on top
		tmp = self.dataStack.pop()
		self.dataStack[-1] %= tmp

	def slashMod(self): # n m - q r	 return divide and modulus from top item into next item
		t = self.dataStack[-1]
		n = self.dataStack[-2]
		self.dataStack[-1], self.dataStack[-2] = n/t, n%t

	def star(self): # n m - p  multiply next data stack item by top and leave on top
		tmp = self.dataStack.pop()
		self.dataStack[-1] *= tmp

	# comparison
	def equals(self): # n m - f	 leave a boolean on stack after equating top two data stack items
		tmp = self.dataStack.pop()
		self.dataStack[-1] = (self.dataStack[-1] == tmp)
   
	def lessthan(self): # n m - f  leave a boolean on stack indicating if next is less than top
		tmp = self.dataStack.pop()
		self.dataStack[-1] = (self.dataStack[-1] < tmp)
   
	def greaterthan(self): # n m - f  leave a boolean on stack indicating if next is greater than top
		tmp = self.dataStack.pop()
		self.dataStack[-1] = (self.dataStack[-1] > tmp)
   
	def ulessthan(self): # n m - f	leave a boolean on stack indicating if unsigned next is less than top
		tmp = self.dataStack.pop() & cellmask
		self.dataStack[-1] = ((self.dataStack[-1]&cellmask) < tmp)
   
	def ugreaterthan(self): # n m - f  leave a boolean on stack indicating if unsigned next is greater than top
		tmp = self.dataStack.pop() & cellmask
		self.dataStack[-1] = ((self.dataStack[-1]&cellmask) > tmp)
   
	def absv(self): # n - n|-n	top data stack item is made positive
		self.dataStack[-1] = abs(self.dataStack[-1])
   
	def minv(self): # n m - n|m	 leave minimum of top two stack items
		tmp = self.dataStack.pop()
		self.dataStack[-1] = min(self.dataStack[-1], tmp)
   
	def maxv(self): # n m - n|m	 leave maximum of top two stack items
		tmp = self.dataStack.pop()
		self.dataStack[-1] = max(self.dataStack[-1], tmp)
   
	# memory
	def memRead(self, a): # read n from memory address a
		m = CELLSIZE - 1
		return sum((self.memory[a+i]<<(8*(m-i))) for i in range(CELLSIZE))

	def memWrite(self, n, a): # write n to memory address a
		m = CELLSIZE - 1
		l = [(n/(2**((m-i)*8)) & 0xFF) for i in range(CELLSIZE)]
		self.memory[a:a+CELLSIZE] = l

	def fetch(self): # a - n  return contents of memory using top stack item as the address (processor sized)
		a = self.dataStack[-1]
		self.dataStack[-1] = self.memRead(self.dataStack[-1])
	
	def store(self): # n a -  store next into memory using top as address (processor sized)
		a, n = self.dataStack.pop(), self.dataStack.pop()
		self.memWrite(n, a)

	def cfetch(self): # a - c  return contents of memory using top stack item as the address (8 bit)
		self.dataStack[-1] = self.memory[self.dataStack[-1]] & 0xFF

	def cstore(self): # c a -  store next into memory using top as address (8 bit)
		a = self.dataStack.pop()
		self.memory[a] = self.dataStack.pop() & 0xFF

	def plusbits(self): # b a -	 turn on b bits at address a: 0b10001 em +b
		a = self.dataStack.pop()
		self.memory[a] |= self.dataStack.pop()

	def minusbits(self): # b a -  turn off b bits at address a: 0b10001 em -b
		a = self.dataStack.pop()
		self.memory[a] &= ~self.dataStack.pop()

	def cmove(self): # s d n --	 move n bytes from s to d
		n = self.dataStack.pop()
		d = self.dataStack.pop()
		s = self.dataStack.pop()
		self.memory[d:d+n] = self.memory[s:s+n]

	def fill(self): # d n p --	fill n bytes from d with p
		p = self.dataStack.pop() & 0xFF
		n = self.dataStack.pop()
		d = self.dataStack.pop()
		self.memory[d:d+n] = [p]*n

	def erase(self): # s n -  erase n bytes from s
		s = self.dataStack.pop()
		n = self.dataStack.pop()
		self.memory[s:s+n] = [0]*n

	# dictionary
	def here(self): # - a  return address of end of dictionary
		self.lit(self.dp)

	def allot(self): # n -	reserve n bytes after end of dictionary
		self.dp += self.dataStack.pop()

	def ccomma(self): # c -	 allocate and 1 byte and put value in it
		self.memory[self.dp] = self.dataStack.pop() & 0xFF
		self.dp += 1

	def comma(self, data=None): # n -	allocate 1 cell and put n into it
		if not data:
			data = self.dataStack.pop()
		self.memWrite(data, self.dp)
		self.dp += CELLSIZE

	def toHere(self, s):
		i = self.dp
		for c in s:
			self.memory[i] = ord(c)
			i += 1
		
	def atHere(self):
		s = ''
		i = self.dp
		n = self.memory[i]
		for j in range(i+1,i+n+1):
			s += chr(self.memory[j])
		return s

	# output
	def emit(self): # c - ) send c to output device
		self.output(chr(self.dataStack.pop()))
		
	def cr(self): # send end of line to output device
		self.output(self.eol)

	def count(self): # a - a' c	 leave first character and incremented address on stack
		top = self.dataStack[-1]
		self.dataStack[-1] += 1
		self.lit(self.memory[top])

	def emits(self): # a n -  output n characters starting at a
		n = self.dataStack.pop()
		a = self.dataStack.pop()
		s = ''
		for i in range(a, a+n):
			s = s + chr(self.memory[i])
		self.output(s)

	def base(self): # - a  return address of number radix
		self.lit(self.basev)

	def setBase(self, n): # set base for number conversion
		self.memory[self.basev] = n
		
	def getBase(self): # return base for number conversion
		return self.memory[self.basev]
		
	def hexBase(self): # interpret all following numbers as hex
		self.setBase(16)

	def decimal(self): # interpret all subsequent numbers as decimal
		self.setBase(10)

	def dot(self): # n -  print n in current number base
		n = self.dataStack.pop()
		s = ' '+int2base(n,self.getBase())
		self.output(s)
		
	def dotr(self): # m n -	 print m in right field of n digits
		n = self.dataStack.pop()
		m = self.dataStack.pop()
		s = int2base(m,self.getBase())
		self.output(s.rjust(n))

	def dotb(self): # n -  print n in binary
		n = self.dataStack.pop() & cellmask
		s = ''
		while True:
			s = ' ' + int2base(n&0xFF,2).zfill(8) + s
			n = n >> 8
			if n == 0: break
		self.output(s)
		
	def dotd(self): # n -  print n in decimal
		n = self.dataStack.pop()
		s = ' '+int2base(n,10)
		self.output(s)
		
	def doth(self): # n -  print n in hex
		n = self.dataStack.pop() & cellmask
		s = ' '+int2base(n,16)
		self.output(s)
		
	def dots(self): #  print out data stackc
		n = len(self.dataStack)
		self.output('%i stack items: '%n)
		if n > 10: n = 10
		for i in range(-n, 0):
			self.lit(self.dataStack[i])
			self.dot()

	# input
	def find(self, name=''): # - x	return tick of given name
		if not name:
			name = self.dataStack.pop()

		flag = COMPILING
		if name in self.dictionary.keys():
			self.lit(self.dictionary[name])
		elif name in self.macros.keys():
			self.lit(self.macros[name])
		elif name in self.compilers.keys():
			self.lit(self.compilers[name])
			flag = BUILDING
		else:
			self.lit(False)
		return flag

	def execute(self, tick=None): # x -	 use the top data stack item as a function call
		if tick:
			tick() # macros are made into callable routines using lambda
		else:
			self.dataStack.pop()()

	def skip(self, c=-1): # skip input equal to c
		if c == -1: c = self.datastack.pop() # allow two ways of calling
		while self.tib[self.inp] and self.tib[self.inp] == c:
			self.inp += 1

	def parse(self, c=-1): # parse characters from input till c or 0
		if c == -1: c = self.datastack.pop() # allow two ways of calling
		n, s = 0, ''
		while self.tib[self.inp] and self.tib[self.inp] != c:
			s += (self.tib[self.inp])
			self.inp += 1
		self.toHere(chr(len(s)) + s + chr(0))
		return s

	def word(self, c=-1): # c -	 parse characters up to c from input to here
		if c == -1: c = self.dataStack.pop() # allow two ways of calling
		self.skip(c)
		return self.parse(c)

	def abort(self, m = ''): # abort with a message
		raise Exception( self.atHere()+'<-eh?',m)

	def number(self, s=''): # convert a string to a number
		base = self.getBase()
		if not s: s = self.dataStack.pop()
		s = s.upper()

		def setBase(s): # check for 0b 0c 0x
			if len(s) < 3:
				return s
			if s[0:2] == '0B':
				self.setBase(2)
			elif s[0:2] == '0C':
				self.setBase(8)
			elif s[0:2] == '0X':
				self.setBase(16)
			else:
				return s
			return s[2:]

		def digits(s): # convert string to # in base
			base = self.getBase()
			n = 0
			for c in s:
				c = ord(c) - ord('0')
				if c > 9:
					c -= 7
				if c < 0  or  c > base:
					self.abort(' Digit conversion')
				n = n*base + c
			return n

		if s[0] == '-':
			negative = True
			s = s[1:]
		else:
			negative = False
		s = setBase(s)
		n = digits(s)

		self.setBase(base)

		if negative:
			self.lit(-n)
		else:
			self.lit(n)

	def executeCompile(self, tick, flag): # execute or compile by flag over state
		if flag > self.state:
			self.execute(tick)
		else:
			self.compile(tick)

	def interpret(self, s): # interpret a string of words
		# transfer string to tib
		i = self.inp = 0
		for c in s:
			self.tib[i] = c
			i += 1
		self.tib[i] = 0

		# parse tib and execute words
		while True:
			s = self.word(' ')
			if not s: return
			flag = self.find(s)
			tick = self.dataStack.pop()
			if tick:
				self.executeCompile(tick, flag)
			else:
				self.number(s)
				self.literal()
	
	def literal(self): # decide what to do with number on the stack
		if self.state == COMPILING:
			self.compile(lambda n = self.dataStack.pop(): self.lit(n))

	def compile(self, f): # compile a function in the dictionary
		self.memory[self.dp] = f
		self.dp += 1

	def tick(self): # return or literalize tick of following word
		if self.find(self.word(' ')):
			self.literal()
		else:
			self.abort()
		
	# macro makers
	def header(self): # create a header in the dictionary
		self.word(' ')
		s = ''
		i = self.dp+1
		while self.memory[i]:
			s += chr(self.memory[i])
			i += 1
		return s

	def create(self, a): # add a definition to the dictionary
		name = self.header()
		self.macros[name] = lambda a = a: self.lit(a) # creates a unique call for each macro

	def constant(self): # add a constant defintion to the dictionary
		self.create(self.dataStack.pop())

	def variable(self): # add a variable defintion to the dictionary
		self.create(self.dp)
		self.comma()
	
	def colon(self): # start creating a macro entry
		name = self.header()
		def colonii(ip):
			self.ip = ip
			while True:
				tick = self.memory[self.ip]
				if tick == 0:
					return
				self.ip += 1
#				print tick,self.ip,
				tick()
#				print self.ip
		self.macros[name] = lambda ip = self.dp: colonii(ip) # unique call for each macro
		self.startmacro()

	def semicolon(self): # terminate a macro entry
		self.endmacro()
		self.lit(0)
		self.comma()
	
	def startmacro(self): # enter macro making mode
		self.state = COMPILING
		
	def endmacro(self): # end macro making mode
		self.state = EXECUTING

	# branching and looping interpreters
	def toI(self): # n -
		self.returnStack.append(self.dataStack.pop())

	def iFrom(self): # - n
		self.lit(self.returnStack.pop())
	
	def branch(self): # branch to following address
		self.ip = self.memory[self.ip]

	def zeroBranch(self): # f - branch if f == 0
		if self.dataStack.pop() == 0:
			self.branch()
		else:
			self.ip += 1

	def minusBranch(self): # decrement and branch if not zero
		if self.returnStack[-1]:
			self.returnStack[-1] -= 1
			self.branch()
		else:
			self.returnStack.pop()
			self.ip += 1

	# Control flow
	def ahead(self): # - a
		self.compile(self.branch)
		self.here()
		self.compile(0)
		
	def ifThen(self): # - a
		self.compile(self.zeroBranch)
		self.here()
		self.compile(0)
	
	def endif(self): # a -
		self.memory[self.dataStack.pop()] = self.dp

	def otherwise(self): # a - a
		self.ahead()
		self.swap()
		self.endif()
	
	def begin(self): # - a
		self.here()

	def again(self): # a -
		self.compile(self.branch)
		self.compile(self.dataStack.pop())

	def whileThen(self): # a - a n
		self.ifThen()

	def repeat(self): # a n -
		self.swap()
		self.again()
		self.endif()
	
	def until(self): # a -
		self.compile(self.zeroBranch)
		self.compile(self.dataStack.pop())

	def forDo(self): # - a n
		self.compile(self.toI)
		self.ahead()
		self.here()
	
	def next(self): # a n -
		self.swap()
		self.endif()
		self.compile(self.minusBranch)
		self.compile(self.dataStack.pop())

	def exit(self): #
		self.compile(0)

	# tools
	def words(self, filter=''): # i:[pattern]  list all words in dictionary
		keys = self.dictionary.keys() + self.macros.keys() + self.compilers.keys()
		keys.sort()
		for key in keys:
			if key.find(filter) >= 0:
				self.output(' '+key)
		self.output('\n')

	def dump(self): # a n -	 dump n 16-byte rows of memory starting at address a
		def dotnb(field, digits, n, r): # print as base digits right placed in field
			self.output(int2base(n, r).zfill(digits).rjust(field))

		def dotn(field, digits, n): # print as hex digits right placed in field
			dotnb(field, digits, n, 16)

		n = self.dataStack.pop()
		a = self.dataStack.pop()
		self.output(' '*2*CELLSIZE)
		for i in range(a, a+16):
			dotn(3, 2, i)
		self.output('\n')
		for i in range(n):
			dotn(8, CELLSIZE*2, a)
			for j in range(a,a+16):
				dotn(3,2,self.memory[j])
			self.output(' ')
			for j in range(a,a+16):
				c = chr(self.memory[j])
				if c < ' ' or c > '~':
					self.output('.')
				else:
					self.output(c)
			a += 16
		self.output('\n')

