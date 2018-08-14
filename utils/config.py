
class Config():
    @staticmethod
    def parse_file(file_name):
        config = {}
        for line in open(file_name):
            line = line.strip()
            if line and line[0] is not "#":
                var,value = line.split('=', 1)
                config[var.strip()] = value.strip()
        return config
