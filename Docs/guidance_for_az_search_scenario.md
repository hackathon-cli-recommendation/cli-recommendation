## Instructions for installing and trying `az search-scenario`

`az search-scenario` helps users to easily search for e2e scenario samples. 

### What to solve

It's difficult for users to search e2e scenario samples through conceptual doc. They have to find the corresponding conceptual doc and then extract the required sample from the doc that contains too much disparate information. 

### How to solve

`az search-scenario` service maintains a data source of hundreds of collected e2e scenario samples. Users can search e2e scenarios directly through the CLI. `az search-scenario` supports two types of search. Users can search e2e scenarios through scenario description keywords or through related commands. `az search-scenario` also supports hybrid search. 

### How to install

1. You need `azure-cli-core` version 2.37.0+. Run `az version` to check your version. Use `az upgrade` to upgrade.
2. Install `az search-scenario <keyword>` directly by executing `az extension add --name search-scenario`.
3. (Optinal) Run `az config set core.collect_telemetry=True` to turn on telemetry. This will help us improve e2e scenarios based on your usage data.

### How to play

1. In this part, I will show you with a example on search scenario samples. Assume that you need some cases about `WEB APP`(or `APP SERVICE` in some cases). Execute following command in terminal. 

    ```pwsh
    az search-scenario "web app service" --match-rule or
    ```

    - The `type` parameter specifies the type to search. You can also use `command` to search for scenarios related to the entered command or use `all` to enable hybrid search. The default of `type` is `all`. 
    - The `top` parameter specifies the number of results to display. The default of `top` is `5`. 

    The search will take a while to complete. After the search is complete, you can see a list of related scenarios. You can then select one to view details.

    ![Search App Service](https://github.com/ReaNAiveD/image/blob/master/search-scenario-app-service.png)

2. Enter `3` to learn about "Create an App Service app with deployment from GitHub". 

    ```pwsh
    ? Please select your option (if none, enter 0): 3
    ```

    `az search-scenario` will display the commands contained in the scenario. 

    If you found nothing help, you can alse enter `0` to quit `az search-scenario`. 

    ![Search Scale Server Detailed Result](https://github.com/ReaNAiveD/image/blob/master/search-scenario-app-service-detail.png)

    You can access the original documentation or script via the given link. 

3. Then you can execute the scenario in an interactive mode if the configuration `search_scenario.execute_in_prompt` is set to `True`. This is helpful to newcomers. 

    ![Search Scale Server Execution](https://github.com/ReaNAiveD/image/blob/master/search-scenario-app-service-exec.png)

### How to give feedback

`az search-scenario` is under active development. Any suggestions or questions are welcome: [issue for az search-scenario](https://github.com/hackathon-cli-recommendation/cli-recommendation/issues). 
