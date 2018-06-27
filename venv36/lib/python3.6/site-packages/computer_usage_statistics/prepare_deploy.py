# prepare_deploy.py
# Replaces all occurences of the actual path to the project folder with the template path PATH_TO_REPOSITORY. This is used in the deploy and when installing, PATH_TO_REPOSITORY is replaced by the actual path to the repository folder.

import os
cwd = os.getcwd()  # Current Working Directory

print "Changing all occurences of ", cwd, " to PATH_TO_REPOSITORY"

for filename in ["bash_script", "python_script.py", "print_to_terminal.py"]:
    with open(filename, 'r') as myfile:
        text = myfile.read()

    new_text = text.replace(cwd, "PATH_TO_REPOSITORY")
    
    with open(filename, 'w') as myfile:
        myfile.write(new_text)
