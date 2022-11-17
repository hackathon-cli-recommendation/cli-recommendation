## Instructions for installing and trying `az scenario guide`


### What is it

`az scenario guide` is a search tool that can help you find and explore E2E scenario samples! </br>
It supports fuzzy search and sort the searched results according to the matching degree from high to low. </br>
It supports flexible search scenarios, you can specify the search scope and customize the matching rules. </br>
Moreover, it helps you execute these E2E scenarios more efficiently with a friendly walk-through process.

### How to install

- You need `azure-cli-core` version `2.20.0+`. Please run `az version` to check your version and use `az upgrade` to upgrade the version.
- Run `az scenario guide <keyword>` directly or install it by executing `az extension add --name scenario-guide`.

### How to play

1. Suppose you want to search the E2E scenario examples whose title or description related to app service or web app, please run:

    ```pwsh
    az scenario guide "app webapp service" --match-rule or
    ```

    - The `--match-rule` parameter allows you specify the matching rules for multi-keywords

    After the search is completed, you will see a list of related scenarios. You can select one to view details.

    ![Search App Service](https://github.com/ReaNAiveD/image/blob/master/scenario-guide-app-service.png)

2. Suppose we choose option 3: `Create an App Service app with deployment from GitHub` 

    This tool will display the commands contained in the scenario

    ![Search Scale Server Detailed Result](https://github.com/ReaNAiveD/image/blob/master/scenario-guide-app-service-detail.png)

    - You can visit the original documentation or CLI script to get more comprehensive context via the given link

3. Then you can execute the the command combinations for this scenario in an walk-through mode

    ![Search Scale Server Execution](https://github.com/ReaNAiveD/image/blob/master/scenario-guide-app-service-exec.png)

- Other Examples

    - Search scenario examples of how to connect the App Service to SQL Database

        ```pwsh
        az scenario guide "app service cosmos"
        ```

    - Search top 3 scenario examples whose commands contain keywords `cosmosdb` and `create` at the same time

        ```pwsh
        az scenario guide "network vnet subnet" --scope "command" --match-rule "and" --top 3
        ```

       - The `scope` parameter allows you specify the search scope
       - The `top` parameter allows you specify the number of results

### How to give feedback

`az scenario guide` is still under development, any suggestions or questions are welcome 😊: [issue for az scenario guide](https://github.com/hackathon-cli-recommendation/cli-recommendation/issues)
