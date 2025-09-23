
def read_list_tag(line, tag):
    if tag in line:
        l = line.split(tag)[1].split("[")[1].split("]")[0].split(",")
        for i in range(len(l)):
            l[i] = l[i].strip()
        return l
    else:
        return None

def has_tag(line, tag):
    return tag in line

def read_boolean_tag(line, tag):
    if tag in line:
        return line.split(tag)[1].strip() == "Yes"
    else:
        print("Line did not contain the given tag")

def read_tag(line, tag) -> bool:
    if tag in line:
        return line.split(tag)[1].strip()
    else:
        return None