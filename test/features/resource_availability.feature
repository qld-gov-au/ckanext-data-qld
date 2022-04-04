@resource_visibility
Feature: Re-identification risk governance acknowledgement or Resource visibility


    Scenario: Sysadmin creates dataset with Contains de-identified data is YES and Resource visibility is TRUE and Acknowledgement is NO
        Given "SysAdmin" as the persona
        When I log in
        And I go to "/dataset/new"
        Then I fill in "title" with "Contains de-identified data YES visibility TRUE acknowledgment NO" 
        Then I fill in "notes" with "hide resource"
        Then I execute the script "document.getElementById('field-organizations').value=jQuery('#field-organizations option').filter(function () { return $(this).html() == 'Test Organisation'; }).attr('value')"
        Then I select "False" from "private"
        Then I fill in "version" with "1"
        Then I fill in "author_email" with "test@test.com"
        Then I select "YES" from "de_identified_data"
        And I press the element with xpath "//form[contains(@class, 'dataset-form')]//button[contains(@class, 'btn-primary')]"
        And I wait for 10 seconds
        Then I execute the script "document.getElementById('field-image-url').value='http://ckanext-data-qld.docker.amazee.io/'"
        Then I fill in "name" with "Resource hidden"
        Then I fill in "description" with "hide resource"
        Then I select "TRUE" from "resource_visibility"
        Then I select "NO" from "governance_acknowledgement"
        Then I press the element with xpath "//button[@value='go-metadata']"
        And I wait for 10 seconds
        Then I should see "Data and Resources"


    Scenario: Sysadmin creates dataset with Contains de-identified data is NO and Resource visibility is TRUE and Acknowledgement is NO
        Given "SysAdmin" as the persona
        When I log in
        And I go to "/dataset/new"
        Then I fill in "title" with "Contains de-identified data NO visibility TRUE acknowledgment NO" 
        Then I fill in "notes" with "dont hide"
        Then I execute the script "document.getElementById('field-organizations').value=jQuery('#field-organizations option').filter(function () { return $(this).html() == 'Test Organisation'; }).attr('value')"
        Then I select "False" from "private"
        Then I fill in "version" with "1"
        Then I fill in "author_email" with "test@test.com"
        Then I select "YES" from "de_identified_data"
        Then I press "save"
        And I wait for 10 seconds
        Then I execute the script "document.getElementById('field-image-url').value='http://ckanext-data-qld.docker.amazee.io/'"
        Then I fill in "name" with "Resource not hidden"
        Then I fill in "description" with "dont hide"
        Then I select "TRUE" from "resource_visibility"
        Then I select "NO" from "governance_acknowledgement"
        Then I press the element with xpath "//button[@value='go-metadata']"
        And I wait for 10 seconds
        Then I should see "Data and Resources"

    Scenario: Sysadmin creates dataset with Contains de-identified data is NO and Resource visibility is FALSE and Acknowledgement is NO
        Given "SysAdmin" as the persona
        When I log in
        And I go to "/dataset/new"
        Then I fill in "title" with "Contains de-identified data NO visibility FALSE acknowledgment NO" 
        Then I fill in "notes" with "hide resource"
        Then I execute the script "document.getElementById('field-organizations').value=jQuery('#field-organizations option').filter(function () { return $(this).html() == 'Test Organisation'; }).attr('value')"
        Then I select "False" from "private"
        Then I fill in "version" with "1"
        Then I fill in "author_email" with "test@test.com"
        Then I select "YES" from "de_identified_data"
        Then I press "save"
        And I wait for 10 seconds
        Then I execute the script "document.getElementById('field-image-url').value='http://ckanext-data-qld.docker.amazee.io/'"
        Then I fill in "name" with "Resource hidden"
        Then I fill in "description" with "hide resource"
        Then I select "FALSE" from "resource_visibility"
        Then I select "NO" from "governance_acknowledgement"
        Then I press the element with xpath "//button[@value='go-metadata']"
        And I wait for 10 seconds
        Then I should see "Data and Resources"

    Scenario: Sysadmin creates dataset with Contains de-identified data is YES and Resource visibility is TRUE and Acknowledgement is YES
        Given "SysAdmin" as the persona
        When I log in
        And I go to "/dataset/new"
        Then I fill in "title" with "Contains de-identified data YES visibility TRUE acknowledgment YES" 
        Then I fill in "notes" with "dont hide resource"
        Then I execute the script "document.getElementById('field-organizations').value=jQuery('#field-organizations option').filter(function () { return $(this).html() == 'Test Organisation'; }).attr('value')"
        Then I select "False" from "private"
        Then I fill in "version" with "1"
        Then I fill in "author_email" with "test@test.com"
        Then I select "YES" from "de_identified_data"
        Then I press "save"
        And I wait for 10 seconds
        Then I execute the script "document.getElementById('field-image-url').value='http://ckanext-data-qld.docker.amazee.io/'"
        Then I fill in "name" with "Resource not hidden"
        Then I fill in "description" with "dont hide resource"
        Then I select "FALSE" from "resource_visibility"
        Then I select "NO" from "governance_acknowledgement"
        Then I press the element with xpath "//button[@value='go-metadata']"
        And I wait for 10 seconds
        Then I should see "Data and Resources"

    # Removed old  labels and showing new ones
    Scenario Outline: User dont see a 'Visibility/Governance Acknowledgment' label
        Given "<User>" as the persona
        And I log in
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledgment-no"
        And I wait for 3 seconds
        Then I press the element with xpath "//a[@title='Resource hidden']"
        Then I should not see "Visibility/Governance Acknowledgment"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 


        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |
     
    Scenario Outline: Non logged in users dont see a hidden resource when de-identified data is YES and Resource visibility is TRUE and Acknowledgement is NO
        Given "TestOrgAdmin" as the persona
        And I log in
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-no"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource hidden']"
        Then I press the element with xpath "//a[@title='Resource hidden']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        Then I log out 
        And "TestOrgEditor" as persona
        And I log in
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-no"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource hidden']"
        Then I press the element with xpath "//a[@title='Resource hidden']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        Then I log out 
        And "User" as persona
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-no"
        And I wait for 3 seconds
        Then I should not see element with xpath "//a[@title='Resource hidden']"

    Scenario Outline: Non logged in users dont see a hidden resource when de-identified data is NO and Resource visibility is FALSE and Acknowledgement is NO
        Given "TestOrgAdmin" as the persona
        And I log in
        And I go to "/contains-de-identified-data-no-visibility-false-acknowledged-no"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource hidden']"
        Then I press the element with xpath "//a[@title='Resource hidden']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        Then I log out 
        And  "TestOrgEditor" as persona
        And I log in
        And I go to "/contains-de-identified-data-no-visibility-false-acknowledged-no"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource hidden']"
        Then I press the element with xpath "//a[@title='Resource hidden']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        Then I log out 
        And "User" as persona
        And I go to "/contains-de-identified-data-no-visibility-false-acknowledged-no"
        And I wait for 3 seconds
        Then I should not see element with xpath "//a[@title='Resource hidden']"


    Scenario Outline: Non logged in users see the resource when de-identified data is YES and Resource visibility is TRUE and Acknowledgement is YES
        Given "TestOrgAdmin" as the persona
        And I log in
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-yes"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource not hidden']"
        Then I press the element with xpath "//a[@title='Resource not hidden']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        Then I log out 
        And "TestOrgEditor" as persona
        And I log in
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-yes"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource not hidden']"
        Then I press the element with xpath "//a[@title='Resource not hidden']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        Then I log out 
        And "User" as persona
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-yes"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource not hidden']"
        Then I press the element with xpath "//a[@title='Resource not hidden']"
        Then I should not see "Resource visible"
        Then I should not see "Re-identification risk governance completed?" 


