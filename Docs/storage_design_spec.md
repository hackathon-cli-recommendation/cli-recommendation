# Storage Design Spec

## Summary

This document defines the storage schema that stores the recommendation data.

### Database (CosmosDB)
We use CosmosDB to store recommendation and scenario data.

- recommendation-without-arguments: store recommendation data assuming only using command as recommendation input.

  |   |   |   |   |
  |---|---|---|---|
  | id (command) | command (partition key) | totalCount | nextCommands |
  |   |   |   |   |

- ~~recommendation-with-arguments: store recommendation data assuming using both command and arugments as input.~~ (Don't support yet, and it will be supported if we use both command and arguments as recommendation input in the future.)

  |   |   |   |   |   |
  |---|---|---|---|---|
  | id (command + arguments) | command (partition key) | arguments | totalCount | nextCommands |

- e2e-scenario: store e2e scenarios that users can search for.

  |   |   |   |   |   | | |
  |---|---|---|---|---| --- |---|
  | id (scenario name) | firstCommand (partition key) | description | commandSet | source | source_url | update_time |

#### Entity in recommendation-without-arguments container
       

```json
        {
            "id": "9a040b9932eeaccb82c70a6154224393", // Generate by command
            "command": "az storage account create",
            "totalCount": 2000,
            "nextCommands":
            [
                {
                    "command": "az storage account show",
                    "arugments": ["-g", "-n"],
                    "count": "200",
                    "score": "90",
                    "reason": "",
                    "type": null
                },
                {
                    "command": "az storage account list",
                    "arugments": ["-g"],
                    "count": "150",
                    "score": "85",
                    "reason": "",
                    "type": null
                },
                {
                    "command": "az storage account show",
                    "arugments": ["-g"],
                    "count": "100",
                    "score": "80",
                    "reason": "",
                    "type": null
                }
            ]
        }
```

  | Property | Type | Description |
  | ------ | ------ | ------ |
  | command | string | The current command. |
  | totalCount | int | The total usage count of the current command. |
  | nextCommands | array | The list of recommended commands ordered by score. |
  | count | int | The usage count of the next command. |
  | score | int | The score of the next command. |
  | reason | string | The reason why this command is recommended. |
  | type | enum | The type of the next command. Currently is not supported. |


#### Entity in recommendation-with-arguments container
       

```json
        {
            "id": "9a040b9932eeaccb82c70a6154224393", // Generate by command + arguments
            "command": "az storage account create",
            "arguments": ["-g", "-n"],
            "totalCount": 2000,
            "nextCommands":
            [
                {
                    "command": "az storage account show",
                    "arugments": ["-g", "-n"],
                    "count": "200",
                    "score": "90",
                    "reason": "",
                    "type": null
                },
                {
                    "command": "az storage account list",
                    "arugments": ["-g"],
                    "count": "150",
                    "score": "85",
                    "reason": "",
                    "type": null
                },
                {
                    "command": "az storage account show",
                    "arugments": ["-g"],
                    "count": "100",
                    "score": "80",
                    "reason": "",
                    "type": null
                }
            ]
        }
```

  | Property | Type | Description |
  | ------ | ------ | ------ |
  | command | string | The current command. |
  | arguments | array | The arguments of the current command. |
  | totalCount | int | The total usage count of the current command. |
  | nextCommands | array | The list of recommended commands ordered by score. |
  | count | int | The usage count of the next command. |
  | score | int | The score of the next command. |
  | reason | string | The reason why this command is recommended. |
  | type | enum | The type of the next command. Currently is not supported. |

#### Entity in e2e-scenario container

```json
{
    "id": "Deploy some app",
    "firstCommand": "az appservice plan create",
    "description": "Create app in a Docker container",
    "commandSet": [
        {
            "command": "az appservice plan create",
            "arguments": [
                "--name",
                "--resource-group",
                "--sku",
                "--is-linux"
            ],
            "reason": "Create an App Service plan in S1 tier",
            "example": "az appservice plan create --name $appServicePlan --resource-group $resourceGroup --sku S1 --is-linux"
        },
        {
            "command": "az webapp create",
            "arguments": [
                "--name",
                "--resource-group",
                "--plan",
                "--runtime"
            ],
            "reason": "Create a web app. To see list of available runtimes, run 'az webapp list-runtimes --linux'",
            "example": "az webapp create --name $webapp --resource-group $resourceGroup --plan $appServicePlan --runtime NODE|14-lts"
        }
    ],
    "source": 1,
    "source_url": "https://github.com/xxxxx/yyyyy/zzzzz.sh",
    "update_time": "2022-07-12T03:58:55.367385",
}
```

  | Property | Type | Description |
  | ------ | ------ | ------ |
  | id (scenario name) | string | The name of scenario. |
  | firstCommand | string | The prototype of first command executed in this scenario. |
  | description | string | The description of this scenario. |
  | commandSet | list | The sequence of commands executed in this scenario. |
  | commandSet/command | str | The prototype of executed command. |
  | commandSet/arguments | list | The arguments of executed command. |
  | commandSet/reason | str | The description of executed command. |
  | commandSet/example | str | A example of executed command. |
  | source | int | How we get the scenario. Use 1 for document crawler, 2 for sample repository |
  | source_url | str | The link to original script or document. |
  | update_time | str | The time scenario last updated. |