from twisted.internet import task, reactor

timeout = 60.0 # Sixty seconds

def doWork():
        #do work here
        print("twist")

l = task.LoopingCall(doWork)
l.start(timeout) # call every sixty seconds

reactor.run()
