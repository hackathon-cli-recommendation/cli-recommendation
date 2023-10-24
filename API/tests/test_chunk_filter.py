import unittest

from common.service_impl.learn_knowledge_index import filter_chunks


class TestChunkFilter(unittest.TestCase):
    chunks_list = [
        {
            "command": "az vm create",
            "summary": "Create an Azure Virtual Machine.",
            "optional parameters": [
                {
                    "name": "--enable-vtpm",
                    "desc": "Enable vTPM.\naccepted values: false, true",
                },
                {
                    "name": "--encryption-at-host",
                    "desc": "Enable Host Encryption for the VM or VMSS. This will enable the encryption for all the disks including Resource/Temp disk at host itself.\naccepted values: false, true",
                },
                {
                    "name": "--ephemeral-os-disk",
                    "desc": "Allows you to create an OS disk directly on the host node, providing local disk performance and faster VM/VMSS reimage time.\naccepted values: false, true",
                },
                {
                    "name": "--ephemeral-os-disk-placement --ephemeral-placement",
                    "desc": "Only applicable when used with --ephemeral-os-disk. Allows you to choose the Ephemeral OS disk provisioning location.\naccepted values: CacheDisk, ResourceDisk",
                },
                {
                    "name": "--eviction-policy",
                    "desc": "The eviction policy for the Spot priority virtual machine. Default eviction policy is Deallocate for a Spot priority virtual machine.\naccepted values: Deallocate, Delete",
                },
                {
                    "name": "--generate-ssh-keys",
                    "desc": "Generate SSH public and private key files if missing. The keys will be stored in the ~/.ssh directory.\ndefault value: False",
                },
                {
                    "name": "--host",
                    "desc": "Resource ID of the dedicated host that the VM will reside in. --host and --host-group can't be used together.",
                },
                {
                    "name": "--host-group",
                    "desc": "Name or resource ID of the dedicated host group that the VM will reside in. --host and --host-group can't be used together.",
                },
            ],
            "score": 0.8216658,
        },
        {
            "command": "az vm create",
            "summary": "Create an Azure Virtual Machine.",
            "optional parameters": [
                {
                    "name": "--data-disk-delete-option",
                    "desc": "Specify whether data disk should be deleted or detached upon VM deletion. If a single data disk is attached, the allowed values are Delete and Detach. For multiple data disks are attached, please use &quot;&lt;data_disk&gt;=Delete &lt;data_disk2&gt;=Detach&quot; to configure each disk.",
                },
                {
                    "name": "--data-disk-encryption-sets",
                    "desc": "Names or IDs (space delimited) of disk encryption sets for data disks.",
                },
                {
                    "name": "--data-disk-sizes-gb",
                    "desc": "Space-separated empty managed data disk sizes in GB to create.",
                },
                {
                    "name": "--disable-integrity-monitoring",
                    "desc": "Disable the default behavior of installing guest attestation extension and enabling System Assigned Identity for Trusted Launch enabled VMs and VMSS.\ndefault value: False",
                },
                {
                    "name": "--disable-integrity-monitoring-autoupgrade",
                    "desc": "Disable auto upgrade of guest attestation extension for Trusted Launch enabled VMs and VMSS.\ndefault value: False",
                },
                {
                    "name": "--disk-controller-type",
                    "desc": "Specify the disk controller type configured for the VM or VMSS.\naccepted values: NVMe, SCSI",
                },
                {"name": "--edge-zone", "desc": "The name of edge zone."},
                {
                    "name": "--enable-agent",
                    "desc": "Indicates whether virtual machine agent should be provisioned on the virtual machine. When this property is not specified, default behavior is to set it to true. This will ensure that VM Agent is installed on the VM so that extensions can be added to the VM later.\naccepted values: false, true",
                },
                {
                    "name": "--enable-auto-update",
                    "desc": "Indicate whether Automatic Updates is enabled for the Windows virtual machine.\naccepted values: false, true",
                },
                {
                    "name": "--enable-hibernation",
                    "desc": "The flag that enable or disable hibernation capability on the VM.\naccepted values: false, true",
                },
                {
                    "name": "--enable-hotpatching",
                    "desc": "Patch VMs without requiring a reboot. --enable-agent must be set and --patch-mode must be set to AutomaticByPlatform.\naccepted values: false, true",
                },
                {
                    "name": "--enable-secure-boot",
                    "desc": "Enable secure boot.\naccepted values: false, true",
                },
            ],
            "score": 0.81135434,
        },
        {
            "command": "az vm create",
            "summary": "Create an Azure Virtual Machine.",
            "optional parameters": [
                {"name": "--os-disk-size-gb", "desc": "OS disk size in GB to create."},
                {
                    "name": "--os-type",
                    "desc": "Type of OS installed on a custom VHD. Do not use when specifying an URN or URN alias.\naccepted values: linux, windows",
                },
                {
                    "name": "--patch-mode",
                    "desc": "Mode of in-guest patching to IaaS virtual machine. Allowed values for Windows VM: AutomaticByOS, AutomaticByPlatform, Manual. Allowed values for Linux VM: AutomaticByPlatform, ImageDefault. Manual - You control the application of patches to a virtual machine. You do this by applying patches manually inside the VM. In this mode, automatic updates are disabled; the paramater --enable-auto-update must be false. AutomaticByOS - The virtual machine will automatically be updated by the OS. The parameter --enable-auto-update must be true. AutomaticByPlatform - the virtual machine will automatically updated by the OS. ImageDefault - The virtual machine's default patching configuration is used. The parameter --enable-agent and --enable-auto-update must be true.\naccepted values: AutomaticByOS, AutomaticByPlatform, ImageDefault, Manual",
                },
                {"name": "--plan-name", "desc": "Plan name."},
                {"name": "--plan-product", "desc": "Plan product."},
                {"name": "--plan-promotion-code", "desc": "Plan promotion code."},
                {"name": "--plan-publisher", "desc": "Plan publisher."},
                {
                    "name": "--platform-fault-domain",
                    "desc": "Specify the scale set logical fault domain into which the virtual machine will be created. By default, the virtual machine will be automatically assigned to a fault domain that best maintains balance across available fault domains. This is applicable only if the virtualMachineScaleSet property of this virtual machine is set. The virtual machine scale set that is referenced, must have platform fault domain count. This property cannot be updated once the virtual machine is created. Fault domain assignment can be viewed in the virtual machine instance view.",
                },
                {
                    "name": "--ppg",
                    "desc": "The name or ID of the proximity placement group the VM should be associated with.",
                },
            ],
            "score": 0.8105075,
        },
        {
            "command": "az vm create",
            "summary": "Create an Azure Virtual Machine.",
            "optional parameters": [
                {
                    "name": "--capacity-reservation-group --crg",
                    "desc": "The ID or name of the capacity reservation group that is used to allocate. Pass in &quot;None&quot; to disassociate the capacity reservation group. Please note that if you want to delete a VM/VMSS that has been associated with capacity reservation group, you need to disassociate the capacity reservation group first.",
                },
                {
                    "name": "--computer-name",
                    "desc": "The host OS name of the virtual machine. Defaults to the name of the VM.",
                },
                {
                    "name": "--count",
                    "desc": "Number of virtual machines to create. Value range is [2, 250], inclusive. Don't specify this parameter if you want to create a normal single VM. The VMs are created in parallel. The output of this command is an array of VMs instead of one single VM. Each VM has its own public IP, NIC. VNET and NSG are shared. It is recommended that no existing public IP, NIC, VNET and NSG are in resource group. When --count is specified, --attach-data-disks, --attach-os-disk, --boot-diagnostics-storage, --computer-name, --host, --host-group, --nics, --os-disk-name, --private-ip-address, --public-ip-address, --public-ip-address-dns-name, --storage-account, --storage-container-name, --subnet, --use-unmanaged-disk, --vnet-name are not allowed.",
                },
                {
                    "name": "--custom-data",
                    "desc": "Custom init script file or text (cloud-init, cloud-config, etc..).",
                },
                {
                    "name": "--data-disk-caching",
                    "desc": "Storage caching type for data disk(s), including 'None', 'ReadOnly', 'ReadWrite', etc. Use a singular value to apply on all disks, or use &lt;lun&gt;=&lt;vaule1&gt; &lt;lun&gt;=&lt;value2&gt; to configure individual disk.",
                },
            ],
            "score": 0.80799973,
        },
        {
            "command": "az vm create",
            "summary": "Create an Azure Virtual Machine.",
            "optional parameters": [
                {
                    "name": "--security-type",
                    "desc": "Specify the security type of the virtual machine.\naccepted values: ConfidentialVM, Standard, TrustedLaunch",
                },
                {
                    "name": "--size",
                    "desc": "The VM size to be created. See https://azure.microsoft.com/pricing/details/virtual-machines/ for size info.\ndefault value: Standard_DS1_v2\nvalue from: az vm list-sizes",
                },
                {
                    "name": "--specialized",
                    "desc": "Indicate whether the source image is specialized.\naccepted values: false, true",
                },
                {
                    "name": "--ssh-dest-key-path",
                    "desc": "Destination file path on the VM for the SSH key. If the file already exists, the specified key(s) are appended to the file. Destination path for SSH public keys is currently limited to its default value &quot;/home/username/.ssh/authorized_keys&quot; due to a known issue in Linux provisioning agent.",
                },
                {
                    "name": "--ssh-key-name",
                    "desc": "Use it as public key in virtual machine. It should be an existing SSH key resource in Azure.",
                },
                {
                    "name": "--ssh-key-values",
                    "desc": "Space-separated list of SSH public keys or public key file paths.",
                },
                {
                    "name": "--storage-account",
                    "desc": "Only applicable when used with --use-unmanaged-disk. The name to use when creating a new storage account or referencing an existing one. If omitted, an appropriate storage account in the same resource group and location will be used, or a new one will be created.",
                },
                {
                    "name": "--storage-container-name",
                    "desc": "Only applicable when used with --use-unmanaged-disk. Name of the storage container for the VM OS disk. Default: vhds.",
                },
            ],
            "score": 0.8079073,
        },
        {
            "command": "az vmware private-cloud create",
            "summary": "Create a private cloud.",
            "optional parameters": [
                {
                    "name": "--accept-eula",
                    "desc": "Accept the end-user license agreement without prompting.\ndefault value: False",
                },
                {
                    "name": "--internet",
                    "desc": "Connectivity to internet. Specify &quot;Enabled&quot; or &quot;Disabled&quot;.",
                },
                {
                    "name": "--location -l",
                    "desc": "Location. Values from: az account list-locations. You can configure the default location using az configure --defaults location=&lt;location&gt;.",
                },
                {
                    "name": "--mi-system-assigned",
                    "desc": "Enable a system assigned identity.\ndefault value: False",
                },
                {"name": "--nsxt-password", "desc": "NSX-T Manager password."},
                {
                    "name": "--secondary-zone",
                    "desc": "The secondary availability zone for the private cloud.",
                },
                {
                    "name": "--strategy",
                    "desc": "The availability strategy for the private cloud.\naccepted values: DualZone, SingleZone",
                },
                {
                    "name": "--tags",
                    "desc": "Space-separated tags: key[=value] [key[=value] ...]. Use &quot;&quot; to clear existing tags.",
                },
                {"name": "--vcenter-password", "desc": "VCenter admin password."},
                {
                    "name": "--yes",
                    "desc": "Delete without confirmation.\ndefault value: False",
                },
                {
                    "name": "--zone",
                    "desc": "The primary availability zone for the private cloud.",
                },
            ],
            "required parameters": [
                {
                    "name": "--cluster-size",
                    "desc": "Number of hosts for the default management cluster. Minimum of 3 and maximum of 16.",
                },
                {"name": "--name -n", "desc": "Name of the private cloud."},
                {
                    "name": "--network-block",
                    "desc": "A subnet at least of size /22. Make sure the CIDR format is conformed to (A.B.C.D/X) where A,B,C,D are between 0 and 255, and X is between 0 and 22.",
                },
                {
                    "name": "--resource-group -g",
                    "desc": "Name of resource group. You can configure the default group using az configure --defaults group=&lt;name&gt;.",
                },
                {"name": "--sku", "desc": "The product SKU."},
            ],
            "score": 0.80739456,
        },
        {
            "command": "az vm create",
            "summary": "Create an Azure Virtual Machine.",
            "optional parameters": [
                {
                    "name": "--priority",
                    "desc": "Priority. Use 'Spot' to run short-lived workloads in a cost-effective way. 'Low' enum will be deprecated in the future. Please use 'Spot' to deploy Azure spot VM and/or VMSS. Default to Regular.\naccepted values: Low, Regular, Spot",
                },
                {
                    "name": "--private-ip-address",
                    "desc": "Static private IP address (e.g. 10.0.0.5).",
                },
                {
                    "name": "--public-ip-address",
                    "desc": "Name of the public IP address when creating one (default) or referencing an existing one. Can also reference an existing public IP by ID or specify &quot;&quot; for None ('&quot;&quot;' in Azure CLI using PowerShell or --% operator). For Azure CLI using powershell core edition 7.3.4, specify  or &quot;&quot; (--public-ip-address  or --public-ip-address &quot;&quot;).",
                },
                {
                    "name": "--public-ip-address-allocation",
                    "desc": "accepted values: dynamic, static",
                },
                {
                    "name": "--public-ip-address-dns-name",
                    "desc": "Globally unique DNS name for a newly created public IP.",
                },
                {
                    "name": "--public-ip-sku",
                    "desc": "Public IP SKU. It is set to Basic by default. The public IP is supported to be created on edge zone only when it is 'Standard'.\naccepted values: Basic, Standard",
                },
                {
                    "name": "--role",
                    "desc": "Role name or id the system assigned identity will have.",
                },
                {
                    "name": "--scope",
                    "desc": "Scope that the system assigned identity can access.",
                },
                {
                    "name": "--secrets",
                    "desc": "One or many Key Vault secrets as JSON strings or files via @{path} containing [{ &quot;sourceVault&quot;: { &quot;id&quot;: &quot;value&quot; }, &quot;vaultCertificates&quot;: [{ &quot;certificateUrl&quot;: &quot;value&quot;, &quot;certificateStore&quot;: &quot;cert store name (only on windows)&quot;}] }].",
                },
            ],
            "score": 0.8059297,
        },
        {
            "command": "az scvmm vm create",
            "summary": "Create VM resource.",
            "optional parameters": [
                {
                    "name": "--no-wait",
                    "desc": "Do not wait for the long-running operation to finish.\ndefault value: False",
                },
                {
                    "name": "--tags",
                    "desc": "Space-separated tags: key[=value] [key[=value] ...]. Use &quot;&quot; to clear existing tags.",
                },
                {
                    "name": "--vm-template -t",
                    "desc": "Name or ID of the vm template for deploying the vm.",
                },
                {
                    "name": "--vmmserver -v",
                    "desc": "Name or ID of the vmmserver that is managing this resource.",
                },
            ],
            "score": 0.8053367,
        },
        {
            "command": "az scvmm vm create",
            "summary": "Create VM resource.",
            "optional parameters": [
                {"name": "--admin-password", "desc": "Admin password for the vm."},
                {
                    "name": "--availability-sets -a",
                    "desc": "List of the name or the ID of the availability sets for the vm.",
                },
                {
                    "name": "--cloud -c",
                    "desc": "Name or ID of the cloud for deploying the vm.",
                },
                {"name": "--cpu-count", "desc": "Number of desired vCPUs for the vm."},
                {
                    "name": "--disk",
                    "desc": "Disk overrides for the vm.Usage: --disk name=&lt;&gt; disk-size=&lt;&gt; template-disk-id=&lt;&gt; bus-type=&lt;&gt; bus=&lt;&gt; lun=&lt;&gt; vhd-type=&lt;&gt; qos-name=&lt;&gt; qos-id=&lt;&gt;.",
                },
                {
                    "name": "--dynamic-memory-enabled",
                    "desc": "If dynamic memory should be enabled.\naccepted values: false, true",
                },
                {
                    "name": "--dynamic-memory-max",
                    "desc": "DynamicMemoryMax in MBs for the vm.",
                },
                {
                    "name": "--dynamic-memory-min",
                    "desc": "DynamicMemoryMin in MBs for the vm.",
                },
                {
                    "name": "--inventory-item -i",
                    "desc": "Name or ID of the inventory item.",
                },
                {
                    "name": "--memory-size",
                    "desc": "Desired memory size in MBs for the vm.",
                },
                {
                    "name": "--nic",
                    "desc": "Network overrides for the vm.Usage: --nic name=&lt;&gt; network=&lt;&gt; ipv4-address-type=&lt;&gt; ipv6-address-type=&lt;&gt; mac-address-type=&lt;&gt; mac-address=&lt;&gt;.",
                },
            ],
            "required parameters": [
                {
                    "name": "--custom-location",
                    "desc": "Name or ID of the custom location that will manage this resource.",
                },
                {
                    "name": "--location -l",
                    "desc": "Location. Values from: az account list-locations. You can configure the default location using az configure --defaults location=&lt;location&gt;.",
                },
                {"name": "--name -n", "desc": "Name of the resource."},
                {
                    "name": "--resource-group -g",
                    "desc": "Name of resource group. You can configure the default group using az configure --defaults group=&lt;name&gt;.",
                },
            ],
            "score": 0.80468285,
        },
        {
            "command": "az vm create",
            "summary": "Create an Azure Virtual Machine.",
            "optional parameters": [
                {
                    "name": "--image",
                    "desc": "The name of the operating system image as a URN alias, URN, custom image name or ID, custom image version ID, or VHD blob URI. In addition, it also supports shared gallery image. Please use the image alias including the version of the distribution you want to use. For example: please use Debian11 instead of Debian.' This parameter is required unless using --attach-os-disk. Valid URN format: &quot;Publisher:Offer:Sku:Version&quot;. For more information, see https://docs.microsoft.com/azure/virtual-machines/linux/cli-ps-findimage.\nvalue from: az sig image-version show-shared, az vm image list, az vm image show",
                },
                {
                    "name": "--license-type",
                    "desc": "Specifies that the Windows image or disk was licensed on-premises. To enable Azure Hybrid Benefit for Windows Server, use 'Windows_Server'. To enable Multi-tenant Hosting Rights for Windows 10, use 'Windows_Client'. For more information see the Azure Windows VM online docs.\naccepted values: None, RHEL_BASE, RHEL_BASESAPAPPS, RHEL_BASESAPHA, RHEL_BYOS, RHEL_ELS_6, RHEL_EUS, RHEL_SAPAPPS, RHEL_SAPHA, SLES, SLES_BYOS, SLES_HPC, SLES_SAP, SLES_STANDARD, UBUNTU, UBUNTU_PRO, Windows_Client, Windows_Server",
                },
                {
                    "name": "--location -l",
                    "desc": "Location in which to create VM and related resources. If default location is not configured, will default to the resource group's location.",
                },
                {
                    "name": "--max-price",
                    "desc": "The maximum price (in US Dollars) you are willing to pay for a Spot VM/VMSS. -1 indicates that the Spot VM/VMSS should not be evicted for price reasons.",
                },
            ],
            "score": 0.8040971,
        },
    ]

    @staticmethod
    def _get_all_params_from_chunks(chunks, command):
        from functools import reduce
        chunks = [c for c in chunks if c['command'] == command]
        return [p["name"] for p in reduce(lambda a, b: a+b['optional parameters']+b.get('required parameters', []), [[]] + chunks)]

    def test_chunk_filter(self):
        raw_command = "az vm create --name --resource-group --image --generate-ssh-keys --license"
        result = filter_chunks(self.chunks_list, raw_command)
        params = self._get_all_params_from_chunks(result, 'az vm create')
        self.assertIn("--generate-ssh-keys", params)
        self.assertIn("--license-type", params)

    def test_chunk_filter_incorrect_sig(self):
        raw_command = "az create vm --name --resource-group --image --generate-ssh-keys --license"
        result = filter_chunks(self.chunks_list, raw_command)
        params = self._get_all_params_from_chunks(result, 'az vm create')
        self.assertIn("--generate-ssh-keys", params)
        self.assertIn("--license-type", params)
