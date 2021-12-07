from bluepy import btle

scanner = btle.Scanner(0)
devices = scanner.scan(3.0)

for device in devices:
    print(device.addr, device.addrType, device.rssi)

MAC_ADDRESS = '40:f5:20:48:5e:94'

peripheral = btle.Peripheral()
peripheral.connect(MAC_ADDRESS)

for service in peripheral.getServices():
    print('service UUID: ', service.uuid)
    for characteristic in service.getCharacteristics():
        print('characteristic UUID: ', characteristic.uuid)
        print('handle: ', characteristic.getHandle())
        print('properties: ', characteristic.propertiesToString())

service = peripheral.getServiceByUUID(SERVICE_UUID)
characteristic = peripheral.getCharacteristics(CHARACTERISTIC_UUID)

class MyDelegate(btle.DefaultDelegate):
    def __init__(self, params):
        super().__init__()

    def handleNotification(self, cHandle, data):
        pass

peripheral.withDelegate(MyDelegate(params))
handle = 18
peripheral.writeCharacteristic(handle, ...)

TIMEOUT = 1.0
while True:
    if peripheral.waitForNotifications(TIMEOUT):
        print('time out')
        continue
    print('waiting')