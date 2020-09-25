# CLI Recommendation

## Overview
### 1. What's the project?
This is a recommendation system based on customer behavior analysis, it performs big-data analysis from the Telemetry log to calculate the behavior tracks of most customers for usage recommendations in CLI.
### 2. What problem does it solve?
At present, there are some problems in usage experience for CLI：
- ❌ There are too many commands, and the association is complex. The CLI beginners often does not know what the command corresponding to his requirements is
- ❌ Most of the knowledge customers need can only be obtained by searching in the documents, so the learning cost is high
- ❌ The operation steps of some scenarios are too complex, the interaction is not intelligent enough, so the operation efficiency is low

So what we're doing is an in-tool guidence which can reduce customer's learning cost and improves use efficiency:
- ✔ Help the CLI beginners quickly pick up the commands they need 
- ✔ Provide a simpler and smoother interaction experience
- ✔ Recommend other potential requirements to customers

![avatar](https://github.com/zhoxing-ms/image/blob/master/Annotation%202020-07-30%20222354.png)

## Applicable Scenarios
### 1. solution
When a customer executes a command with some kind of error, recommend the next command that the vast majority of users execute and ask him to confirm whether to execute it. This reduces the process of the customer's troubleshooting and command input

*For example, when a customer fails to execute a command due to an unknown permission problem, it is directly recommended to the next command that most users use to apply for a certain permission, and let him confirm whether to execute it.* 

```pwsh
(env) PS C:\project> az deployment create -l westus -f template.json -p @param.json
msrestazure.azure_exceptions.CloudError: Azure Error: AuthorizationFailed
Message: The client 'xxx' with object id 'xxx' does not have authorization to perform action 'Microsoft.Resources/subscriptions/resourcegroups/write' over scope '/subscriptions/xxx' or the scope is invalid. If access was recently granted, please refresh your credentials.

(env) PS C:\project> az next

Please select the type of recommendation you need:
1. all: It will intelligently analyze the types of recommendation you need, and may recommend multiple types of content to you
2. solution: Only the solutions to problems when errors occur are recommend
3. command: Only the commands with high correlation with previously executed commands are recommend
4. resource: Only the resources related to previously created resources are recommended
5. senario: Only the E2E scenarios related to current usage scenarios are recommended

What kind of recommendation do you want? (RETURN is to set all): 2

az role assignment create
Recommended reason: 97% users create a new role assignment for a user, group, or service when this error is encountered

Does it help for you? (y/n): y

Do you want to do it immediately? (y/n): y

Please input role (Role name or id): contributor
Please input assignee (Represent a user, group, or service principal): xxx
Please input scope (Scope at which the role assignment or definition applies to): /subscription/xxx/...
...
```

### 2. command
When a customer executes a command, it is recommended that other groups of commands be used most frequently by users who also executed the same command.

*For example, there are the following possible common command combination recommendations: 'az policy definition create' --> 'az policy assignment create', 'az deployment sub validate' --> 'az deployment sub what-if' --> 'az deployment sub create' ...*

```pwsh
(env) PS C:\project> az policy definition create --name readOnlyStorage --rules "{...}"
Policy definition created successfully...

(env) PS C:\project> az next

Please select the type of recommendation you need:
1. all: It will intelligently analyze the types of recommendation you need, and may recommend multiple types of content to you
2. solution: Only the solutions to problems when errors occur are recommend
3. command: Only the commands with high correlation with previously executed commands are recommend
4. resource: Only the resources related to previously created resources are recommended
5. senario: Only the E2E scenarios related to current usage scenarios are recommended

What kind of recommendation do you want? (RETURN is to set all): 3

az policy assignment create
Recommended reason: 92% users create a policy assignment to assign policy after creating the policy

Does it help for you? (y/n): y

Do you want to do it immediately? (y/n): y

Please input name (Name of the new policy assignment): next-test
Please input location (The location of the policy assignment): westus
Please input scope (Scope to which this policy assignment applies): /subscription/xxx/...
...
```

### 3. resource
After a customer has created a certain type of resource, it is recommended to the next type of resource that most users who have created the same resource will create. Help the customer find more resources that might be helpful to him.

*For example, after creating a VM, most users will create a policy to ensure the security of resources. Therefore, the policy resource can be recommended to the user who has just created the VM* 

```pwsh
(env) PS C:\project> az vm create -n MyVm -g MyResourceGroup --image UbuntuLTS
VM created successfully...

(env) PS C:\project> az next

Please select the type of recommendation you need:
1. all: It will intelligently analyze the types of recommendation you need, and may recommend multiple types of content to you
2. solution: Only the solutions to problems when errors occur are recommend
3. command: Only the commands with high correlation with previously executed commands are recommend
4. resource: Only the resources related to previously created resources are recommended
5. senario: Only the E2E scenarios related to current usage scenarios are recommended

What kind of recommendation do you want? (RETURN is to set all): 4

1. az policy definition create
Recommended reason: 78% users create a policy to set the security policy after creating the VM

2. az network vnet create
Recommended reason: 67% users create a vnet to manage virtual networks after creating the VM

3. az group create 
Recommended reason: 54% users create a resource group to manage resources after creating the VM

Which one is helpful to you? (If none, please input 0) : 2

Do you want to do it immediately? (y/n): y

Please input name (Name of the new policy definition): next-test
Please input mode (Mode of the policy definition): Indexed
Please input rules (Policy rules in JSON format, or a path to a file containing JSON rules): ...
...
```

### 4. senario
Dig into more E2E scenarios and recommend them to customers.

*For example, many users are associated with some RP scenarios, and we can design a new E2E Service by analyzing the data of these scenarios. When a user uses one of the RP, we can recommend the new E2E Service to him.*

```pwsh
(env) PS C:\project> az monitor log-analytics workspace create ...
Log-analytics workspace created successfully...

(env) PS C:\project> az next

Please select the type of recommendation you need:
1. all: It will intelligently analyze the types of recommendation you need, and may recommend multiple types of content to you
2. solution: Only the solutions to problems when errors occur are recommend
3. command: Only the commands with high correlation with previously executed commands are recommend
4. resource: Only the resources related to previously created resources are recommended
5. senario: Only the E2E scenarios related to current usage scenarios are recommended

What kind of recommendation do you want? (RETURN is to set all): 5

az monitor log-analytics solution create
Recommended reason: 72% users create a log-analytics solution to manage the workspace after creating the log-analytics workspace

Does it help for you? (y/n): y

Do you want to do it immediately? (y/n): y

Please input name (Name of the log-analytics solution): next-test
Please plan-product (Product name of the plan for solution): Container
Please input workspace (The name or resource ID of the log analytics workspace with which the solution will be linked): /subscription/xxx/...
...

```

## Bussiness process
![avatar](https://github.com/zhoxing-ms/image/blob/master/Annotation%202020-07-19%20150631.png)

#### 1. Use telemetry to collect and record the customer uasge of CLI. Since most of the required data already exists, the cold start problem of the algorithm is avoided.

#### 2. After a customer performed some operations, the coordination filtering algorithm will be used to collect and count the usage data from other users who have done the similar operations.

#### 3. Based on the data collected from other users, the merges are calculated, and the hotspots are sorted according to some weighted values. 

*For example, when recommending CDN-related usage, because the effect of CDN usage is affected by the region, so the data used by other users in the same region as the customer will be given higher weight.*

#### 4. The calculation of recommender system adds the configurability of using knowledge.

*For example:*<br/>
*(1) The correlation threshold of recommending content to users, time range of participating in calculation data can be configured*<br/>
*(2) In some special business, the recommending content can be added with the interception, filtering or supplementation according to business knowledge*<br/>
*(3) The recommendation preferences of some businesses can be set, such as aggressive recommendation and conservative recommendation*

#### 5. Produce the recommended content and give the reasons. Through the reasons for recommendation and the proportion of users to tell the customer the reasons why we recommend and the strength of the recommendation.

*For example, Recommended reason: 97% users create a new role assignment for a user, group, or service when this error is encountered*

#### 6. The user's adoption of the recommended content is collected by Telemetry as the feedback data, and then continuously optimizes the recommendation scheme of the recommendation system.

## Technical architecture
### 1. Overall architecture
In this recommendation scene, the real-time requirement of the recommendation content is not high (the updating frequency of the recommendation content is low), but the response speed of obtaining the recommendation results is higher.
Therefore, the architecture of offline computing can be considered to cache the calculated results into storage periodically and provide users with direct query recommendation results through the REST API of Web Service.
![avatar](https://github.com/zhoxing-ms/image/blob/master/1.png)

### 2. Technical selection of specific modules
* **CLI**: Send command records, command results and recommendation feedback to Telemetry.

* **Telemetry**: It is a log collection platform.

* **Kusto(ADE)**: Kusto is a fast, fully managed data analytics service for real-time analysis on big data.

* **Data Preproccess(Function Chaining)**: Data cleaning, conversion, preprocessing.

* **Schedule Task（Function Timer)**: Using collaborative filtering and hotspot ranking to calculate recommendation content offline.
  1. ***Full Benchmark Task***: Long period full calculation to ensure that the life cycle of the data involved in the calculation is reasonable and eliminate outdated recommendation content.If there is a new recommendation content, the original recommendation results will be overwritten; otherwise, the original recommendation results will be retained.
  2. ***Incremental Sync Task***: Short execution period, provide more real-time calculation of recommended content.

* **Result Storage (Cosmos)**: Store the calculation results as documents

* **Knowleage Base (Cosmos)**: Configurable business knowledge, data can come from internal input, customer feedback, and crawlers crawling data such as Github issue.

* **Web Service (Function HttpTrigger)**: Query and aggregate data of result storage and knowleage base to provide a Rest recommendation service(serverless) for CLI.

## Algorithm design
### 1. Offline calculation of recommended content
![avatar](https://github.com/zhoxing-ms/image/blob/master/2.png)

### 2. Real-time recommendation service
![avatar](https://github.com/zhoxing-ms/image/blob/master/3.png)

## Project plan
* In the early stage of the project, we will analyze the actual effect of data calculation, and first find out the data scenarios with good recommendation effect and strong correlation to conduct the key recommendation test (such as: solution and senario recommendation).
Then according to the customer's adoption feedback, the system is continuously optimized.

* In the middle stage of the project, we gradually try to solve some recommendation scenarios with higher difficulty, but which belonged to customer's pain points and were of great help to customers, so as to further enhance the recommendation ability of the system.

* In the later stage of the project, we will continue to improve the system to support more comprehensive recommendation scenarios, and have different personalized recommendation configurations according to the characteristics of different business scenarios.

* After the completion of the project, we began to cooperate with all parties to enhance the capability scope of the system. For example, working with the Alladin team to enable it to recommend examples. Working with other clinet terminals (such as: PowerShell, Terraform) to help them reuse the capabilities of our recommendation system as well.


## Other questions
1. Is there any other recommendation algorithm that is applicable and easy to implement?
2. What is the more appropriate technology stack for part modules
3. What is the development and maintenance costs that this system will bear 
4. Future monitoring and maintenance plan of the system
5. Support A/B test for recommendation effects in the future
