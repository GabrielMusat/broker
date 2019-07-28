import socketio
import requests
import json
import sys
import octoapi as octoapi
import asyncio

config = json.loads(open('config.json').read())

sio = socketio.AsyncClient()


username = sys.argv[1]
password = sys.argv[2]
gcodes_folder = config['gcodes_folder']


def retrieve_file(file):
    params = {'file': file}
    r = requests.get(config['url'] + '/download', params=params, auth=(username, password), stream=True)
    assert r.status_code == 200, Exception('response {} from server: {}'.format(r.status_code, r.text))
    with open(gcodes_folder + '/' + file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)


def send_instruction(data):
    try:
        if data['instruction'] == 'home':
            r = octoapi.post_home()
            assert r.status_code == 200, Exception(r.text)
            print('homing...')
            return 'ok'

        elif data['instruction'] == 'print':
            r = octoapi.post_print(data['file'])
            assert r.status_code == 200, Exception(r.text)
            print('printing file "{}"'.format(data['file']))
            return 'ok'

        elif data['instruction'] == 'download':
            retrieve_file(data['file'])
            print('file {} uploaded to octoprint'.format(data['file']))
            return 'ok'

        elif data['instruction'] == 'command':
            r = octoapi.post_command(data['command'])
            assert r.status_code == 200, Exception(r.text)
            print('executing command {}'.format(data['command']))
            return 'ok'

    except Exception as e:
        print('error sending instruction: {}'.format(str(e)))
        return 'error sending instruction: {}'.format(str(e))


@sio.event
async def connect():
    print('I am connected, Yuju!')


@sio.event
async def disconnect():
    print('I have been disconneted, noooooo!')


@sio.event
async def instruction(data):
    print('I just received this instruction: {}'.format(data))
    r = send_instruction(data)
    await sio.emit('response', {'user': username, 'response': r})


async def main():
    await sio.connect(config['url'], headers={'name': username})
    while True:
        temp = octoapi.get_tool_dict()
        job = octoapi.get_job_dict()
        await sio.emit('status', {
            'user': username,
            'status': {
                'temp': int(temp['tool0']['actual']) if isinstance(temp, dict) else -1,
                'job': int(job['progress']['completion']) if isinstance(job, dict) and octoapi.is_printing() else -1
            }
        })
        await asyncio.sleep(10)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
