if len(command_args) < 3:
    print "Usage:  " + command_args[1] + " intentname"

else:
    intentName = command_args[2]

    if intentName in Intent.directory:
        print Intent.directory[intentName]
    else:
        print "not found"

    
        
