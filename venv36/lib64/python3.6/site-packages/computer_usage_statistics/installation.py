# installation.py
# Replaces all occurences of "PATH_TO_REPOSITORY/" with the path to the current working folder.

import os
cwd = os.getcwd()  # Current Working Directory

print "Changing all occurences of PATH_TO_REPOSITORY to ", cwd

# Set up the paths
for filename in ["bash_script", "python_script.py", "print_to_terminal.py"]:

    with open(filename, 'r') as myfile:
        text = myfile.read()

    new_text = text.replace("PATH_TO_REPOSITORY", cwd)

    with open(filename, 'w') as myfile:
        myfile.write(new_text)

# Initialize an empty histogram if there is none
if os.path.isfile(cwd + '/histogram.txt'):
    print "Histogram already present, leaving it untouched."
    
else:
    print "No histogram.txt present, making a new empty histogram"
    empty_histogram = "0\n"*24
    with open('histogram.txt', 'w') as myfile:
        myfile.write(empty_histogram)
    
        

