## Collected `az next` and `az interactive` feedback data

### Storage
Collected by Telemetry

### Data scheme

#### Custom Identification
| Field          | Content                                                        | Value                                                                              |
|----------------|----------------------------------------------------------------|------------------------------------------------------------------------------------|
| MachineId      | The id of the customer's machine, each device has a unique id. | 64-bit hex char (9eb810f6158f99693851fd6f203a2b7248c81563be91bd310ca03c0c10cf08c9) |


#### Recommendation Properties

Stored at Properties["context.default.azurecli.recommendation"]

| Field                       | Content                                                | Value                                                                                                                                 |
|-----------------------------|--------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| request_type                | The recommendation type that the user filters          | 1:all 2:solution 3:command 4:scenario 5:search                                                                                        |
| option                      | Options adopted by users                               | str (item value: -1:no result; 0:not adopted; a$:accept the $st command; b$:accept the $st scenario; c$: accepted the $st from search |
| trigger_commands            | The last 1-2 commands that triggers the recommendation | command name                                                                                                                          |
| error_info                  | Error infos when using the recommendation of Solution  | error info                                                                                                                            |
| recommendations_list        | The list of all recommendations                        | list                                                                                                                                  |                                                       
| recommendations_source_list | The data source of recommendation items                | list (item value: 1:knowledge base 2:caculation 3:Aladdin)                                                                            |
| recommendations_type_list   | The type of recommendation items                       | list (item value: 2:solution 3:command 4:scenario)                                                                                    |
| accepted_recommend_source   | The data source of adoption accepted recommendation    | 1:knowledge base 2:caculation 3:Aladdin                                                                                               |
| accepted_recommend_type     | The type of accepted recommendation                    | 2:solution 3:command 4:scenario                                                                                                       |
| accepted_recommend          | The contents accepted by users                         | command name/scenario name                                                                                                            |
| is_personalized             | Whether the accepted recommend is a personalized one   | bool                                                                                                                                  |

### Sample
```
Adopt E2E Scenario:
{
    "api_version": null,
    "recommendation_properties": {
        "request_type": 1,
        "option": "b2",
        "trigger_commands": [
            "group create",
            ""
        ],
        "error_info": "None",
        "recommendations_list": [
            {
                "scenario": "Create a cluster with Data Lake Storage Gen2"
            },
            {
                "scenario": "Route policy state change events to Event Grid"
            },
            {
                "scenario": "Mount an Azure file share in Azure Container Instances"
            },
            {
                "scenario": "Send events from private container registry to Event Grid"
            },
            {
                "scenario": "Setup geodr and failover database failover group"
            }
        ],
        "recommendations_source_list": [
            "4"
        ],
        "recommendations_type_list": [
            "4"
        ],
        "accepted_recommend_source": 4,
        "accepted_recommend_type": 4,
        "accepted_recommend": "Route policy state change events to Event Grid",
        "is_personalized": "None"
    }
}

Adopt Command:
{
    "api_version": null,
    "recommendation_properties": {
        "request_type": 1,
        "option": "a2",
        "trigger_commands": [
            "group create",
            "group create"
        ],
        "error_info": "None",
        "recommendations_list": [
            {
                "command": "group show"
            },
            {
                "command": "group list"
            },
            {
                "command": "keyvault create"
            },
            {
                "scenario": "Create a cluster with Data Lake Storage Gen2"
            },
            {
                "scenario": "Route policy state change events to Event Grid"
            },
            {
                "scenario": "Mount an Azure file share in Azure Container Instances"
            },
            {
                "scenario": "Send events from private container registry to Event Grid"
            },
            {
                "scenario": "Setup geodr and failover database failover group"
            }
        ],
        "recommendations_source_list": [
            "2",
            "3",
            "4"
        ],
        "recommendations_type_list": [
            "3",
            "4"
        ],
        "accepted_recommend_source": 3,
        "accepted_recommend_type": 3,
        "accepted_recommend": "group list",
        "is_personalized": "None"
    }
}

Adopt Solution:
1#1#group create#the following arguments are required: --location/-l#1 2#2#1#2#group create#--name -l

Not adopt:
1#0#webapp create# #1 2#4 3# # # # 

No recommendation:
1#-1#storage share#_share_ is misspelled or not recognized by the system.# # # # # # 
```

## Summarize the effect of `az next` recommendation items

### Storage
Store through Cosmos, offline caculation. It will be used to optimize the recommendation capabilities.

### Data scheme
```
{
   "command": "group show",                 // the last command that triggers the recommendation (latest_command)
   "total_adoption_rate": 0.30,             // total adoption rate (total_adoption_count/total_rec_count)
   "total_rec_count": 33000,                // total recommendation count (option>=0)
   "total_adoption_count": 10000,           // total adoption count (option>0),
   "operate_adoption_rate": 0.30,           // operate adoption rate (operate_adoption_count/operate_rec_count)
   "operate_rec_count": 5000,               // operate recommendation count (option>=0 & rec_type in (3,4)),
   "operate_adoption_count": 10000,         // operate adoption count (option>0 & adoption_type in (3,4)),
   "solution_adoption_rate": 0.30,          // solution adoption rate (solution_adoption_count/solution_rec_count)
   "solution_rec_count": 5000,              // solution recommendation count (option>=0 & rec_type=2),
   "solution_adoption_count": 10000,        // solution adoption count (option>0 & adoption_type=2),
   "adoption_content": [                    // adopted content distribution
      {
         "content": "group create",         // recommendation content (content)
         "proportion_in_total": 0.36,       // proportion in all recommendations (adoption_count/operate_rec_count)
         "proportion_in_adoption": 0.5,     // proportion in adoption (adoption_count/operate_adoption_count)
         "adoption_count" 3600,             // adoption count (count group by content,adoption_type)
         "average_position": 4,             // recommended average position (sum(option)/adoption_count)
         "type": 3                          // item type (adoption_type)
      },
      {
         "content": "Monitor an App Service app with web server logs",
         "proportion_in_total": 0.36,
         "proportion_in_adoption": 0.5,                          
         "adoption_count" 3600,                                        
         "average_position": 3,                                    
         "type": 4                                                 
      },
      {
         "content": "group create",                                          
         "proportion_in_total": 0.36,       // adoption rate (adoption_count/solution_rec_count) 
         "proportion_in_adoption": 0.5,     // The proportion in adoption (adoption_count/solution_adoption_count)                                            
         "adoption_count" 3600,                                               
         "average_position": 3,                                             
         "type": 2,   
         "error_info"："the following arguments are required: --location/-l"  // matching error messages (error_info)
      }
   ],
   "source_adoption":{                                  // adoption rates from different sources
      "Aladdin_adoption_count": 2700,                   // aladdin adoption count (adoption_source=3)
      "Aladdin_rec_count": 10000,                       // aladdin recommendation count (3 in rec_source)
      "Aladdin_proportion_in_total": 0.27,              // proportion in all recommendations (Aladdin_adoption_count/operate_rec_count)
      "Aladdin_proportion_in_adoption": 0.27,           // proportion in adoption (Aladdin_adoption_count/operate_adoption_count)
      "Aladdin_proportion_of_accuracy" 0.27,            // proportion_of_accuracy (Aladdin_adoption_count/Aladdin_rec_count)
      "caculation_adoption_count": 2700,                // caculation adoption count (adoption_source=2)
      "caculation_rec_count": 10000,                    // caculation recommendation count (2 in rec_source)
      "caculation_proportion_in_total": 0.27,           // proportion in all recommendations (caculation_adoption_count/operate_rec_count)
      "caculation_proportion_in_adoption": 0.27,        // proportion in adoption (caculation_adoption_count/operate_adoption_count)
      "caculation_proportion_of_accuracy" 0.27,         // proportion_of_accuracy (caculation_adoption_count/caculation_rec_count)
      "knowledgebase_adoption_count": 2700,             // knowledgebase adoption count (adoption_source=1)
      "knowledgebase_rec_count": 10000,                 // knowledgebase recommendation count (1 in rec_source)
      "knowledgebase_proportion_in_total": 0.27,        // proportion in all recommendations (knowledgebase_adoption_count/operate_rec_count)
      "knowledgebase_proportion_in_adoption": 0.27,     // proportion in adoption (knowledgebase_adoption_count/operate_adoption_count)
      "knowledgebase_proportion_of_accuracy" 0.27,      // proportion_of_accuracy (knowledgebase_adoption_count/knowledgebase_rec_count)
   },
   "type_adoption":{                                    // adoption rates from different types
      "command_adoption_count": 2700,                   // command adoption count (adoption_type=3)
      "command_rec_count": 10000,                       // command recommendation count (3 in rec_type)
      "command_proportion_in_total": 0.27,              // proportion in all recommendations (command_adoption_count/operate_rec_count)
      "command_proportion_in_adoption": 0.27,           // proportion in adoption (command_adoption_count/operate_adoption_count)
      "command_proportion_of_accuracy" 0.27,            // proportion_of_accuracy (command_adoption_count/command_rec_count)
      "scenario_adoption_count": 2700,                   // scenario adoption count (adoption_type=4)
      "scenario_rec_count": 10000,                       // scenario recommendation count (4 in rec_type)
      "scenario_proportion_in_total": 0.27,              // proportion in all recommendations (scenario_adoption_count/operate_rec_count)
      "scenario_proportion_in_adoption": 0.27,           // proportion in adoption (scenario_adoption_count/operate_adoption_count)
      "scenario_proportion_of_accuracy" 0.27,            // proportion_of_accuracy (scenario_adoption_count/scenario_rec_count)
      "solution_adoption_count": 2700,                   // solution adoption count (adoption_type=2)
      "solution_rec_count": 10000,                       // solution recommendation count (2 in rec_type)
      "solution_proportion_in_total": 0.27,              // proportion in all recommendations (solution_adoption_count/operate_rec_count)
      "solution_proportion_in_adoption": 0.27,           // proportion in adoption (solution_adoption_count/operate_adoption_count)
      "solution_proportion_of_accuracy" 0.27,            // proportion_of_accuracy (solution_adoption_count/solution_rec_count)
   }
}
```

## Overall summary data

### Storage
PowerBI/Dashboard

### Data scheme
```
{
   "PV": 10000,                                         // the number of times "az next" was executed
   "UV": 1000,                                          // the number of users using "az next"
   "retention_rate": 0.42                               // Usage retention rate
   "total_adoption_rate": 0.30,                         // total adoption rate (total_adoption_count/total_rec_count)
   "total_rec_count": 33000,                            // total recommendation count (option>=0)
   "total_adoption_count": 10000,                       // total adoption count (option>0),
   "total_req_count": 10000,                            // total request count (all)
   "total_covering_rate": 1,                            // total covering rate (total_rec_count/total_req_count)
   "operate_adoption_rate": 0.30,                       // operate adoption rate (operate_adoption_count/operate_rec_count)
   "operate_rec_count": 5000,                           // operate recommendation count (option>=0 & rec_type in (3,4)),
   "operate_adoption_count": 10000,                     // operate adoption count (option>0 & adoption_type in (3,4)),
   "operate_req_count": 10000,                          // operate request count (all)
   "operate_covering_rate": 1,                          // operate covering rate (operate_rec_count/operate_req_count)
   "solution_adoption_rate": 0.30,                      // solution adoption rate (solution_adoption_count/solution_rec_count)
   "solution_rec_count": 5000,                          // solution recommendation count (option>=0 & rec_type=2),
   "solution_adoption_count": 10000,                    // solution adoption count (option>0 & adoption_type=2),
   "solution_req_count": 10000,                         // solution request count (all)
   "solution_covering_rate": 1,                         // solution covering rate (solution_rec_count/solution_req_count)
   "source_adoption":{                                  // adoption rates from different sources
      "Aladdin_adoption_count": 2700,                   // aladdin adoption count (adoption_source=3)
      "Aladdin_rec_count": 10000,                       // aladdin recommendation count (3 in rec_source)
      "Aladdin_proportion_in_total": 0.27,              // proportion in all recommendations (Aladdin_adoption_count/operate_rec_count)
      "Aladdin_proportion_in_adoption": 0.27,           // proportion in adoption (Aladdin_adoption_count/operate_adoption_count)
      "Aladdin_proportion_of_accuracy" 0.27,            // proportion of accuracy (Aladdin_adoption_count/Aladdin_rec_count)
      "caculation_adoption_count": 2700,                // caculation adoption count (adoption_source=2)
      "caculation_rec_count": 10000,                    // caculation recommendation count (2 in rec_source)
      "caculation_proportion_in_total": 0.27,           // proportion in all recommendations (caculation_adoption_count/operate_rec_count)
      "caculation_proportion_in_adoption": 0.27,        // proportion in adoption (caculation_adoption_count/operate_adoption_count)
      "caculation_proportion_of_accuracy" 0.27,         // proportion of accuracy (caculation_adoption_count/caculation_rec_count)
      "knowledgebase_adoption_count": 2700,             // knowledgebase adoption count (adoption_source=1)
      "knowledgebase_rec_count": 10000,                 // knowledgebase recommendation count (1 in rec_source)
      "knowledgebase_proportion_in_total": 0.27,        // proportion in all recommendations (knowledgebase_adoption_count/operate_rec_count)
      "knowledgebase_proportion_in_adoption": 0.27,     // proportion in adoption (knowledgebase_adoption_count/operate_adoption_count)
      "knowledgebase_proportion_of_accuracy" 0.27,      // proportion of accuracy (knowledgebase_adoption_count/knowledgebase_rec_count)
   },
   "type_adoption":{                                    // adoption rates from different types
      "command_adoption_count": 2700,                   // command adoption count (adoption_type=3)
      "command_rec_count": 10000,                       // command recommendation count (3 in rec_type)
      "command_proportion_in_total": 0.27,              // proportion in all recommendations (command_adoption_count/operate_rec_count)
      "command_proportion_in_adoption": 0.27,           // proportion in adoption (command_adoption_count/operate_adoption_count)
      "command_proportion_of_accuracy" 0.27,            // proportion of accuracy (command_adoption_count/command_rec_count)
      "scenario_adoption_count": 2700,                   // scenario adoption count (adoption_type=4)
      "scenario_rec_count": 10000,                       // scenario recommendation count (4 in rec_type)
      "scenario_proportion_in_total": 0.27,              // proportion in all recommendations (scenario_adoption_count/operate_rec_count)
      "scenario_proportion_in_adoption": 0.27,           // proportion in adoption (scenario_adoption_count/operate_adoption_count)
      "scenario_proportion_of_accuracy" 0.27,            // proportion of accuracy (scenario_adoption_count/scenario_rec_count)
      "solution_adoption_count": 2700,                   // solution adoption count (adoption_type=2)
      "solution_rec_count": 10000,                       // solution recommendation count (2 in rec_type)
      "solution_proportion_in_total": 0.27,              // proportion in all recommendations (solution_adoption_count/operate_rec_count)
      "solution_proportion_in_adoption": 0.27,           // proportion in adoption (solution_adoption_count/operate_adoption_count)
      "solution_proportion_of_accuracy" 0.27,            // proportion of accuracy (solution_adoption_count/solution_rec_count)
   },
   "average_adoption_position": 3.5,                     // average adoption position (sum(position if position>0)/total_adoption_count)
   "most_adoption_position": 3.5,                        // most adoption position (max(count group by position))           
   "highest_adoption_rate":{                             // highest adoption items
       "operation":[
           {
                "content": "group create",         // recommendation content (content) 
                "adoption_rate": 0.36,             // adoption rate
                "type": 3                          // item type (adoption_type)
            }
       ],
       "solution":[
           {
                "content": "group create",                                          
                "adoption_rate": 0.36,                                          
                "type": 2,   
                "error_info"："the following arguments are required: --location/-l"  // matching error messages (error_info)
           }
       ]
   },
   "lowest_adoption_rate":{                        // lowest adoption items
      "operation":[
           {
                "content": "group create",         // recommendation content (content) 
                "adoption_rate": 0.36,             // adoption rate
                "type": 3                          // item type (adoption_type)
            }
       ],
       "solution":[
           {
                "content": "group create",                                          
                "adoption_rate": 0.36,                                          
                "type": 2,   
                "error_info"："the following arguments are required: --location/-l"  // matching error messages (error_info)
           }
       ]
   },
   "most_used_command":{
      "operation":[
               {
                  "content": "group create",         // recommendation content (content) 
                  "adoption_rate": 0.36,             // adoption rate
                  "type": 3                          // item type (adoption_type)
               }
            ],
       "solution":[
           {
                "content": "group create",                                          
                "adoption_rate": 0.36,                                          
                "type": 2,   
                "error_info"："the following arguments are required: --location/-l"  // matching error messages (error_info)
           }
       ]
   }
}
```

## Collected `az search-scenario` feedback data

### Storage
Collected by Telemetry

### Data scheme
|   Field   |   Content   |   Value   |
|  -------  |  ---------  |  -------  |
| search_type | The search type that the user used | 1:all 2:scenairo 3:command |
| option | Options adopted by users | -1:no results 0:not adopted >0:adopted |
| keyword | The keywords that used to search | string |
| rec_source | The source of scenario | space separated array (item value: 1:sample repository 2:crawler) |
| adoption_source | The data source of adoption | 1:sample repository 2:crawler |
| scenario_name | The scenario adopted by users | string |
| description | The adopted scenario description | string |

> Use `\sharp` to escape `#`

### Sample

```
Adopt Searched Scenario
2#1#scale server#1 1 1 1#1#Scale postgresql server#Monitor and scale a single PostgreSQL server

Not Adopted
2#0#scale server#1 1 1 1# # # 

No Result
2#-1#az webapp log tail# # # # 
```