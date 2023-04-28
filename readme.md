Advacam Quad Controller

Offline Installation
- Install python from ```prerequisites/python-3.7.9-amd64.exe```, select add python to path.
- Check python version from cmd with ```python -V```, should be 3.7.x.
- Install redist from ```prerequisites/VC_redist.x64.exe```.
- Open cmd in prerequsites folder, install dearpygui with ```python -m pip install dearpygui-1.9.0-cp37-cp37m-win_amd64.whl```

Online Installation
- Install python from ```https://www.python.org/downloads/release/python-379/```
- Check python version from cmd with ```python -V```, should be 3.7.x.
- Install redist from ```https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170#visual-studio-2015-2017-2019-and-2022```
- Install dearpygui with ```python -m pip install dearpygui```

Use
- Start Pixet and load all device confings to appropriate devices OR manually copy all configs to ```C:\Users\<username>\AppData\Local\PixetPro\configs``` on Windows.
- Copy this script next to Pixet runnable and execute ```AdvacamQuadController.py```

Warning
- Pixet should not be running along the script. Always use only script or only Pixet.
