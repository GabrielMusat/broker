import wifi
import json


class Wifi:
    def __init__(self, interface='wlan0'):
        self.interface = interface
        config = json.load(open('config.json'))
        self.ssid = config['wifi']['ssid']
        self.password = config['wifi']['password']

    def set(self, ssid, password):
        cell = self.find(ssid)
        assert cell, LookupError('{} not found'.format(ssid))
        scheme = wifi.Scheme.for_cell(self.interface, ssid, cell, password)
        scheme.activate()
        scheme.save()
        config = json.load(open('config.json'))
        config['wifi']['ssid'] = ssid
        config['wifi']['password'] = password
        json.dump(config, open('config.json', 'w'))
        self.ssid = ssid
        self.password = password

    def connect(self):
        cell = self.find(self.ssid)
        assert cell, LookupError('{} not found'.format(self.ssid))
        scheme = wifi.Scheme.for_cell(self.interface, self.ssid, cell, self.password)
        scheme.activate()

    def find(self, ssid):
        for cell in wifi.Cell.all(self.interface):
            if cell.ssid == ssid:
                return cell
        else:
            return None

    def scan(self):
        cells = []
        print('scanning...')
        for cell in wifi.Cell.all(self.interface):
            print(cell.ssid)
            cells.append(cell)
        return cells


if __name__ == '__main__':
    manager = Wifi('wlx000db0029ce7')
    manager.scan()