Scenario Outline: Non logged in users see the resource when de-identified data is YES and Resource visibility is TRUE and Acknowledgement is YES
        Given "TestOrgAdmin" as the persona
        And I log in
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-yes"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource not hidden']"
        Then I press the element with xpath "//a[@title='Resource not hidden']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        Then I log out 
        And "TestOrgEditor" as persona
        And I log in
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-yes"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource not hidden']"
        Then I press the element with xpath "//a[@title='Resource not hidden']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        Then I log out 
        And "User" as persona
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledged-yes"
        And I wait for 3 seconds
        Then I should see element with xpath "//a[@title='Resource not hidden']"
        Then I press the element with xpath "//a[@title='Resource not hidden']"
        Then I should not see "Resource visible"
        Then I should not see "Re-identification risk governance completed?" 


    ###
    # Create resource  with default values
    ###
    Scenario Outline: Create resource with default values
        Given "<User>" as the persona
        When I log in
        And I go to "/dataset/new_resource/contains-de-identified-data-yes-visibility-true-acknowledgment-no"
        Then I execute the script "document.getElementById('field-image-url').value='http://ckanext-data-qld.docker.amazee.io/'"
        Then I fill in "name" with "Resource created by <User> with default values"
        Then I fill in "description" with "description"
        Then I press "save"

          Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    ###
    # Check the resource  with default values
    ###
    Scenario Outline: Check the resource with default values
        Given "<User>" as the persona
        When I log in
        And I go to "/contains-de-identified-data-yes-visibility-true-acknowledgment-no"
        And I wait for 3 seconds
        Then I press the element with xpath "//a[@title='Resource created by <User> with default values']"
        Then I should see "Resource visible"
        Then I should see "Re-identification risk governance completed?" 
        

          Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |
