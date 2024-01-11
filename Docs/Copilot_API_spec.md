
* <span id = "Copilot">CLI Handler for Azure Copilot</span>

    * Request URL：
      - Pord: <Update later>
      - Dog Food: <Update later>

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

    * Example:

        Request Body:
        ```http
        {
             "question": "How do I deploy a python application on Azure?",
             "history": [
                     {
                         "role": "user",
                         "content": "a question from user"
                     },
                     {
                         "role": "assistant",
                         "content": "the answer of the question"
                     }
                 ],
             "top_num": 5,
             "type": "Mix"
         }
        ```

        Response Body:
        - Having high-quality answers
        ```json
        {
             "data": [
                 {
                     "history_msg": [ // only for GPT request
                         {
                             "role": "user", 
                             "content": "How do i create an kubernetes cluster with service mesh using Azure CLI"
                         }, 
                         {
                             "role": "assistant", 
                             "content": "{'Description': 'Create an Azure Kubernetes Service (AKS) cluster and install the Azure Service Operator', 'CommandSet': [{'command': 'aks create', 'arguments': ['--resource-group', '--name', '--node-count', '--enable-addons', '--generate-ssh-keys'], 'reason': 'Create an Azure Kubernetes Service (AKS) cluster.', 'example': 'az aks create --resource-group chatgpt-ResourceGroup-123456 --name chatgpt-AKS-123456 --node-count 2 --enable-addons monitoring --generate-ssh-keys'}, {'command': 'aks get-credentials', 'arguments': ['--resource-group', '--name'], 'reason': 'Get the credentials for the Kubernetes cluster.', 'example': 'az aks get-credentials --resource-group chatgpt-ResourceGroup-123456 --name chatgpt-AKS-123456'}, {'command': 'apply', 'arguments': ['-f'], 'reason': 'Install the Azure Service Operator on the cluster.', 'example': 'kubectl apply -f https://raw.githubusercontent.com/Azure/azure-service-operator/master/charts/azure-service-operator/crds.yaml'}], 'Reason': 'To create an Azure Kubernetes Service (AKS) cluster and install the Azure Service Operator, you need to create the AKS cluster, get the credentials for the cluster, and then apply the Azure Service Operator.'}"
                         }
                     ], 
                     "commandSet": [
                         {
                             "command": "aks create", 
                             "arguments": [
                                 "--resource-group", 
                                 "--name", 
                                 "--node-count", 
                                 "--enable-addons", 
                                 "--generate-ssh-keys"
                             ], 
                             "reason": "Create an Azure Kubernetes Service (AKS) cluster.", 
                             "example": "az aks create --resource-group chatgpt-ResourceGroup-123456 --name chatgpt-AKS-123456 --node-count 2 --enable-addons monitoring --generate-ssh-keys"
                         }, 
                         {
                             "command": "aks get-credentials", 
                             "arguments": [
                                 "--resource-group", 
                                 "--name"
                             ], 
                             "reason": "Get the credentials for the Kubernetes cluster.", 
                             "example": "az aks get-credentials --resource-group chatgpt-ResourceGroup-123456 --name chatgpt-AKS-123456"
                         }, 
                         {
                             "command": "apply", 
                             "arguments": [
                                 "-f"
                             ], 
                             "reason": "Install the Azure Service Operator on the cluster.", 
                             "example": "kubectl apply -f https://raw.githubusercontent.com/Azure/azure-service-operator/master/charts/azure-service-operator/crds.yaml"
                         }
                     ], 
                     "firstCommand": "aks create", 
                     "scenario": "Create an Azure Kubernetes Service (AKS) cluster and install the Azure Service Operator", 
                     "description": "To create an Azure Kubernetes Service (AKS) cluster and install the Azure Service Operator, you need to create the AKS cluster, get the credentials for the cluster, and then apply the Azure Service Operator."
                 }
             ], 
             "error": null,
             "status": 200, 
             "api_version": "1.1.0-alpha"
         }
        ```

        - No high-quality answers
        ```json
         {"data": [], "error": null, "status": 200, "api_version": "1.0.0"}
        ```

        - Bad request error
        ```json
         {"data": [], "error": "Bad Request Error", "status": 400, "api_version": "1.0.0"}
        ```

        - Service internal error
        ```json
         {"data": [], "error": "service internal error", "status": 500, "api_version": "1.0.0"}
        ```

---
