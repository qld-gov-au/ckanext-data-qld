
@reporting

Feature: AdminReporting

    Scenario: As an admin user of my organisation, I can view 'My Reports' tab in the dashboard and show the "Admin Report" with filters and table columns
        Given "TestOrgAdmin" as the persona
        When I log in
        And I visit "dashboard"
        And I click the link with text that contains "My Reports"
        And I click the link with text that contains "Admin Report"
        Then I should see an element with id "organisation"
        When I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see "Organisation: Test" within 1 seconds
        Then I should see an element with xpath "//tr/th[string()='Criteria' and position()=1]"
        Then I should see an element with xpath "//tr/th[string()='Figure' and position()=2]"

    
    Scenario: As an editor user of my organisation, I can view 'My Reports' tab in the dashboard but I cannot view the "Admin Report" link 
        Given "TestOrgEditor" as the persona
        When I log in
        And I visit "dashboard"
        And I click the link with text that contains "My Reports"
        Then I should not see an element with xpath "//a[contains(string(), 'Admin Report')]"


    Scenario: As an admin user of my organisation, when I view my admin report, I can verify the de-indentified datasets row exists
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        And I click the link with text that contains "Admin Report"
        And I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see an element with xpath "//tr[@id='de-identified-datasets']/td[contains(@class, 'metric-title') and contains(string(), 'De-identified Datasets') and position()=1]"
        Then I should see an element with xpath "//tr[@id='de-identified-datasets']/td[contains(@class, 'metric-data') and position()=2]"

    Scenario: As an admin user of my organisation, when I view my admin report, I can verify the over due datasets row exists correct
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        And I click the link with text that contains "Admin Report"
        And I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see an element with xpath "//tr[@id='overdue-datasets']/td[contains(@class, 'metric-title') and contains(string(), 'Overdue Datasets') and position()=1]"
        Then I should see an element with xpath "//tr[@id='overdue-datasets']/td[contains(@class, 'metric-data') and position()=2]"

    # TODO: Need to create a dataset with de-identified data
    # Scenario: As an admin user of my organisation, when I view my admin report, I can view the de-indentified datasets report
    #     Given "TestOrgAdmin" as the persona
    #     When I log in
    #     And I go to my reports page
    #     And I click the link with text that contains "Admin Report"
    #     And I press the element with xpath "//button[contains(string(), 'Show')]"
    #     And I click the link with text that contains "De-identified Datasets"
    #     Then I should see "Admin Report: De-identified Datasets" within 1 seconds

    # TODO: Need to create a dataset with overdue data. Not sure how because the validator will stop this
    # Scenario: As an admin user of my organisation, when I view my admin report, I can view the overdue datasets report
    #     Given "TestOrgAdmin" as the persona
    #     When I log in
    #     And I go to my reports page
    #     And I click the link with text that contains "Admin Report"
    #     And I press the element with xpath "//button[contains(string(), 'Show')]"
    #     And I click the link with text that contains "Overdue Datasets"
    #     Then I should see "Admin Report: Overdue Datasets" within 1 seconds
