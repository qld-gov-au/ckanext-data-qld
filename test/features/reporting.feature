@reporting
Feature: Reporting

    Scenario Outline: As a user with admin or editor role capacity of an organisation, I can view 'My Reports' tab in the dashboard and show the organisation report with filters
        Given "<User>" as the persona
        When I log in
        And I visit "dashboard"
        And I click the link with text that contains "My Reports"
        Then I should see an element with id "organisation"
        And I should see an element with id "start_date"
        And I fill in "start_date" with "01-01-2019"
        And I should see an element with id "end_date"
        And I fill in "end_date" with "01-01-2020"
        When I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see "Organisation: Test" within 1 seconds
        And I should see "01/01/2019 - 01/01/2020" within 1 seconds
    
        Examples: Users  
        | User              |
        | TestOrgAdmin      |
        | TestOrgEditor     |


    Scenario: As a data request organisation admin, when I view my organisation report, I can verify the number of data requests is correct and increments
        Given "DataRequestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        And I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see an element with xpath "//td[@id='datarequests_total' and string()='0']"
        When I create a datarequest
        And I go to my reports page
        And I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see an element with xpath "//td[@id='datarequests_total' and string()='1']"


    Scenario: As an admin user of my organisation, when I view my organisation report, I can verify the number of dataset followers is correct and increments
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        Then I should see an element with xpath "//td[@id='dataset_followers' and string()='0']" 
        When I visit "/dataset/warandpeace"
        And I press the element with xpath "//a[@class='btn btn-success' and contains(string(), 'Follow')]"
        And I go to my reports page
        Then I should see an element with xpath "//td[@id='dataset_followers' and string()='1']"  


    Scenario: As an admin user of my organisation, when I view my organisation report, I can verify the number of dataset comments is correct and increments
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        Then I should see an element with xpath "//td[@id='dataset_comments' and string()='0']" 
        When I go to dataset "warandpeace" comments
        And I submit a comment with subject "Test subject" and comment "This is a test comment"
        And I go to my reports page
        Then I should see an element with xpath "//td[@id='dataset_comments' and string()='1']"


    Scenario: As an admin user of my organisation, when I view my organisation report, I can verify the number of data request comments is correct and increments
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        Then I should see an element with xpath "//td[@id='datarequest_comments' and string()='0']" 
        When I go to datarequest page
        And I click the link with text that contains "Test Request"
        And I click the link with text that contains "Comments"
        And I submit a comment with subject "Test subject" and comment "This is a test comment"
        And I go to my reports page
        Then I should see an element with xpath "//td[@id='datarequest_comments' and string()='1']"
