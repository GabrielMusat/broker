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
            print('homing...')
            r = octoapi.post_home()
            assert r.status_code == 204, Exception(r.text)
            print('home ok')
            return 'ok'

        elif data['instruction'] == 'print':
            print('printing file "{}"'.format(data['file']))
            r = octoapi.post_print(data['file'])
            assert r.status_code == 204, Exception(r.text)
            print('print ok')
            return 'ok'

        elif data['instruction'] == 'cancel':
            print('cancelling print')
            r = octoapi.post_cancel()
            assert r.status_code == 204, Exception(r.text)
            print('cancel ok')
            return 'ok'

        elif data['instruction'] == 'download':
            retrieve_file(data['file'])
            print('file {} uploaded to octoprint'.format(data['file']))
            print('download ok')
            return 'ok'

        elif data['instruction'] == 'move':
            print('moving axis {} {}mm'.format(data['axis'], data['distance']))
            for command in ['G91', 'G1 {}{} F1000'.format(data['axis'], data['distance']), 'G90']:
                print('executing command {}'.format(command))
                r = octoapi.post_command(command)
                assert r.status_code == 204, Exception(r.text)
            print('move ok')
            return 'ok'

        elif data['instruction'] == 'command':
            print('executing command {}'.format(data['command']))
            r = octoapi.post_command(data['command'])
            assert r.status_code == 204, Exception(r.text)
            print('command ok')
            return 'ok'

        elif data['instruction'] == 'unload':
            print('unloading filament...')
            for command in ['M109 S210', 'G92 E0', 'G1 E15 F150', 'G1 E-135 F300', 'M109 S0']:
                print('executing command {}'.format(command))
                r = octoapi.post_command(command)
                assert r.status_code == 204, Exception('error executing command {}: {}'.format(command, r.text))
            print('unload ok')
            return 'ok'

        elif data['instruction'] == 'load':
            print('loading filament...')
            for command in ['M109 S210', 'G92 E0', 'G1 E100 F150', 'M109 S0']:
                print('executing command {}'.format(command))
                r = octoapi.post_command(command)
                assert r.status_code == 204, Exception('error executing command {}: {}'.format(command, r.text))
            print('load ok')
            return 'ok'
        else:
            raise Exception('instruction {} not understood'.format(data['instruction']))

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
    while True:
        try:
            await sio.connect(config['url'], headers={'name': username})
            break
        except Exception as e:
            print('error connecting to server: {}'.format(str(e)))
        await asyncio.sleep(5)

    while True:
        try:
            printer_status = octoapi.get_printer_dict()
        except Exception as e:
            print('error getting printer status: {}'.format(str(e)))
            printer_status = None

        if not isinstance(printer_status, dict):
            await sio.emit('status', {'user': username, 'status': {'hotend': 0, 'bed': 0, 'job': -1, 'status': 'Disconnected'}})
            if printer_status is not None: octoapi.post_connect()
            await asyncio.sleep(3)
            continue
        hotend = printer_status['temperature']['tool0']['actual'] if 'tool0' in printer_status['temperature'] else 0
        bed = printer_status['temperature']['bed']['actual'] if 'bed' in printer_status['temperature'] else 0
        printing = printer_status["state"]["flags"]["printing"]
        status = printer_status['state']['text']
        if status == 'Closed':
            octoapi.post_connect()
        job = octoapi.get_job_dict()
        job = job['progress']['completion'] if 'progress' in job and printing else -1
        await sio.emit('status', {
            'user': username,
            'status': {
                'hotend': hotend,
                'bed': bed,
                'job': job,
                'status': status
            }
        })
        await asyncio.sleep(3)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
