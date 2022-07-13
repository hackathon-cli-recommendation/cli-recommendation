## API LIST

|  API  | Description |
|------ |----- |
|[https://cli-recommendation.azurewebsites.net/api/RecommendationService](#recommendation)| Get recommended data|

## API Detail

* <span id = "recommendation">Get recommended data</span>

    * Request URL：https://cli-recommendation.azurewebsites.net/api/RecommendationService

    * Request Method：`POST` or `GET`

    * Request Format：`JSON`

    * Response Format：`JSON`

    * Note：Get the recommendation data based on the customer's previous input

    * Request Parameters：

        | Name | Type | Is Require | Default value | Description | Supported |
        |----- |------| ---------  | ------------- | ----------- | --------- |
        |command | string | true | - | The command used by customer | Yes |
        |arugments | JSON | false | None | The arugments used by customer | No |
        |extra_data | JSON | false | None | Additional request data. Such as the error information passed in when recommending the solution to a problem | No |
        |type | int | false | 1 | Recommendation type, value range: 1.all 2.solution 3.command 4.resource 5.senario | Yes |
        |top_num | int | false | 5 | The maximum number of recommended items | Yes |

    * Response Data:

        | Name | Type | Description |
        |----- |------|-------------|
        | status | int | Status code |
        | error | JSON | Error information |
        | data | JSON (list) | [Recommended data](#recommended_data) |

        <span id = "recommended_data">Recommended data</span>
        | Name | Type | Description |
        |----- |------|-------------|
        | command | string | Recommended command |
        | arugments   | JSON | Recommended arugments |
        | reason | string | Recommended reason |
        | ratio | float | Usage percentage |
        | score | float | Relevancy score |
        |type | int | Recommendation type, value range: 1.all 2.solution 3.command 4.resource 5.senario |

    * Example：
        
        Request exeample:
        1. `POST` request:
        ```json
                {
                    "command": "az deployment create",
                    "arugments": "['-l', '-f', '-p']",
                    "extra_data": "'ErrorType': 'AuthorizationFailed', 'Message':'The client 'xxx' with object id 'xxx' does not have authorization to perform action...' ",
                    "type": 1,
                    "top_num": 10
                }
        ```
        
        2. `GET` request:
        https://cli-recommendation.azurewebsites.net/api/RecommendationService?command=az%20deployment%20create&top_num=2&type=1

        Response exeample:
        ```json
                {
                    "status": 200,
                    "error": null,
                    "data": [
                        {
                            "command": "az role assignment create",
                            "arugments": "['--role', '--assignee']",
                            "reason": "The customers create a new role assignment for a user, group, or service when this error is encountered",
                            "ratio": 0.49,
                            "score": 95,
                            "type": 1
                        },
                        {
                            "command": "az role assignment create",
                            "arugments": "['--role', '--assignee-object-id']",
                            "reason": "The customers create a new role assignment for a user, group, or service when this error is encountered",
                            "ratio": 0.32,
                            "score": 90,
                            "type": 1
                        }
                    ]
                }
        ```

---

* <span id = "scenario-search">Search scenario data</span>

    * Request URL：https://cli-recommendation.azurewebsites.net/api/SearchService

    * Request Method：`POST` or `GET`

    * Request Format：`JSON`

    * Response Format：`JSON`

    * Note：Get scenario search result based on scenario of command keyword

    * Request Parameters：

        | Name    | Type          | Is Require | Default value | Description                                          | Supported |
        | ------- | ------------- | ---------- | ------------- | ---------------------------------------------------- | --------- |
        | keyword | string        | true       | -             | The search keyword user searches                     | Yes       |
        | type    | int or string | false      | all           | Search type, value range: 1.all 2.scenario 3.command | Yes       |
        | top_num | int           | false      | 5             | The maximum number of search results                 | Yes       |

    * Response Data:

        | Name   | Type        | Description                     |
        | ------ | ----------- | ------------------------------- |
        | status | int         | Status code                     |
        | error  | JSON        | Error information               |
        | data   | JSON (list) | [Search Result](#search_result) |

        <span id = "search_result">Search Result</span>
        | Name               | Type       | Description                               |
        | ------------------ | ---------- | ----------------------------------------- |
        | id                 | string     | Recommended command                       |
        | source             | int        | Scenario source                           |
        | commandSet         | json(list) | command sequence in scenario              |
        | scenario           | string     | scnario name                              |
        | firstCommand       | string     | first command in scenario                 |
        | source_url         | string     | link to origin file                       |
        | update_time        | string     | when the scenario updated                 |
        | description        | string     | scenario description                      |
        | score      | float      | Search score                              |
        | highlights | json       | highlight related content with &lt;em&gt; |

    * Example：
        
        1. Search Scenario Example:
        Request:
        ```http
                POST http://localhost:7071/api/SearchService HTTP/1.1
                Content-Type: application/json

                {
                    "keyword": "scale+server",
                    "top": 5,
                    "type": "Scenario"
                }
        ```

        Response
        ```json
        {
            "data": [
                {
                    "id": "az postgres server create | scale postgresql server - Azure CLI Samples",
                    "source": 1,
                    "commandSet": [
                        {
                        "command": "az postgres server create",
                        "arguments": [
                            "--name",
                            "--resource-group",
                            "--location",
                            "--admin-user",
                            "--admin-password",
                            "--sku-name"
                        ],
                        "reason": "Create a PostgreSQL server in the resource group\\nName of a server maps to DNS name and is thus required to be globally unique in Azure.",
                        "example": "az postgres server create --name $server --resource-group $resourceGroup --location $location --admin-user $login --admin-password $password --sku-name $sku"
                        },
                        {
                        "command": "az postgres server update",
                        "arguments": [
                            "--resource-group",
                            "--name",
                            "--sku-name"
                        ],
                        "reason": "Scale up the server by provisionining more vCores within the same tier",
                        "example": "az postgres server update --resource-group $resourceGroup --name $server --sku-name $scaleUpSku"
                        }
                    ],
                    "scenario": "scale postgresql server - Azure CLI Samples",
                    "firstCommand": "az postgres server create",
                    "source_url": "https://github.com/Azure-Samples/azure-cli-samples/blob/master/postgresql/scale-postgresql-server/scale-postgresql-server.sh",
                    "update_time": "2022-07-12T03:00:25.262Z",
                    "description": "Monitor and scale a single PostgreSQL server",
                    "score": 3.9647722,
                    "highlights": {
                        "scenario": [
                            "<em>scale</em> postgresql <em>server</em> - Azure CLI Samples"
                        ]
                    }
                }
            ],
            "error": null,
            "status": 200
        }
        ```

---

