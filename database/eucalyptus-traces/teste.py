def get_profile(nit, pr, profile_file):
    profile = {}

    with open(profile_file, 'r') as log:
        for i in range(nit):
            profile[i] = []
            op = str(log.readline())
            
            print "OP:"+op
            
            if op.find("START"):
                print "FOUND START"
                line = log.readline()
                print "LINE:" + line
                profile[i].append({'op': "START"})
            elif op.find("STOP"):
                print "FOUND STOP"
                line = log.readline().split()
                print "LINE:" + line.__str__()

get_profile(20, 2, "DS1-trace.txt")

