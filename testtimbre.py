# TDD for Timbre  Robert Chapman III  Jul 30, 2011

'''
test harness
 o context setting
 o environment testing
 o truth statement to run after test - just testing an int doesn't work for all cases
   - it is more general to have a general task which returns true after performing
     function specific tasks. This keeps the test harness general yet flexible.
 o diagnostic statement to run if failed. often when a fail occurs it kicks off
   a debugging task. by examining the details of the failure, it helps to point
   a finger at the faulty source or test code without any debugging.
 '''
from timbre import Timbre, int2base

passed = failed = 0

class capture(): # capture output to check it
    def __init__(me):
        me.empty()

    def empty(me):
        me.outs = ''

    def __call__(me,string): # is used for write
        me.outs += string

def runDiagnostic(t, diagnostic):
    if diagnostic: exec diagnostic

def testTimbre():
    t = Timbre()
    ds = t.dataStack
    rs = t.returnStack
    di = t.dictionary
    me = t.memory

    def nothing():
        pass

    def test(function=nothing, dstack=(), stacks=(0,0), d=(), r=(),
             rstack=(), arg=(), test=0, mem=(), truth='True', diagnostic='None',
             post=None):
        global passed, failed
#        exec diagnostic

        def setup(dstack, rstack):
            if type(dstack) == type(()):
                for i in dstack: ds.append(i)
            else: ds.append(dstack)

            if type(rstack) == type(()):
                for i in rstack: rs.append(i)
            else: rs.append(rstack)

        def runTest(arg, stacks, d, r):
            if arg: function(arg)
            else: function()

            if (len(ds), len(rs)) != stacks:
                raise Exception('Expected:',stacks,'got:',len(ds),len(rs))

            if d and d != ds: raise Exception('Expected:',d,'got:',ds)

            if r and r != rs: raise Exception('Expected:',r,'got:',rs)

            if mem and me[mem[0]] != mem[1]:
                 raise Exception('Expected:',mem[1],'got:',me[mem[0]])

        def teardown(post):
            t.reset()
            if post: post()
        
        try:
            setup(dstack, rstack)
            runTest(arg, stacks, d, r)
            if truth:
                if not eval(truth): raise Exception('false truth')
            passed += 1
        except Exception as e:
            failed += 1
            testn = ''
            if test:  testn = ' test '+str(test)
            print 'testing',function.__name__,'failed'+testn+'.',e
