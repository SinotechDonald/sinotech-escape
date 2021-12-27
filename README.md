# 中興工程顧問公司 x 國立臺灣大學 捷運站模型擷取暨逃生路徑規劃

## Prerequisite

* Git
* Python3.8+

## Install

* Clone the Repo

```bash
git clone https://code.hc07180011.synology.me/startup/sinotech-escape.git
cd sinotech-escape/source/
```

* Setup the environment

```bash
py -m venv venv
source venv/Scripts/activate
py -m pip install -r requirements_windows.txt
```

* Test if all things are correct

```bash
py main.py -h # Should be no error
```

## Deployment (windows 10)

```bash
source venv/Scripts/activate
py -m PyInstaller -D app.spec
# Output .exe is at: dist/app/app.exe
# The entire directory dist/app should not be modified
```

