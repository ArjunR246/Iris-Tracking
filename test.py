import serial
esp = serial.Serial("COM5", 115200)
esp.write(b'B')
print("Sent B")
esp.close()
