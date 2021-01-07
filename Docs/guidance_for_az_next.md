## The guidance for az next

### How to install

**MSI** *(If you installed CLI by MSI before, please choose this way)* <br/>
Supported Systems: `Windows` <br/>
Script URL: [install_by_msi.ps1](https://clirecommendation.blob.core.windows.net/package/install_by_msi.ps1) <br/>
Start `PowerShell` as **administrator** and run this script: **./install_by_msi.ps1** <br/>

**Pip** *(If you installed CLI by pip before, please choose this way)* <br/>
Supported Systems: `Windows`, `Linux`, `Mac` <br/>
Script URL: [install_by_pip.sh](https://clirecommendation.blob.core.windows.net/package/install_by_pip.sh) <br/>
Please run this script: **sh install_by_pip.sh**

**Others** *(If you installed CLI by other ways before, such as Homebrew, please choose this way)* <br/>
Supported Systems: `Windows`, `Linux`, `Mac` <br/>
- Create a virtual environments by `Python` [How to create venv](https://docs.python.org/3/tutorial/venv.html) <br/>
- After entering the virtual environment, execute command **pip install azure-cli** to install `azure-cli` <br/>
- Using script to install `az next`: **sh install_by_pip.sh** *(Script URL: [install_by_pip.sh](https://clirecommendation.blob.core.windows.net/package/install_by_pip.sh) )* <br/>

### How to play

1. When you make an error in executing command, it will recommend the solution most used by others who has the same error
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223136.png)

2. When you don't know what to do next, it will recommend the next command to be executed most by others who has the same execution path
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223705.png)

3. When you may be in a common E2E scenario, it will recommend the next set of command combinations in a specific scenario
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223800.png)
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223923.png)

### Feedback
Please do play with it and share any feedback or suggestions. <br/>
If you think there are some inaccuracies in the recommendation, please let us know what you expect to be recommended, we will try to solve these problems in the future.
