# cli-recommendation

<div class="video-container">
    <video width="100%" controls autoplay fullscreen>
        <source src="https://raw.githubusercontent.com/wu5bocheng/cli-recommendation/add-chatgpt-service/Videos/intelligent_az_interactive.mp4" type="video/mp4">
        Your browser does not support the video tag.
    </video>
</div>
 

We are very excited to announce that Azure CLI team combined AI with CLI interactive mode *(az interactive)* to provide users with an intelligent interactive experience.

It is mainly oriented to the inexperienced users in interactive mode to help them reduce the learning cost, provide an intelligent interactive experience, and improve the operation efficiency in some complex scenarios.

 

# What is it

Currently, our product mainly provides customers with four revolutionary features:

• Intelligent Completion

It combines the AI powered recommendation system based on Telemetry analysis to analyze and predict customer behavior, prioritizing the most needed contents as the high priority completion options.



• Command Recommendation

When you don't know what to do next, it supports recommending the next command which is most used in other similar sessions.

\# GIF 2 当用户没有任何输入时命令推荐的补全场景

 

• Scenario identification

When you work on an E2E scenario, it can identify the current possible scenarios and recommend a set of related command combinations for this specific E2E scenario. *(And it has a parameter completion mechanism, which can reduce repeated input of the same parameter values in the same scenario.)*

 

\# GIF 3 用户补全scenario时的补全场景

 

• Usage knowledge search

You can use the natural language keywords to search for the commands and usage scenarios you need, and smoothly create and execute corresponding CLI tasks.

 

\# GIF 4 用户搜索scenario时执行的场景

 

Moreover, we are investing in using ChatGPT's ability to generate complex and more accurate CLI tasks by multiple sessions, which will be announced in the future versions. Please stay tuned! 😊

 

If you want to have a more intuitive understanding of our features, you can watch the demo video: 

# How to Play

 

As it is currently in the public preview stage, you need to install our beta version of *"az interactive"* extension:

*$ az extension remove --name interactive* *(if you have already installed it, you need to remove the original version first)*

*$ az extension add --source https://raw.githubusercontent.com/wu5bocheng/azure-cli-extensions/storage/storage/interactive-0.5.0-py2.py3-none-any.whl*

 

All AI related features are enabled by default. If they disturb you, you can use the following command to turn them off

*$ az config set interactive.enable_recommender=False*

 

For more specific usage, please refer to the [guideline](https://nam06.safelinks.protection.outlook.com/?url=https%3A%2F%2Fgithub.com%2Fwu5bocheng%2Fazure-cli-extensions%2Fedit%2Finteractive-main%2Fsrc%2Finteractive%2FREADME.md%3Fpr%3D%2FAzure%2Fazure-cli-extensions%2Fpull%2F5950&data=05|01|v-bochengwu%40microsoft.com|d775dafe0df9495af94408db5dd3dcf5|72f988bf86f141af91ab2d7cd011db47|1|0|638206936809495429|Unknown|TWFpbGZsb3d8eyJWIjoiMC4wLjAwMDAiLCJQIjoiV2luMzIiLCJBTiI6Ik1haWwiLCJXVCI6Mn0%3D|3000|||&sdata=n9UHAntocBl8Ye02YmLemQV3ET04VmxMZipBG4HHxcI%3D&reserved=0) of "az interactive".

 

If you encounter any issues while using the CLI intelligent mode or have suggestions on how we can make it even better, please do not hesitate to create an issue on [GitHub](https://nam06.safelinks.protection.outlook.com/?url=https%3A%2F%2Fgithub.com%2FAzure%2Fazure-cli%2Fissues%2F&data=05|01|v-bochengwu%40microsoft.com|d775dafe0df9495af94408db5dd3dcf5|72f988bf86f141af91ab2d7cd011db47|1|0|638206936809495429|Unknown|TWFpbGZsb3d8eyJWIjoiMC4wLjAwMDAiLCJQIjoiV2luMzIiLCJBTiI6Ik1haWwiLCJXVCI6Mn0%3D|3000|||&sdata=w2ty4LVImOBo3n%2FGFuczQIGhopOJ00vZLLJJTfkA%2BjE%3D&reserved=0).

 

Thanks,

Xing

 
