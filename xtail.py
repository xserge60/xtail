#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time  #, sys, os
from datetime import datetime

__version__ = '4.15.2'

sys.path.insert(1, '/home/oracle/Lib')

from tools import *
value["DEBUG"] = False

print('Python version '+sys.version.split(' ')[0])

import json
import argparse

vers = 'Версия #15 {}#7  от {}'.format(__version__, datetime.fromtimestamp(os.path.getmtime(os.path.join(os.path.abspath(os.path.dirname(__file__)), os.path.basename(sys.argv[0])))).strftime('%d.%m.%Y %H:%M'))
print("#15 XTAIL#7  - Печатает файл или таблицу БД на стандартный вывод. {}".format(vers))

prnt("№12 Отладочный режим.")

def with_colors(s, c):
    if colors:
        for k in colors:
            s = s.replace(k, '#'+str(colors[k])+' '+k+'#7 ')
    return s

parser = argparse.ArgumentParser() #(description="Печатает последние строки файла или отбор из БД на стандартный вывод.")

parser.add_argument("-c", "--colors", help="JSON-строка описания цвета указанных слов")
parser.add_argument("-f", "--filecolors", help="JSON-файл с описанием цвета указанных слов. Если -c, то -f не учитывается")
parser.add_argument("-n", "--lines", help="выводить последние n строк (только для текстового файла)", default=10, type=int)
parser.add_argument("-o", "--oracle", help="Сервер БД Oracle", action="store_true")
parser.add_argument("-m", "--mysql", help="Сервер БД MySQL", action="store_true")
parser.add_argument("-s", "--host", help="адрес серва с БД (для MySQL)")
parser.add_argument("-b", "--database", help="имя БД")
parser.add_argument("-l", "--login", help="логин пользователя БД")
parser.add_argument("-p", "--password", help="пароль пользователя БД")
parser.add_argument("-w", "--wait", help="ждать доступность БД после потери коннекта", action="store_true")
parser.add_argument("-i", "--interval", help="интервал просмотра в секундах", default=1, type=float)
parser.add_argument("-v", "--verbose", help="Подробный вывод", action="store_true", default=False)
parser.add_argument("file", help="имя текстового файла или select из БД для отслеживания изменений.")

if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()

colors = json.loads(args.colors.replace("'", '"')) if args.colors else None

if args.filecolors and not colors:
    with open(args.filecolors, "r", encoding="utf-8") as fn:
        colors = json.load(fn)
elif colors and args.filecolors and args.verbose:
    print(args.filecolors, 'ignored.')

listening = True

