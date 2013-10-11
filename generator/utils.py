import subprocess;

class Popen:
    def __init__(self, string):
        args = string.split(" ");
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
        (self.out, self.err) = proc.communicate()
        self.returncode = proc.returncode;
