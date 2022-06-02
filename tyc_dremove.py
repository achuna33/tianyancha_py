def main():
    list_a = []
    list_b = []
    with open("result/structure_CompaniesList.csv", "r+", encoding="UTF-8") as file_1:
        for i in file_1.readlines():
            list_a.append(i.strip())

    with open("result/group_CompaniesList.csv", "r+", encoding="UTF-8") as file_2:
        for i in file_2.readlines():
            list_b.append(i.strip())

    for i in list_b:
        if i not in list_a:
            with open("result/othters.csv", "a+", encoding="UTF-8") as f:
                f.write(i + '\n')

if __name__ == '__main__':
    main()