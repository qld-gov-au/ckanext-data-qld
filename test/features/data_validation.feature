@config
Feature: Data Validation

    Scenario: As a sysadmin, admin and editor user of the dataset organisation I cannot see the  “</> JSON “ button
       Given "<User>" as the persona
        When I log in
        And I visit "dataset/new_resource/annakarenina"
        And I should not see an element with xpath "//a[contains(string(), '</> JSON')]"
        
        Examples: Users  
        | SysAdmin              |
        | TestOrgAdmin          |
        | TestOrgEditor         |