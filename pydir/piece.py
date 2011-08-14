import re

s0 = "39"
s1 = ",19-22, 40-50, 100"
s2 = ",50-55,60"

p0 = r"^[, ]?(\d+-?\d+)"
p1 = r"[, ]?(\d+-\d+)"
p2 = r"[, ]?(\d+)"

for s in (s0, s1, s2):
    if not re.sub(r"[, \d-]", "", s):
        print("{} cleared!".format(s))


_list = []
def my_match(obj):
    global _list
    print("appending {}".format(obj.group(0)))
    obj_str = obj.group(1)
    inner = re.match(r"(\d+)-(\d+)", obj_str)
    if inner:
        first = inner.group(1)
        last  = inner.group(2)
        for i in range(int(first), int(last)+1):
            _list.append(str(i))
    else:
        _list.append(obj_str)
    return ""


for pattern in (p1, p2):
    print("applying {} on {}".format(pattern, s2))
    s2 = re.sub(pattern, my_match, s2)

print(_list)
