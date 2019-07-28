import requests
import json
import base64
import socketio
import octoapi as octoapi

config = json.loads(open('config.json').read())

sio = socketio.Client()
sio.connect(config['url'], headers={'Authorization': 'Basic ' + base64.b64encode(f'{config["username"]}:{config["password"]}'.encode()).decode()})

username = config['username']
password = config['password']
gcodes_folder = config['gcodes_folder']


def retrieve_file(filename):
    params = {'filename': filename}
    r = requests.get(config['url'] + '/download', params=params, auth=(username, password), stream=True)
    with open(gcodes_folder + '/' + filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)


def send_instruction(data):
    try:
        if data['instruction'] == 'home':
            octoapi.post_home()
            print('homing...')
            return 'ok'

        elif data['instruction'] == 'print':
            octoapi.post_print(data['file'])
            print('printing file "{}"'.format(data['file']))
            return 'ok'

        elif data['instruction'] == 'download':
            retrieve_file(data['filename'])
            print('file {} uploaded to octoprint'.format(data['file']))
            return 'ok'

        elif data['instruction'] == 'command':
            octoapi.post_command(data['command'])
            print('executing command {}'.format(data['command']))
            return 'ok'

    except Exception as e:
        print(f'error sending instruction: {e}')
        return f'error sending instruction: {e}'


@sio.event
def connect():
    print('I am connected, Yuju!')


@sio.event
def instruction(data):
    print(f'I just received the next instruction: {data}')
    r = send_instruction(data)
    sio.emit('response', {'user': config['username'], 'response': r})


def main():
    while True:
        sio.emit('status', {
            'temp': int(octoapi.get_tool_dict()['tool0']['actual']),
            'job': int(octoapi.get_completion()) if octoapi.is_printing() else -1
        })
        sio.sleep(10)


if __name__ == '__main__':
    main()
