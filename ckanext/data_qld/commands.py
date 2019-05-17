import ckan.model as model
import ckan.plugins.toolkit as toolkit
import sqlalchemy
import re
import requests
from datetime import datetime

from ckan.model.package import Package
from ckan.model.package_extra import PackageExtra

from ckan.lib.cli import CkanCommand
from pprint import pprint
from ckanapi import LocalCKAN, ValidationError

_and_ = sqlalchemy.and_


class MigrateExtras(CkanCommand):
    '''Migrates
    '''

    summary = __doc__.split('\n')[0]

    def __init__(self,name):

        super(MigrateExtras,self).__init__(name)

    def get_package_ids(self):
        # @Todo: Load all packages
        # package_ids = ['f0742c45-995d-4299-9d79-f0b777e2d0eb']
        # return package_ids
        session = model.Session
        package_ids = []

        packages = (
            session.query(
                Package
            )
        )

        for pkg in packages:
            package_ids.append(pkg.id)

        return package_ids

    def update_package(self, package_id, security_classification, data_driven_application, version, author_email, notes, resources):
        # https://github.com/ckan/ckanext-scheming/issues/158
        destination = LocalCKAN()
        destination.action.package_patch(id=package_id,
                                         security_classification=security_classification,
                                         data_driven_application=data_driven_application,
                                         version=version,
                                         author_email=author_email,
                                         notes=notes,
                                         resources=resources)

    def try_parsing_date(self, text, resource_id):
        for fmt in ('%d/%m/%Y', '%d/%m/%y', '%d.%m.%Y', '%d.%m.%y', '%d-%m-%Y', '%d-%m-%y', '%Y-%m-%d', '%y-%m-%d', '%Y/%m/%d', '%y/%m/%d', '%d-%B-%Y', '%d-%B-%y', '%d %B %Y', '%d %B %y'): #'%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y', '%y'
            try:
                # print ('Attempting to parse date: ' + text + ' with format: ' + fmt)
                parsed_date = datetime.strptime(text.strip(), fmt)      
                #  print ('Parsed date: ' + parsed_date.strftime('%Y-%m-%d') + ' with format: ' + fmt)    
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError as ve:
                # print ('ValueError: ', ve)
                pass
        print ("'" + str(resource_id)+"',")
        return 'default_expiration_date'

    def command(self):
        '''

        :return:
        '''
        self._load_config()

        context = {'session': model.Session}

        # Step 1: Get all the package IDs
        package_ids = self.get_package_ids()

        for package_id in package_ids:

            # print(package_id)

            # Set some defaults
            default_security_classification = "PUBLIC"
            default_data_driven_application = "NO"
            default_version = "1.0"
            default_author_email = "opendata@qld.gov.au"
            default_expiration_date = "2020-06-30"          
            default_size = 1000
            resources = []

            pkg = toolkit.get_action('package_show')(context, {
                'id': package_id
            })

            #pprint(pkg)        

            # Update the 'Expiration date' field in Resources
            if pkg['resources']:
                expiration_date = default_expiration_date
                size = default_size  
                         
                for resource in pkg['resources']:   
                    # print ('resources %s' % resource['id'])               
                    if 'Expiration date' in resource:
                        # print ('This resource has Expiration date: ' + resource['Expiration date'])                     
                        if resource['Expiration date']:
                            expiration_date = self.try_parsing_date(resource['Expiration date'], resource['id'])  
                        else:                            
                            expiration_date = default_expiration_date                       
                    elif 'ExpirationDate' in resource:                                             
                        if resource['ExpirationDate']:
                            expiration_date = self.try_parsing_date(resource['ExpirationDate'], resource['id'])  
                        else:                            
                            expiration_date = default_expiration_date                        
                    elif 'expiration_date' in resource:  
                        print ('expiration_date ' + resource['id'])                                  
                        if resource['expiration_date']:
                            expiration_date = self.try_parsing_date(resource['expiration_date'], resource['id'])  
                        else:                            
                            expiration_date = default_expiration_date                        
                    elif 'expiration-date' in resource:                                         
                        if resource['expiration-date']:
                            expiration_date = self.try_parsing_date(resource['expiration-date'], resource['id'])  
                        else:                            
                            expiration_date = default_expiration_date
                    
                    else:
                        expiration_date = default_expiration_date
                    
                    if 'size' in resource:
                        size = resource['size'] if resource['size'] != None and resource['size'] != '0 bytes' else default_size 
                        # print ('size : ' + str(size)) 
                                        
                    if 'name' in resource:
                        name = resource['name']
                        # print ('name : ' + name)         

                    if 'description' in resource:
                        description = resource['description'] or name
                        # print ('description : ' + description)  
                  
                    
                    update_resource = {
                        "id": resource['id'],
                        "expiration_date": expiration_date,
                        "size": size,
                        "name": name,
                        "description": description                        
                        }
                    resources.append(update_resource)

            # Go through the packages and check for presence of 'Security classification'
            # and 'Used in data-driven application' extras
            security_classification = default_security_classification
            data_driven_application = default_data_driven_application
            version = default_version
            author_email = default_author_email  
      
        
            if pkg.get('extras', None):
           
                for extra in pkg['extras']:
                    if extra['key'] == 'Security classification':
                        # print ('Found ' + extra['key'] + ' | value: ' + extra['value'])
                        security_classification = extra['value'] or default_security_classification
                    elif extra['key'] in ['Used in data-driven application']:
                        # print ('Found ' + extra['key'] + ' | value: ' + extra['value'])
                        data_driven_application = extra['value'] or default_data_driven_application                 
            
            if 'version' in pkg:
                version = pkg['version'] or default_version

            if 'author_email' in pkg:
                author_email = pkg['author_email'] or default_author_email

            if 'notes' in pkg:
                notes = pkg['notes'] or pkg['title']                 
            
            self.update_package(package_id, security_classification, data_driven_application, version, author_email, notes, resources)  
          
        return 'SUCCESS'
