# Example of site setup with 2 apps
Using avi_config Ansible Role\
Deploys two VirtualServices (apps) in a NSX-T Cloud\
- It require following precreated objects to work (used as variables in creds.yaml file)\
        - NSX-Cloud integration named nsx-overlay-data\
        - Service Engine Group named SEG-TEST in above cloud\
        - NSX-T Tier 1 Logical Router named T1-DATA


```
# List of applications to be included as part of the site.
#

- import_playbook: applications/app1/app.yml

- import_playbook: applications/app2/app.yml
```

Use following to deploy (be careful with whitespaces in the path)
        
```
ansible-playbook site_applications.yml --extra-vars "site_dir=`pwd`"
```
Remove with 
```
ansible-playbook site_applications.yml --extra-vars "site_dir=`pwd` avi_config_state=absent"
```
