if len(command_args) < 3:
    print "Usage:  " + command_args[1] + " expectationname"

else:
    expectationName = command_args[2]

    if expectationName in Expectation.directory:
        print Expectation.directory[expectationName]
    else:
        print "not found"

    
        
