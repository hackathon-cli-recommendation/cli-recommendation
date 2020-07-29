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

        | Name | Type | Is Require | Default value | Description | 
        |----- |------| ---------  | ------------- | ----------- |
        |command | string | true | - | The command used by customer |
        |arugments | JSON | false | None | The arugments used by customer |
        |extra_data | JSON | false | None | Additional request data. Such as the error information passed in when recommending the solution to a problem |
        |type | int | false | 1 | Recommendation type, value range: 1.all 2.solution 3.command 4.resource 5.senario |
        |top_num | int | false | 5 | The maximum number of recommended items

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
        https://cli-recommendation.azurewebsites.net/api/RecommendationService?command=az%20group%20create&top_num=2

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
