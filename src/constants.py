"""
Central module for application constants.
This helps avoid duplication and ensures consistency across the codebase.
"""

class Modes:
    """Constants for canvas interaction modes."""
    SELECT = "select"
    ADD_DEVICE = "add_device"
    DELETE = "delete"
    DELETE_SELECTED = "delete_selected"
    ADD_BOUNDARY = "add_boundary" 
    ADD_CONNECTION = "add_connection"

class DeviceTypes:
    """Constants for device types."""
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    SERVER = "server"
    CLOUD = "cloud"
    WORKSTATION = "workstation"
    GENERIC = "generic"
    
    # Risk Management Framework (RMF) information for each device type
    RMF_INFO = {
        ROUTER: {
            "impact_level": "Moderate",
            "security_categorization": "High",
            "typical_stig_compliance": "DISA Router STIG",
            "authorization_requirements": "Boundary device, requires ATO",
            "common_controls": ["AC-4", "SC-7", "SC-8", "SI-4"],
            "rmf_priority": "High",
            "description": "Network routing devices that forward traffic between different networks."
        },
        SWITCH: {
            "impact_level": "Moderate",
            "security_categorization": "Moderate",
            "typical_stig_compliance": "DISA Switch STIG",
            "authorization_requirements": "Infrastructure device, requires ATO",
            "common_controls": ["AC-3", "AC-6", "SC-7", "SC-8"],
            "rmf_priority": "Moderate",
            "description": "Network switching devices that connect devices within a local network."
        },
        FIREWALL: {
            "impact_level": "High",
            "security_categorization": "High",
            "typical_stig_compliance": "DISA Firewall STIG",
            "authorization_requirements": "Security device, requires ATO",
            "common_controls": ["AC-4", "SC-7", "SC-8", "SI-4", "CM-7"],
            "rmf_priority": "Critical",
            "description": "Network security devices that control and filter traffic between networks."
        },
        SERVER: {
            "impact_level": "High",
            "security_categorization": "High",
            "typical_stig_compliance": "DISA OS STIG (based on OS type)",
            "authorization_requirements": "Server system, requires ATO",
            "common_controls": ["AC-2", "AC-3", "AC-6", "AU-2", "AU-6", "CM-6", "IA-2"],
            "rmf_priority": "High",
            "description": "Computing systems that provide services and resources to clients across a network."
        },
        CLOUD: {
            "impact_level": "Moderate",
            "security_categorization": "Moderate",
            "typical_stig_compliance": "FedRAMP Compliance",
            "authorization_requirements": "Cloud service, requires FedRAMP",
            "common_controls": ["AC-2", "AC-3", "AC-17", "SC-7", "SC-8", "SC-13"],
            "rmf_priority": "High",
            "description": "Cloud-based services and resources accessed over the internet."
        },
        WORKSTATION: {
            "impact_level": "Low",
            "security_categorization": "Low",
            "typical_stig_compliance": "DISA OS STIG (based on OS type)",
            "authorization_requirements": "End-user system, covered by site ATO",
            "common_controls": ["AC-2", "AC-3", "AC-7", "SC-28", "SI-3"],
            "rmf_priority": "Low",
            "description": "End-user computing devices used by personnel to access network resources."
        },
        GENERIC: {
            "impact_level": "Varies",
            "security_categorization": "Varies",
            "typical_stig_compliance": "Depends on device type",
            "authorization_requirements": "Varies by specific device",
            "common_controls": ["AC-3", "IA-2"],
            "rmf_priority": "Moderate",
            "description": "Generic network devices that don't fit other categories."
        }
    }
    
    @classmethod
    def get_all_types(cls):
        """Return a list of all device types."""
        return [
            cls.ROUTER,
            cls.SWITCH,
            cls.FIREWALL,
            cls.SERVER,
            cls.CLOUD,
            cls.WORKSTATION,
            cls.GENERIC
        ]
    
    @classmethod
    def get_rmf_info(cls, device_type):
        """Return RMF information for a specific device type.
        
        Args:
            device_type: The device type to get RMF information for
            
        Returns:
            dict: RMF information dictionary for the specified device type
        """
        return cls.RMF_INFO.get(device_type, cls.RMF_INFO[cls.GENERIC])

