# Storage Design Spec

## Summary

This document defines the storage schema that stores the recommendation data.

### Database (CosmosDB)
We use CosmosDB to store recommendation data.

- recommendation-without-arguments: store recommendation data assuming only using command as recommendation input.

  |   |   |   |   |
  |---|---|---|---|
  | id (command) | command (partition key) | totalCount | nextCommands |
  |   |   |   |   |

- ~~recommendation-with-arguments: store recommendation data assuming using both command and arugments as input.~~ (Don't support yet, and it will be supported if we use both command and arguments as recommendation input in the future.)

  |   |   |   |   |   |
  |---|---|---|---|---|
  | id (command + arguments) | command (partition key) | arguments | totalCount | nextCommands |

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