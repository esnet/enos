from net.es.netshell.api import GenericGraphViewer

if len(command_args) < 3:
    print "Usage:  " + command_args[1] + " intentname"

else:
    intentName = command_args[2]

    if intentName in Intent.directory:
        g = Intent.directory[intentName].graph
        gv = GenericGraphViewer(g)
        gv.display()
        
    else:
        print "not found"

    
        
