import csv
import datetime
import glob

#import mylogger

file_output = []


date_entry = input("Введите дату создания учетной записи, начиная с которой необходимо записть пользователей в новом созданном файле Users-Result.\nДату введите в YYYY-MM-DD формате: ")
year, month, day = map(int, date_entry.split('-'))
input_date = datetime.date(year, month, day)


def convert_str_to_datetime(datetime_str):
    """
    Конвертирует строку с датой в формате 11.10.2019 14:05:01 в объект datetime.
    """
    return datetime.datetime.strptime(datetime_str, "%d.%m.%y %H:%M:%S")


def loadCSVdata(source_file):
    with open (source_file, encoding='cp1251', errors='replace') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            user_date_cr_str = row[-4]
            if user_date_cr_str == "":
                continue
            elif user_date_cr_str == "Last login on":
                header = user_date_cr_str
                file_output.append({source_file})
                file_output.append(row)
                continue
            else:
                try:
                    user_date_cr = convert_str_to_datetime(user_date_cr_str)
                    if user_date_cr.date() > input_date:
                        file_output.append(row)
#                        print(user_date_cr)
#                        print(type(user_date_cr))
                    else:
                        continue
                except:
                    print("Ошибка считывания данных")
                    break
    file_output.append("\n")
    return file_output


def writeCSVdata(files, dest_file, append=False):
    for file in files:
        loadCSVdata(file)
#        print(file_output)
        with open(dest_file, 'a' if append else 'w', encoding='cp1251') as dest:
#            writer = csv.writer(dest, delimiter=";", quotechar=" ", quoting=csv.QUOTE_MINIMAL)
            writer = csv.writer(dest, delimiter=";")
            for line in file_output:
                writer.writerow(line)
        print(f"Файл {file} был обработан и обработанные данные записаны в новый файл {dest_file}.")


if __name__=='__main__':
    tenant_files = glob.glob("userExport_users*")
    print("*"*70)
    print(f"Названия файлов скопированные и найденные в текущем каталоге:\n{tenant_files}")
    print("*"*70)
    writeCSVdata(tenant_files, "Users-Result.csv")
