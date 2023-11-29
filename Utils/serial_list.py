import serial.tools.list_ports

def list_serial_ports():
    port_list = list(serial.tools.list_ports.comports())
    
    if not port_list:
        print("No serial ports found.")
    else:
        for port in port_list:
            print(f"Port: {port.device}, Description: {port.description}")

# Call the function to list available serial ports
list_serial_ports()
