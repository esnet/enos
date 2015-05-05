from net.es.netshell.api import GenericGraphViewer

if len(command_args) < 3:
    print "Usage:  " + command_args[1] + " expectationname"

else:
    expectationName = command_args[2]

    if expectationName in Expectation.directory:
        g = Expectation.directory[expectationName].props['topology']
        gv = GenericGraphViewer(g)
        gv.display()
        
    else:
        print "not found"
