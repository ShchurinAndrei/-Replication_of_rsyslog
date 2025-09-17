import paramiko
import sys
import datetime
from scp import SCPClient
import km_lin

linKey = r'/home/sigma.sbrf.ru@22682851/.ssh/rsa_key_prometheus_IFT'
file_path = r'/home/work/22682851@sigma.sbrf.ru/Replication_of_rsyslog/certificates/'
from_file = 'host_user.txt'

phost = []
puser = []
ptopic = []
pshort = []
files_1 = ['chain.pem', 'private_key.pem', 'published.pem']
dirs = ['mc', 'rsyslog_certs', 'rsyslog_workdir']
files_2 = ['rsyslog.conf', 'rules.pg']

# функция формирования из эталонных файлов - файлы для соответвующего хоста
def overwriting(input_file, host, user, topic, output_file):
    with open(input_file, 'r', encoding="utf-8") as f:
        content = f.read()
    new_content = content.replace('{host}', host.split('.',1)[0])
    new_content = new_content.replace('{user}', user)
    new_content = new_content.replace('{topic}', topic)
    with open(output_file, 'w', encoding="utf-8") as f:
        f.write(new_content)

#-----------------------------------------------------------------------------------------------------------------------
with open(from_file) as file:
    array_from=[row.strip() for row in file]

for f in array_from:    # цикл по строкам файла
    if f=='': continue # пропускаем пустые строки
    if f.startswith('#'): continue # пропускаем закомментированные строки
    phost.append(f.split()[0])
    puser.append(f.split()[1])
    ptopic.append(f.split()[2])
    pshort.append(f.split()[3])

for host, user, topic, short in zip(phost, puser, ptopic, pshort):  # цикл по связкам хост-уз-топик-АС
    print(host)

    for dir in dirs:    # создание струткуры директорий для rsyslog
        pp_res, s = km_lin.linCommand(f'test -d /home/{user}/.config/{dir}/ && echo 1 || echo 0', host, user, linKey)
        if s.strip()=='0':
            pp_res, s = km_lin.linCommand(f'mkdir /home/{user}/.config/{dir}', host, user, linKey)
            print(f'\t{dir} - создана')
        else: print(f'\t{dir} - уже существует')

    for file in files_1:    # копирование первой части файлов 
        path_out =file_path + short + '/' + file
        path_in = f'/home/{user}/.config/rsyslog_certs/'
        pp_res, s = km_lin.linCommand(f'test -f /home/{user}/.config/rsyslog_certs/{file} && echo 1 || echo 0', host, user, linKey)
        if s.strip()=='0':
            pp_res_transfer = km_lin.linPutFile(host, user, linKey, path_in, path_out)
            print(f'\t{file} - скопирован')
        else: print(f'\t{file} - уже существует')

    for file in files_2:    # копирование второй части файлов 
        path_out =file_path + file
        path_in = f'/home/{user}/.config/'
        pp_res, s = km_lin.linCommand(f'test -f /home/{user}/.config/{file} && echo 1 || echo 0', host, user, linKey)
        if file=='rsyslog.conf':
            overwriting(file_path + 'etalon_rsyslog.conf', host, user, topic, path_out)
        pp_res_transfer = km_lin.linPutFile(host, user, linKey, path_in, path_out)
        print(f'\t{file} - скопирован')

    pp_res, s = km_lin.linCommand(f'sudo systemctl start user_rsyslog@{user}.service', host, user, linKey)
    pp_res, s = km_lin.linCommand(f'sudo systemctl enable user_rsyslog@{user}.service', host, user, linKey)
    pp_res, s = km_lin.linCommand(f'systemctl is-active user_rsyslog@{user}.service', host, user, linKey)
    print(f'\tСтатус rsyslog - {s}')

    # pp_res, s = km_lin.linCommand(f'sudo systemctl restart user_rsyslog@{user}.service', host, user, linKey)
