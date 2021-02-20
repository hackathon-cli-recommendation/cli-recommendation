## The guidance for az next

### How to install

`az next` has been released as an extension, so you can install `az next` directly by executing `az extension add --source https://clirecommendation.blob.core.windows.net/package/next-0.1.0-py2.py3-none-any.whl --yes`.  *(If you have ever installed an older version of `az next`, please execute `az extension remove -n next` to uninstall the older version before installing the new version for `az next`)*

However, you need to make sure that the version of `azure-cli-core` is 2.19.0+ (which can be viewed with `az version`). 
If you are using an older version, please use `az upgrade` to upgrade.

### How to play

1. When you make an error in executing command, it will recommend the solution most used by others who has the same error. <br/>
*Pelase note: This kind of recommendation need to turn on telemetry. If you haven not turned it on yet, please run `az config set core.collect_telemetry=True` and try again. If telemetry is not turned on, only this kind of recommendation will be affected, others can be used normally.*
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223136.png)

2. When you don't know what to do next, it will recommend the next command to be executed most by others who has the same execution path
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223705.png)

3. When you may be in a common E2E scenario, it will recommend the next set of command combinations in a specific scenario
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223800.png)
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223923.png)

### How to feedback
Please do play with it, and if you have any suggestions or feedback, please submit them here: [issue for az next](https://github.com/hackathon-cli-recommendation/cli-recommendation/issues). <br/>
If you think there are some inaccuracies in the recommendation, please let us know what you expect to be recommended, we will try to solve these problems in the future.
