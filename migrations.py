#!/usr/bin/env python
import re
import sys
import shlex
import subprocess
import migrations_settings as settings


BASE_CMD= f'psql -tA -U {settings.USER} {settings.DBNAME} -c'
FNAME = settings.FNAME
TAG = '# '


def exec_cmd(cmd):
    r = subprocess.run(shlex.split(cmd), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if r.stderr != b'' and not r.stderr.startswith(b'NOTICE:'):
        print('QUERY:', cmd)
        print('ERROR:', r.stderr)
        sys.exit()
    return r


def last_applied():
    cmd = f"{BASE_CMD} 'select public.last_migration_n()'"
    r = subprocess.run(shlex.split(cmd), stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if b'does not exist' in r.stderr: return None
    if r.stderr != b'':
        print(r.stderr)
        sys.exit()
    return int(r.stdout.strip())


def check_last_applied():
    if last_applied() is None:
        handle_notexist_last_applied()
        last_applied()


def handle_notexist_last_applied():
    print('>>> It looks like this database has no applied migrations yet.',
        'I will set the migration counter to zero. If this is a mistake, do not continue!')
    if input('Continue? ').lower() == 'y':
        init_last_applied()
    else:
        print('Can not continue without the migration counter.')
        sys.exit()


def init_last_applied():
    update_last_applied(0)


def update_last_applied(n):
    lines = open(FNAME).readlines()
    lines[0] = '#LAST_APPLIED: ' + str(n) + '\n'
    open(FNAME, 'w').write(''.join(lines))
    q = 'create or replace function public.last_migration_n() '\
        f"RETURNS int LANGUAGE sql PARALLEL SAFE AS 'select {n}'";
    cmd = f'{BASE_CMD} "{q}"'
    exec_cmd(cmd)
    print(f'>>> Migration counter was set to {n}.')


def enumerate_migrations():
    f = open(FNAME)
    lines = f.readlines()
    f.close()
    new = ''
    n = 1
    for line in lines:
        if line.startswith(TAG):
            n = int(line.strip(TAG)) + 1
    ln = 0
    while ln < len(lines):
        line = lines[ln]
        nextline = lines[ln+1] if ln+1 < len(lines) else '123'
        if (line.strip() == '' and not nextline.startswith(TAG)):
            new += f'\n{TAG}{n}'
            n += 1
        new += line
        ln += 1

    print(new)
    if  input('\n>>> Correct? ').lower() == 'y':
        f = open(FNAME, 'w')
        f.write(new)
        f.close()
        print('>>> OK. Now lets apply.')
    else:
        sys.exit()


def apply():
    lines = open(FNAME).readlines()
    last_n = last_applied()
    print('>>> Last applied migration number:', last_n)
    is_any_unapplied_found = False
    for line in lines:
        if line.startswith(TAG):
            n = int(line.strip(TAG))
            if last_n is None or n > last_n:
                is_any_unapplied_found = True
                q = ''.join(lines).split(f'\n{TAG}{n}')[1].split(TAG)[0].strip()
                print(f'\n>>> This query will be executed:\n{q}')
                if input('\n>>> Apply? ').lower() == 'y':
                    q = q.replace('\n', ' ')
                    cmd = f'{BASE_CMD} "{q}"'
                    exec_cmd(cmd)
                    update_last_applied(n)
                    print('>>> Applied successfully.\n')
                else:
                    sys.exit()
    if not is_any_unapplied_found:
        print('>>> No unapplied migrations found.')


def tables_list():
    cmd = f'{BASE_CMD} "select table_name from information_schema.tables where table_schema = \'public\'";'
    r = exec_cmd(cmd)
    tables = r.stdout.decode().split('\n')
    return [str(table).strip() for table in tables if table.strip() != '']


def dump_schema():
    cmd = f'pg_dump --schema-only -U {settings.USER} {settings.DBNAME}'
    r = exec_cmd(cmd)
    open(f'schema/schema.sql', 'w').write(r.stdout.decode())

    for table in tables_list():
        print(f'Saving schema of {table} to schema/{table}.sql')
        cmd = 'pg_dump  --schema-only -U postgres lpsql -t users | grep -v "^--" | grep -v "^SET " | grep -v "^SELECT pg_catalog.set_config"'
        cmd = f'pg_dump --schema-only -U {settings.USER} {settings.DBNAME} -t {table} -O'
        r = exec_cmd(cmd)
        s = r.stdout.decode()
        fin = ''
        for line in s.split('\n'):
            if (not line.startswith('--')
                    and not line.startswith('SET ')
                    and not line.startswith('SELECT pg_catalog.set_config')
                    #and line.strip() != ''
            ):
                fin += line + '\n'
        fin = re.sub(r'\n\n+', '\n\n', fin)
        fin = re.sub(r'^\n+', '', fin)
        open(f'schema/{table}.sql', 'w').write(fin)



if __name__ == '__main__':
    check_last_applied()
    enumerate_migrations()
    apply()
    if settings.DUMP_SCHEMA:
        dump_schema()
