## API LIST

|  API  | Description |
|------ |----- |
|[http://azure-cli.azurewebsites.net/orchestrators/recommendation](#recommendation)| Get recommended data|

## API Detail

* <span id = "recommendation">Get recommended data</span>

    * Request URL：http://azure-cli.azurewebsites.net/orchestrators/recommendation

    * Request Method：`POST`

    * Request Format：`JSON`

    * Response Format：`JSON`

    * Note：Get the recommendation data based on the customer's previous input

    * Request Parameters：

        | Name | Type | Is Require | Default value | Description |
        |----- |------| ---------  | ------------- | ----------- |
        |command | string | true | - | The command used by customer |
        |param | JSON | false | None | The parameters used by customer |
        |extra_data | JSON | false | None | Additional request data. Such as the error information passed in when recommending the solution to a problem |
        |type | int | false | 1 | Recommendation type, value range: 1.all 2.solution 3.command 4.resource 5.senario |
        |top_num | int | false | 5 | The maximum number of recommended items

    * Response Data:

        | Name | Type | Description |
        |----- |------|-------------|
        | status | int | Status code |
        | error_code | int | Error code |
        | data | JSON (list) | [Recommended data](#recommended_data) |

        <span id = "recommended_data">Recommended data</span>
        | Name | Type | Description |
        |----- |------|-------------|
        | command | string | Recommended command |
        | param   | JSON | Recommended parameters |
        | reason | string | Recommended reason |
        | ratio | float | Usage percentage |
        | score | float | Relevancy score |
       

    * Example：
        
        Request exeample:
        ```json
                {
                    "command": "az deployment create",
                    "param": "['-l', '-f', '-p']",
                    "extra_data": "'ErrorType': 'AuthorizationFailed', 'Message':'The client 'xxx' with object id 'xxx' does not have authorization to perform action...' ",
                    "type": 1,
                    "top_num": 10
                }
        ```

        Response exeample:
        ```json
                {
                    "status": 200,
                    "error_code": null,
                    "data": [
                        {
                            "command": "az role assignment create",
                            "param": "['--role', '--assignee']",
                            "reason": "The customers create a new role assignment for a user, group, or service when this error is encountered",
                            "ratio": 49,
                            "score": 95
                        },
                        {
                            "command": "az role assignment create",
                            "param": "['--role', '--assignee-object-id']",
                            "reason": "The customers create a new role assignment for a user, group, or service when this error is encountered",
                            "ratio": 32,
                            "score": 90
                        }
                    ]
                }
        ```

---
