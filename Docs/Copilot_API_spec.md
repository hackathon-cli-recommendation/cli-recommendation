
* <span id = "Copilot">CLI Handler for Azure Copilot</span>

    * Request URL：
      - Pord: https://clitools-copilot-fdcvbhgkfkhpata5.z01.azurefd.net/api/copilotservice
      - Dog Food: https://cli-copilot-dogfood.azurewebsites.net/api/copilotservice

    * Request Method：`POST`

    * Request Format：`JSON`

    * Response Format：`JSON`

    * Note：Get the Azure CLI scripts or commands for management operations of Azure resources and the end-to-end scenarios containing multiple different Azure resources

    * Request Parameters：

        | Name    | Type          | Is Require | Default value | Description                                          | Notes     |
        | ------- | ------------- | ---------- | ------------- | ---------------------------------------------------- | --------- |
        | question | string       | true       | -             | Customer questions                                   | -         |
        | history  | string       | false      | -             | Chat history                                         | -         |
        | top_num  | int          | false      | 5             | The maximum number of search results                 | -         |
        | type     | enum (Mix/knowledgeSearch/GPTGeneration) | false      | Mix | The service type, the mix mode is to first calls "knowledgeSearch". If "knowledgeSearch" does not meet expectations, it will fall back to "GPTGeneration" | Under normal circumstances, it is not recommended to send this parameter, as our server will control the service type by default         |

    * Response Data:

        | Name         | Type         | Description                               |
        |--------------|--------------| ----------------------------------------- |
        | status       | int          | Status code                               |
        | error        | JSON         | Error information                         |
        | api_version  | string       | The API version (x.x.x) parsed from environment variables. the MAJOR version for major upgrades, the MINOR version for new feature, and the PATCH version for bugfix |
        | data         | JSON (list)  | [Copilot Result](#copilot_result)           |

        <span id = "copilot_result">Copilot Result</span>
        | Name               | Type       | Description                               |
        | ------------------ | ---------- | ----------------------------------------- |
        | scenario           | string     | scnario name                              |
        | source             | int        | Scenario source: 1. sample repo 2.document crawler 3.expert input |
        | commandSet         | JSON (list) | [Command Set](#command_set)              |
        | firstCommand       | string     | first command in scenario                 |
        | source_url         | string     | link to origin file (knowlegde search only) |
        | update_time        | string     | when the scenario updated                 |
        | description        | string     | scenario description                      |
        | score              | float      | Search score (knowlegde search only)                              |
        | highlights         | json       | highlight related content with &lt;em&gt; (knowlegde search only) |
  
        <span id = "command_set">Command Set</span>
        | Name               | Type       | Description                               |
        | ------------------ | ---------- | ----------------------------------------- |
        | command            | string     | command name                              |
        | arguments          | string     | arguments                                 |
        | reason             | string     | command description                       |
        | example            | string     | command example                           |
        
