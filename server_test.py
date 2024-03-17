from typing import Optional

# pip install pyusb
import usb.core
import usb.util


dev: Optional[usb.Device] = None
while dev is None:
    # Find the USB device by vendor and product ID
    for fdev in usb.core.find(idVendor=0x1234, idProduct=0x5678):
        dev = fdev
    print("Device not fouind")

# Set configuration
dev.set_configuration()

# Endpoint information
endpoint = dev[0][(0, 0)][0]

# Send data
data = b"Hello, USB!"
dev.write(endpoint.bEndpointAddress, data, 1000)

# Receive data
data = dev.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize, 1000)
print("Received data:", data)
