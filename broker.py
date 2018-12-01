#!/usr/bin/env python


import requests
import json
import octoapi as octoapi
import time

config = json.loads(open('broker.conf').read())


username = config['username']
password = config['password']
Artenea_URL = config['Artenea_URL']
gcodes_folder = config['gcodes_folder']


def retrieve_file(filename):
    params = {'filename': filename}
    r = requests.get(Artenea_URL + '/download', params=params, auth=(username, password), stream=True)
    with open(gcodes_folder + '/' + filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)


def temp():
    return int(octoapi.get_tool_dict()['tool0']['actual'])


def print_percentage():
    if octoapi.is_printing():
        return int(octoapi.get_completion())
    else:
        return -1


def send_instruction(to_send):
    instruction = to_send['instruction']

    try:
        if instruction == 'home':
            octoapi.post_home()
            print('homing...')

        elif instruction == 'print':
            octoapi.post_print(to_send['file'])
            print('printing file "{}"'.format(to_send['file']))

        elif instruction == 'download':
            retrieve_file(to_send['filename'])
            print('file {} uploaded to octoprint'.format(to_send['filename']))

        elif instruction == 'command':
            octoapi.post_command(to_send['command'])
            print('executing command {}'.format(to_send['command']))

    except Exception as e:
        print('imposible to connect to octoprint')
        print(e)


def main():
    while True:
        try:
            params = {'temp': temp(), 'job': print_percentage()}
            r = requests.get(Artenea_URL + '/buffer', params=params, auth=(username, password))
            to_send = r.json()

            if to_send['instruction'] == 'None':
                print('no instructions in buffer')

            else:
                print('instruction found on Artenea /buffer:')
                send_instruction(to_send)

        except Exception as e:
            print('Unable to send instruction to Artenea server, retrying...')
            print(e)

        time.sleep(1)


if __name__ == '__main__':
    main()