#            if diagnostic: exec diagnostic
            runDiagnostic(t, diagnostic)
            if t.output.outs: print 'output:',t.output.outs
        finally:
            teardown(post)

    test() # test test with defaults

    print 'Test data stack:'
    test(t.lit,(),(1,0),[5],arg=5)
    test(t.lit,5,(2,0),[5,4],arg=4)
    test(t.swap,(5,4),(2,0),[4,5])
    test(t.dup,(4,5),(3,0),[4,5,5])
    test(t.drop,(4,5,5),(2,0))
    test(t.over,(4,5),(3,0),[4,5,4])
    test(t.qdup,1,(2,0),[1,1])
    test(t.qdup,0,(1,0),[0])
    test(t.spStore,(1,2,3,5),(0,0))

    print 'Test return stack:'
    test(t.tor,6,(0,1),[],[6])
    test(t.r,(),(1,1),[6],[6],rstack=6)
    test(t.rfrom,5,(2,0),[5,6],[],rstack=6)

    print 'Test operations:'
    test(t.bitand,(0xC,0x5),(1,0),[4])
    test(t.bitor,(4,0x9),(1,0),[0xd])
    test(t.xor,(0xd,-1,),(1,0),[~0xd])
    test(t.bitnot,~0xD,(1,0),[0xd])
    test(t.negate,0xD,(1,0),[-0xd])
    test(t.plus,(0xD,-0xD),(1,0),[0])
    test(t.minus,(0,0xD),(1,0),[-0xd])
    test(t.slash,(15,4),(1,0),[15/4])
    test(t.star,(4,3),(1,0),[12])
    test(t.slashMod,(12,5),(2,0),[12/5,12%5])
    test(t.mod,(15,4),(1,0),[3])
    test(t.shift,(3,2),(1,0),[3<<2])
    test(t.shift,(6,-2),(1,0),[1])
    test(t.shift,(6,0),(1,0),[6])

    print 'Test compares:'
    test(t.equals,(1,2),(1,0),[False], test=1)
    test(t.equals,(1,1),(1,0),[True], test=2)
    test(t.lessthan,(1,1),(1,0),[False], test=1)
    test(t.lessthan,(1,2),(1,0),[True], test=2)
    test(t.greaterthan,(1,1),(1,0),[False], test=1)
    test(t.greaterthan,(2,1),(1,0),[True], test=2)
    test(t.ulessthan,(1,1),(1,0),[False], test=1)
    test(t.ulessthan,(-2,-1),(1,0),[True], test=2)
    test(t.ugreaterthan,(-1,-1),(1,0),[False], test=1)
    test(t.ugreaterthan,(-1,-2),(1,0),[True], test=2)
    test(t.absv,-5,(1,0),[5], test=1)
    test(t.absv,5,(1,0),[5], test=2)
    test(t.minv,(-5,-6),(1,0),[-6], test=1)
    test(t.minv,(-5,6),(1,0),[-5], test=2)
    test(t.maxv,(-5,-6),(1,0),[-5], test=1)
    test(t.maxv,(-5,6),(1,0),[6], test=2)

    print 'Test memory:'
    test(t.fetch,1,(1,0),[0])
    test(t.store,(333,3),mem=(3, 333))
    test(t.cfetch,3,(1,0),[333 & 0xFF])
    test(t.cstore,(444,4),mem=(4, 444 & 0xFF))
    test(t.plusbits,(0xa5,5),mem=(5, 0xa5))
    test(t.minusbits,(0xa5,5),mem=(5,0))
    test(t.cmove,(3,2,2),truth='me[2]==333 and me[3]==444&0xFF')
    test(t.fill,(4,2,0x55),truth='me[4]==0x55 and me[5]==0x55')
    test(t.erase,(2,2),truth='me[2]==0 and me[3]==0')
    
    print 'Test dictionary:'
    test(t.here,(),(1,0),[t.firstAddress])
    test(t.allot,3, truth = 't.dp == t.firstAddress+3')
    test(t.ccomma,257, truth = 't.dp == t.firstAddress+1 and me[t.firstAddress] == 1')
    test(t.comma,257, truth = 't.dp == t.firstAddress+1 and me[t.firstAddress] == 257')
    test(t.find,'junk',(1,0),[False])
    test(t.find,'dup',(1,0),[t.dup])
    test(t.execute,(0,t.dup),(2,0),[0,0])

    print 'Test output:'
    t.output = capture()
    test(t.emit,0x61, truth='t.output.outs == chr(0x61)', post=t.output.empty)
    test(t.cr,(),truth='t.output.outs == t.eol', post=t.output.empty)
    test(t.count,10,(2,0),[11,0])
    test(t.emits,(10,2),(0,0),truth=t.output.outs == '\x00\x00',post=t.output.empty)
    test(t.base,(),(1,0),[0])
    test(t.hexBase,(),truth='t.memory[0] == 16')
    test(t.decimal,(),truth='t.memory[0] == 10')
    test(t.dotr,(1,2),truth='t.output.outs == " 1"', post=t.output.empty)
    test(t.dot,2,truth='t.output.outs == " 2"', post=t.output.empty)
    test(t.dotb,1,truth='t.output.outs == " 00000001"', post=t.output.empty)
    test(t.dotb,-1,truth='t.output.outs == " 11111111"*4', post=t.output.empty)
    test(t.dotd,1,truth='t.output.outs == " 1"', post=t.output.empty)
    test(t.dotd,-1,truth='t.output.outs == " -1"', post=t.output.empty)
    test(t.doth,0x1234ABCD,truth='t.output.outs == " 1234ABCD"', post=t.output.empty, test=1)
    test(t.doth,-0x1234,truth='t.output.outs == " "+hex(0x100000000-0x1234)[2:-1].upper()', post=t.output.empty, diagnostic='t.dots()',test=2)
    test(t.dots,(1,2,3),(3,0),truth='t.output.outs == "3 stack items:  1 2 3"')

    print 'Test input'
    t.tib[0:4] = ['a','a','a',0]
    test(t.skip,(),arg=('a'),truth='t.inp == 3',test=1)
    test(t.skip,(),arg=('a'),truth='t.inp == 0',test=2)
    t.tib[0:4] = ['a','a','a',0]
    test(t.skip,(),arg=('v'),truth='t.inp == 0',test=3)
    test(t.parse,(),arg=('a'),truth='t.inp == 0',test=1)
    t.tib[0:4] = ['a','b','c',0]
    test(t.parse,(),arg=('c'),truth='t.inp == 2 and t.memory[t.dp:t.dp+4] == [2,"a","b",0]',test=2)
    t.tib[0:4] = ['a','b','c',0]
    test(t.parse,(),arg=('d'),truth='t.inp == 3 and t.memory[t.dp:t.dp+5] == [3,"a","b","c",0]',test=3)
    t.tib[0:4] = ['c','b','c',0]
    test(t.word,'c',truth='t.inp == 2 and t.memory[t.dp:t.dp+3] == [1,"b",0]',test=1)
    t.tib[0:4] = ['c','b','c',0]
    test(t.word,'x',truth='t.inp == 3 and t.memory[t.dp:t.dp+5] == [3,"c","b","c",0]',test=2)

    print 'Test makers'
    t.interpret('5 constant con')
    print t.tib[0:16]
    print t.memory[t.dp:t.dp+10]
    test(t.interpret,(),(1,0),5,arg=' con')
    
    print 'Passed',passed,'tests.',' Failed',failed,'tests.'

    def printTimbre():
        print 'data stack:', ds,
        print 'return stack:', rs
        print 'dictionary(%i):'%len(t.dictionary),
        t.words()

    printTimbre()
        
testTimbre()