if args.database:
    connection = False
    if not (args.login and args.password):
        print("#12 Для БД {} надо указывать логин (-l) и пароль (-p)".format(args.database))
        sys.exit(1)

    if args.oracle or not args.mysql:
        # c:\Python3\python.exe c:\Tools\xtail.py -i 10 -b rplus -l python -p python "select rpad(l.src,5), to_char(l.date_form,'dd.mm.yyyy hh24:mi'), decode(code,'WARN','#6 ','ERROR','#13 ','FATAL','#12 ','#15 ')||rpad(code,6)||'#7 ', rpad(l.section,30), decode(substr(l.answer_text,1,1),'!', '#12 ','?', '#14 ','-', '#2 ',null, '', '#10 ')||substr(text,1,50)||'#7 ' from view_log l where l.date_form>least(trunc(sysdate), sysdate-1/24) and code in ('WARN', 'ERROR', 'FATAL') order by cnt"
        import cx_Oracle

        row_hash = []

        if len(args.file) > 4 and args.file[-4:].lower() == '.sql':  # select может находиться в файле *.sql

            if not os.path.exists(args.file):
                print("#12 Не существует файл #15 {}".format(args.file))
                sys.exit(1)

            with open(args.file, "r") as f:
                select = f.read()
        else:
            select = args.file

        connection = False
        lastTimeAlive = datetime.now()
        connectionStatus = 0  # 0 -до первого коннекта; 1 -успешно подключен; 2 -потеря коннекта
        
        while True:

            try:
                # отслеживание таблицы БД Oracle
                prnt("connectionStatus: "+str(connectionStatus))
                connection = cx_Oracle.Connection(args.login, args.password, args.database)
                cursor = connection.cursor()
                cursor.execute(select)  # тест соединения
                prnt("connectionStatus: "+str(connectionStatus))
                if connectionStatus == 0:
                    if args.verbose:
                        print("Server Version:", connection.version)
                        print("Успешно подключено к", args.database)
                        print("Colors:", with_colors(str(colors), colors) if colors else "None")
                else:
                    if args.verbose:
                        print("-#2 ", datetime.now().strftime("%-d %b %Y %H:%M:%S %z"), "\r")

                connectionStatus = 1
                prnt("connectionStatus: "+str(connectionStatus))
                while listening:
                    cursor.execute(select)

                    for row in cursor:
                        h = hash(row)
                        if not (h in row_hash):
                            row_hash.append(h)
                            for val in row:
                                print(with_colors(str(val), colors).replace('\n', ' ').strip()+' ', end='')
                            print('')
                    sleep(args.interval)

            except Exception as e:
                prnt("connectionStatus: "+str(connectionStatus))

                if args.wait and connectionStatus > 0:
                    if connectionStatus == 1:
                        
                        if args.verbose:
                            print("#4 {}#7 ".format(datetime.now().strftime("%-d %b %Y %H:%M:%S %z")), end='')
                        
                        connectionStatus = 2
                    else:
                        if args.verbose:
                            print('.', end='', sep='')
                        sleep(args.interval*10)
                    connectionStatus = 2
                else:
                    print("Ошибка подключения к БД #15 {}#7 \n{}\n{}".format(args.database, e.args[0], select))
                    sys.exit(1)

                prnt("connectionStatus: "+str(connectionStatus))

            except KeyboardInterrupt:
                print("\n#15 End tailing.")
                listening = False

                sys.exit(0)

            finally:
                if connection:
                    connection.close()
                
                prnt("connectionStatus: "+str(connectionStatus))

                if connectionStatus == 1 and args.verbose:
                    print("Отключено от", args.database)

    elif args.mysql:
        # c:\Python3\python.exe xtail.py -i 2 -m -s 192.168.1.202 -b homedb -l pi -p mnp5 "SELECT date_format(h.date_form,'%d.%m.%Y %H:%i:%s') AS `date_form`, concat(IF(h.status>0 AND h.serial != '310208a7' AND if_signaling(h.cnt)=1, '#12 ', ''), IF(h.status=0 AND h.serial  = '310208a7', '#14 ', IF(h.serial = '310208a7', '#10 ', '')), rpad(`s`.`name`, 12)) AS `name`, `n`.`description` AS `description` FROM ((`sensors_need` `n` JOIN `bl_s1_sensors` `s`) JOIN `sensors_hist` `h`) WHERE `s`.`serial` = `n`.`serial` AND `h`.`serial` = `s`.`serial` AND `h`.`status` = `n`.`status` AND h.date_form > CURRENT_DATE() ORDER BY `h`.`cnt`"
        import MySQLdb

        row_hash = []

        if len(args.file) > 4 and args.file[-4:].lower() == '.sql':  # select может находиться в файле *.sql

            if not os.path.exists(args.file):
                print("#12 Не существует файл #15 {}".format(args.file))
                sys.exit(1)

            with open(args.file, "r") as f:
                select = f.read()
        else:
            select = args.file

        try:
            # отслеживание таблицы БД Oracle
            connection = MySQLdb.connect(host=args.host,
                                         user=args.login,
                                         passwd=args.password,
                                         db=args.database,
                                         charset='utf8',
                                         autocommit=True)

            if args.verbose:
                print("Успешно подключено к", args.database)
                print("Colors:", with_colors(str(colors), colors) if colors else "None")

            with connection.cursor() as cursor:
                while listening:
                    # if True:
                    try:
                        cursor.execute(select)
                        rows = cursor.fetchall()

                        for row in rows:
                            h = hash(row)
                            if not (h in row_hash):
                                row_hash.append(h)
                                for val in row:
                                    print(with_colors(str(val), colors)+' ', end='')
                                print('')
                        sleep(args.interval)

                    # else:
                    except Exception as e:
                        print("Ошибка выборки из таблицы MySQL {}: {}]".format(e.args[0], e.args[1]))

                    except KeyboardInterrupt:
                        print("\n#15 End tailing.")
                        listening = False

        except Exception as e:
            print("Ошибка подключения к БД #15 {} на {}, логин {}, пароль {}#7 \n{}".format(args.database, args.host, args.login, args.password, e.args[0]))
            sys.exit(1)

        finally:
            if connection:
                connection.close()
            
            if args.verbose:
                print("Отключено от", args.database)

    sys.exit(0)


fdino = None

# if True:
try:
    fd = open(args.file)
    fdino = os.fstat(fd.fileno()).st_ino

    if fd:
        nlines = 0
        for s in fd:
            nlines += 1

    n = min(nlines, args.lines)
    if args.verbose:
        print("Colors:", with_colors(str(colors), colors) if colors else "None", '\n', '~'*10+gram_case(n, ' последняя {} строка '.format(n), ' последние {} строки '.format(n), ' последние {} строк '.format(n))+'~'*10)

    pr_wait_file = False

    while listening:
        if pr_wait_file and not os.path.exists(args.file):
            print('\n#4 waiting for file ...', end='')
            sleep(3)
            continue

        fd = open(args.file)
        fdino = os.fstat(fd.fileno()).st_ino

        if fd:
            while listening:
                try:
                    if pr_wait_file:
                        pr_wait_file = False
                        print('\n#15 Файл появился!')
                    for s in fd:
                        if nlines > args.lines:
                            nlines -= 1
                            continue

                        print(with_colors(s,colors).replace('\n', '').replace('\r', ''), end = '\n' if s.find('\n')>=0 else '', sep = '')

                    sleep(args.interval)
                    print(' \b', end='', sep='')
                   
                    if os.stat(args.file).st_ino != fdino:
                        # pr_wait_file = True
                        print('\n#15 Файл сменился.')
                        break

                except FileNotFoundError:
                    pr_wait_file = True
                    break


# else:
except KeyboardInterrupt:
    print("\n#15 End tailing.")
    listening = False

    sys.exit(0)

except FileNotFoundError:
    print("\n#12 File not found "+args.file)
    listening = False
    sys.exit(1)

except Exception as e:
    print("[xTail #12 error#7 ]", e)
    sys.exit(1)
