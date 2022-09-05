#! /usr/bin/python3

import argparse
import json
import pathlib
import requests
import secrets
import socket
import string
import sys
import time
from PIL import Image, ImageDraw, ImageFont
from sys import platform
from zeroconf import *

default_passwordfile = "./latestpassword.txt"
mdns_type = '_ekilb._tcp.local.'

class ServiceListener(object):
    def __init__(self):
        self.r = Zeroconf()
        self.devices = []

    def remove_service(self, zeroconf, type, name):
        pass

    def add_service(self, zeroconf, type, name):
        info = self.r.get_service_info(type, name)
        if info:
            address = (socket.inet_ntoa(info.addresses[0]))
            port = info.port
            name = info.name
            self.devices.append({"address": address, "port": port, "name": name})

    def update_service(self):
        pass


def generate_password():
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(20))
    return password


def lock(password, host):
    response = json.loads(
        requests.post(
            host+"/lock",
            data={"password": password}
        ).content
    )
    if response['result'] == "success":
        return True
    else:
        print(f"Error: {response['error']}")
        return False


def unlock(password, host):
    response = json.loads(
        requests.post(
            host+"/unlock",
            data={"password": password}
        ).content
    )
    if response['result'] == "success":
        return True
    else:
        print(f"Error: {response['error']}")
        return False


def update(host):
    response = json.loads(
        requests.post(
            host+"/update"
        ).content
    )
    if response['result'] == "success":
        return True
    else:
        print(f"Error: {response['error']}")
        return False


def get_settings(host):
    response = json.loads(
        requests.get(
            host+"/settings"
        ).content
    )
    return json.dumps(response["data"])


def set_setting(host, key, value):
    response = json.loads(
        requests.post(
            host+"/settings",
            data={key: value}
        ).content
    )
    if response['result'] == "success":
        return True
    else:
        print(f"Error: {response['error']}")
        return False


def find_devices(device_name = None):
    r = Zeroconf()
    listener = ServiceListener()
    browser = ServiceBrowser(r, mdns_type, listener=listener)
    for i in range(5):
        if len(listener.devices) > 0:
            if device_name is not None:
                if (any(d["name"] == device_name for d in listener.devices)):
                    break
            else:
                break
        time.sleep(1)
    r.close()
    return listener.devices


def save_password_text(password, file):
    f = open(file, "w")
    f.write(password)
    f.close()


def save_password_image(password, file):
    image_height = 128
    image_width = 512
    margins = 32
    img = Image.new('RGB', (image_width, image_height), color = (0, 0, 0))
    d = ImageDraw.Draw(img)

    if platform == "linux" or platform == "linux2":
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 28)
    elif platform == "win32":
        font = ImageFont.truetype("arial.ttf", 28)
    else:
        raise "Generating images only supported on linux and windows"

    text_width, text_height = font.getsize(password)
    if text_width > image_width - 2*margins:
        raise "Password too long for image"

    d.text((margins,margins), password, fill=(255,255,255), font=font)
    img.save(file)



def retrieve_password(file):
    f = open(file, "r")
    password = f.readline().strip()
    f.close()
    return password


def main():
    parser = argparse.ArgumentParser(description='Control the EKI Lockbox')
    parser.add_argument('-a', '--action', dest='action',
                        choices=["lock", "unlock", "update", "info", "change_setting"],
                        required=True)
    parser.add_argument('-s', '--setting', dest='setting',
                        help="e.g. 'name=my_first_box",
                        required='change_setting' in sys.argv)
    parser.add_argument('-p', '--password', dest='password')
    parser.add_argument('-f', '--password-file', dest='password_file',
                        help="e.g. './password.txt' or './password.png'")
    parser.add_argument('-d', '--device', dest='device',
                        help="e.g. 'lockbox_000000._ekilb._tcp.local.'")
    parser.add_argument('--host-override', dest='host_override',
                        help="e.g. 'http://192.168.0.1:5000'")
    args = parser.parse_args()

    # HOST SELECTION

    picked_host = ""
    if args.host_override is None:
        if args.device is None:
            devices = find_devices()
            if (len(devices) == 0):
                print("Error: no lockbox available. Exiting.")
                exit(1)
            elif len(devices) == 1:
                d = devices[0]
                print(f"Found one device: {d['name']}")
                picked_host = f'http://{d["address"]}:{d["port"]}'
            elif len(devices > 1):
                print("Error: too many devices. Select a specific one. Exiting.")
                exit(1)
        else:
            devices = find_devices(args.device)
            for d in devices:
                if d["name"] == args.device:
                    picked_host = f'http://{d["address"]}:{d["port"]}'
            if picked_host == "":
                print("Error: selected device not found. Exiting.")
                exit(1)
        
    else:
        picked_host = args.host_override
    print(f"Picked host {picked_host}")

    # FILE SELECTION

    if args.password_file is not None:
        password_file = args.password_file
    else:
        password_file = default_passwordfile
    
    password_file_extension = pathlib.Path(password_file).suffix

    # ACTION SELECTION

    if args.action == "lock":
        if args.password is not None:
            password = args.password
        else:
            password = generate_password()
        print(f'Password: {password}')

        if password_file_extension == ".txt":
            save_password_text(password, password_file)
        elif password_file_extension == ".png":
            save_password_image(password, password_file)
        else:
            print(f"Unknown file extension: {password_file_extension} Exiting.")
            exit(1)

        if lock(password, picked_host):
            print("Locked!")
        else:
            print("Could not lock")
    elif args.action == "unlock":
        if args.password is not None:
            password = args.password
        else:
            print("Getting password from file. Will fail for images!") # TODO: this is a lazy workaround
            try:
                password = retrieve_password(password_file)
            except FileNotFoundError:
                print("Could not unlock: file not found!")
                password = ""

        if unlock(password, picked_host):
            print("Unlocked!")
        else:
            print("Could not unlock")
    elif args.action == "update":
        if update(picked_host):
            print("updated succesfully")
        else:
            print("update failed")
    elif args.action == "info":
        print("Current settings are: " + get_settings(picked_host))
    elif args.action == "change_setting":
        key = args.setting.split('=')[0]
        value = args.setting[len(key)+1:]
        if key in ["name", "servo_open_position", "servo_closed_position"] and len(value) > 1:
            if set_setting(picked_host, key, value):
                print("Set!")
            else:
                print("Not set!")
        else:
            print("Invalid key or value")
    else:
        print("No action taken!")


if __name__ == "__main__":
    main()
