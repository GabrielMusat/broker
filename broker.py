import socketio
import requests
import json
import octoapi as octoapi
import base64
import asyncio

config = json.loads(open('config.json').read())

sio = socketio.AsyncClient()


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
async def connect():
    print('I am connected, Yuju!')


@sio.event
async def disconnect():
    print('I have been disconneted, noooooo!')


@sio.event
async def instruction(data):
    print(f'I just received this instruction: {data}')
    r = send_instruction(data)
    await sio.emit('response', {'user': config['username'], 'response': r})


async def main():
    await sio.connect(config['url'], headers={'name': config["username"]})
    while True:
        await sio.emit('status', {
            'user': config["username"],
            'status': {
                'temp': 1,
                'job': -1
            }
        })
        await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
