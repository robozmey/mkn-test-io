import json
from pprint import pprint

import os
from cram._encoding import b, bchr, bytestype, envencode, unicodetype
from cram._process import PIPE, STDOUT, execute

def execute_test(run_test, shell='/bin/sh', env=None, cleanenv=True):

    stdin = run_test

    if env is None:
        env = os.environ.copy()

    if cleanenv:
        for s in ('LANG', 'LC_ALL', 'LANGUAGE'):
            env[s] = 'C'
        env['TZ'] = 'GMT'
        env['CDPATH'] = ''
        env['COLUMNS'] = '80'
        env['GREP_OPTIONS'] = ''
    

    output, retcode = execute([shell] + ['-'], stdin=b('\n').join(stdin),
                              stdout=PIPE, stderr=STDOUT, env=env)

    return output

# Прочитать JSON

with open('.github/classroom/autograding.json', 'r', encoding='utf-8') as f:

    text = json.load(f) 

import subprocess

points = 0
sum_points = 0

for test in text['tests']:
    # Запустить команду
    output = execute_test(bytes(test['run'] + '\n' + test['input'] , 'utf-8').split(b'\n'))
    output = output.decode("utf-8") 
    # print (output)

    sum_points += test['points']

    if len(output) > 0 and (output[-1] == '\n' or output[-1] == ' '):
        output = output[0:-1]

    if output == test['output']:
        points += test['points']
        print('Test: "' + test['name'] + '" successed')
    else:
        print('Test: "' + test['name'] + '" failed')
        print((output))
        

print ("Points: ", str(points) + "/" + str(sum_points))


# Подсчитать и вывести ответ