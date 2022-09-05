# Control

The box is controlled with a python application. Download `main.py` and `requirements.txt` by cloning this repository, downloading the .zip or in another way you prefer.

## Windows

Install Python from the Microsoft Store or in whichever way you prefer. mDNS/Zeroconf should be supported out of the box on recent versions of Windows.

With CMD or Powershell, navigate to these files.

Install the requirements for the application:

```Powershell
Python3 -m pip install -r requirements.txt
```

You can now run the application:

```Powershell
python3 main.py --action lock --password-file C:\Users\username\Desktop\password.png
```

## Linux

Install the requirements for the application:

```bash
pip3 install -r requirements.txt
```

You can now run the application:

```bash
python3 main.py -a lock
```

To access the box more easily, enter the following commands.

```bash
sudo chmod +x ./main.py
sudo ln -s /path/to/main.py /usr/bin/lockboxcontrol
```
