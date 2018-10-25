
class Config():
    @staticmethod
    def parse_file(file_name):
        config = {}
        with open(file_name) as file_:
            for line in file_:
                line = line.strip()
                if line and line[0] is not "#":
                    var,value = line.split('=', 1)
                    config[var.strip()] = value.strip()

        return config
