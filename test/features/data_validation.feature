@config
Feature: Data Validation

    Scenario Outline: As a sysadmin, admin and editor user of the dataset organisation I cannot see the  “</> JSON “ button
       Given "<User>" as the persona
        When I log in
        And I visit "dataset/new_resource/annakarenina"
        And I should not see an element with xpath "//a[contains(string(), '</> JSON')]"
    
        Examples: Users  
        | User              |
        | Admin             |
        | TestOrgAdmin      |
        | TestOrgEditor     |


     Scenario: As any user, I can view the “Data Schema” file URL link in the “Additional Info” table of resource read-view page. Clicking on the link will open the file in another browser window to view the schema file.
       Given "Admin" as the persona
        When I log in
        And I visit "dataset/new" 
        When I fill in title with random text
        When I fill in "notes" with "Description"
        When I fill in "version" with "1.0"
        When I fill in "author_email" with "test@me.com"
        When I press "Add Data"
        And I attach the file "test-resource_schemea.json" to "upload"  
        And I fill in "name" with "Test Resource"  
        And I execute the script "document.getElementById('field-format').value='JSON'"      
        And I fill in "description" with "Test Resource Description"  
        And I fill in "size" with "1"  
        And I attach the file "test-resource_schemea.json" to "schema_upload"
        And I press "Finish"
        When I wait for 1 seconds
        And I click the link with text that contains "Test Resource"
        And I click the link with text that contains "View Schema File"
        Then the browser's URL should contain "/schema/show/"