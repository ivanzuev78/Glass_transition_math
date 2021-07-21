import os

for filename in os.listdir(os.getcwd()):
    if filename.endswith(".receipt") or filename.endswith(".xlsx"):
        os.remove(filename)
