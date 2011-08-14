
def random_file_names(how_many):
    import random

    for h in range(how_many):
        l = random.randint(6, 50)
        chr_list = [chr( (ord('a')-1) + random.randint(1, 26)) for t in range(l)]
        if len(chr_list) > 10:
            where_spaces = [random.randint(6, l-4 if l > 6+4 else 7) for t in range(random.randint(1, 3))]
            last = 0
            for w in where_spaces:
                if not w - 1 == last and not w == l:
                    print(w)
                    print(chr_list)
                    chr_list[w] = ' '
                last = w
        ext = "".join([chr( (ord('a')-1) + random.randint(1, 26)) for t in range(3)])
        yield "{}.{}".format("".join(chr_list), ext)


if __name__ == '__main__':

    for r in random_file_names(100):
        print(r)
