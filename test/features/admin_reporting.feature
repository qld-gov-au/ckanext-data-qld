
@reporting

Feature: AdminReporting

    Scenario Outline: As a user with admin or editor role capacity of an organisation, I can view 'My Reports' tab in the dashboard and show the "Admin Report" with filters and table columns
        Given "<User>" as the persona
        When I log in
        And I visit "dashboard"
        And I click the link with text that contains "My Reports"
        And I click the link with text that contains "Admin Report"
        Then I should see an element with id "organisation"
        When I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see "Organisation: Test" within 1 seconds
        Then I should see an element with xpath "//tr/th[string()='Criteria' and position()=1]"
        Then I should see an element with xpath "//tr/th[string()='Figure' and position()=2]"

        Examples: Users
            | User          |
            | TestOrgAdmin  |
            | TestOrgEditor |

    Scenario: As an admin user of my organisation, when I view my admin report, I can verify the de-indentified datasets row exists
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        And I click the link with text that contains "Admin Report"
        And I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see an element with xpath "//tr[@id='de-identified-datasets']/td[contains(@class, 'metric-title')]/a[string()='De-identified Datasets' and position()=1]"
        Then I should see an element with xpath "//tr[@id='de-identified-datasets']/td[contains(@class, 'metric-data')]/a[position()=1]"

    Scenario: As an admin user of my organisation, when I view my admin report, I can verify the over due datasets row exists correct
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        And I click the link with text that contains "Admin Report"
        And I press the element with xpath "//button[contains(string(), 'Show')]"
        Then I should see an element with xpath "//tr[@id='overdue-datasets']/td[contains(@class, 'metric-title')]/a[string()='Overdue Datasets' and position()=1]"
        Then I should see an element with xpath "//tr[@id='overdue-datasets']/td[contains(@class, 'metric-data')]/a[position()=1]"

    Scenario: As an admin user of my organisation, when I view my admin report, I can view the de-indentified datasets report
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        And I click the link with text that contains "Admin Report"
        And I press the element with xpath "//button[contains(string(), 'Show')]"
        And I click the link with text that contains "De-identified Datasets"
        Then I should see "Report: De-identified Datasets" within 1 seconds

    Scenario: As an admin user of my organisation, when I view my admin report, I can view the overdue datasets report
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to my reports page
        And I click the link with text that contains "Admin Report"
        And I press the element with xpath "//button[contains(string(), 'Show')]"
        And I click the link with text that contains "Overdue Datasets"
        Then I should see "Report: Overdue Datasets" within 1 seconds
