## Instructions for installing and trying `az next`

### How to install

1. You need `azure-cli-core` version 2.20.0+. Run`az version`to check your version. Use `az upgrade` to upgrade.
2. Install `az next` directly by executing `az extension add --name next`.
3. Run `az config set core.collect_telemetry=True` to turn on telemetry. This will help us improve az next recommendations based on your usage data.

### How to play

1. When you encounter an error, `az next` will recommend resolutions, based on what other users used most frequently to resolve the same error. <br/>
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223136.png)
*Pelase note: This kind of recommendation need to turn on telemetry, otherwise it will not work properly. (The following two recommendations are not affected)*

2. When you don't know what to do next, `az next` will recommend the next command to run, based on what other users with the same path used most frequently.
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223705.png)

3. When you may be in a common E2E scenario, `az next` will recommend the next set of command combinations, based on command combinations from the knowledge base constructed by data mining.
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223800.png)
![avatar](https://github.com/zhoxing-ms/image/blob/master/Screenshot%202021-01-06%20223923.png)

### How to give feedback
Please try az next for about a week, and give us feebdback: [issue for az next](https://github.com/hackathon-cli-recommendation/cli-recommendation/issues). <br/>
We are particularly interested in relevancy of recommendations. If there are any that you don't find relevant, please let us know and we can improve their relevancy.
