Controller_Version = "20.1.5"

demo_env_params= {
    'name' : 'avicontroller',
    'controller_username': "admin",
    'controller_password': "993HQSTPosL!",
    'controller_ip': "172.25.11.6",
    'controller_domain_name': 'avicontroller.cpod-santander.az-mad.cloud-garage.net',
    'tenant': "admin",
    'api_version': Controller_Version,
    'cloud': "nsx-overlay-data", # Name of NSX-T Cloud Integration as defined in the controller configuration
    'service_engine_group': "SEG-TEST",
    'headers': {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'X-AVI-VERSION': Controller_Version
            },
}
