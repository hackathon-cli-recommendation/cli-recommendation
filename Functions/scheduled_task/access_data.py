from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.data.helpers import dataframe_from_result_table

cluster = "https://ddazureclients.kusto.windows.net/"
client_id = "<insert here your AAD application id>"
client_secret = "<insert here your AAD application key>"
authority_id = "72f988bf-86f1-41af-91ab-2d7cd011db47"

# kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(cluster, client_id, client_secret, authority_id)
kcsb = KustoConnectionStringBuilder.with_aad_device_authentication(cluster)
client = KustoClient(kcsb)
client.execute("RawEventsAzCli", ".show version")