class RoutingStyle:
    """Constants for connection routing styles."""
    STRAIGHT = "straight"
    ORTHOGONAL = "orthogonal"
    CURVED = "curved"
    
    @classmethod
    def get_all_styles(cls):
        """Return a list of all routing styles."""
        return [
            cls.STRAIGHT,
            cls.ORTHOGONAL,
            cls.CURVED
        ]

class ConnectionTypes:
    """Constants for connection types."""
    # Basic connection types
    ETHERNET = "ethernet"
    SERIAL = "serial"
    FIBER = "fiber"
    WIRELESS = "wireless"
    
    # Enterprise connection types
    GIGABIT_ETHERNET = "gigabit_ethernet"
    TEN_GIGABIT_ETHERNET = "10gig_ethernet"
    FORTY_GIGABIT_ETHERNET = "40gig_ethernet"
    HUNDRED_GIGABIT_ETHERNET = "100gig_ethernet"
    FIBER_CHANNEL = "fiber_channel"
    MPLS = "mpls"
    POINT_TO_POINT = "p2p"
    VPN = "vpn"
    SDWAN = "sdwan"
    SATELLITE = "satellite"
    MICROWAVE = "microwave"
    BLUETOOTH = "bluetooth"
    CUSTOM = "custom"

    # Dictionary mapping connection types to display names
    DISPLAY_NAMES = {
        ETHERNET: "Ethernet",
        SERIAL: "Serial",
        FIBER: "Fiber",
        WIRELESS: "Wireless",
        GIGABIT_ETHERNET: "Gigabit Ethernet (1GbE)",
        TEN_GIGABIT_ETHERNET: "10 Gigabit Ethernet (10GbE)",
        FORTY_GIGABIT_ETHERNET: "40 Gigabit Ethernet (40GbE)",
        HUNDRED_GIGABIT_ETHERNET: "100 Gigabit Ethernet (100GbE)",
        FIBER_CHANNEL: "Fiber Channel",
        MPLS: "MPLS",
        POINT_TO_POINT: "Point-to-Point",
        VPN: "VPN Tunnel",
        SDWAN: "SD-WAN",
        SATELLITE: "Satellite",
        MICROWAVE: "Microwave",
        BLUETOOTH: "Bluetooth",
        CUSTOM: "Custom Connection"
    }

    # Dictionary mapping connection types to default bandwidth values
    DEFAULT_BANDWIDTHS = {
        ETHERNET: "100 Mbps",
        SERIAL: "2 Mbps",
        FIBER: "1 Gbps",
        WIRELESS: "54 Mbps",
        GIGABIT_ETHERNET: "1 Gbps",
        TEN_GIGABIT_ETHERNET: "10 Gbps",
        FORTY_GIGABIT_ETHERNET: "40 Gbps",
        HUNDRED_GIGABIT_ETHERNET: "100 Gbps",
        FIBER_CHANNEL: "16 Gbps",
        MPLS: "Variable",
        POINT_TO_POINT: "100 Mbps",
        VPN: "50 Mbps",
        SDWAN: "Variable",
        SATELLITE: "15 Mbps",
        MICROWAVE: "1 Gbps",
        BLUETOOTH: "3 Mbps",
        CUSTOM: ""
    }

    @classmethod
    def get_all_types(cls):
        """Return a list of all connection types."""
        return [
            cls.ETHERNET,
            cls.SERIAL,
            cls.FIBER, 
            cls.WIRELESS,
            cls.GIGABIT_ETHERNET,
            cls.TEN_GIGABIT_ETHERNET,
            cls.FORTY_GIGABIT_ETHERNET,
            cls.HUNDRED_GIGABIT_ETHERNET,
            cls.FIBER_CHANNEL,
            cls.MPLS,
            cls.POINT_TO_POINT,
            cls.VPN,
            cls.SDWAN,
            cls.SATELLITE,
            cls.MICROWAVE,
            cls.BLUETOOTH,
            cls.CUSTOM
        ]