@data-qld-theme
Feature: Data QLD Theme

    Scenario: Lato font is implemented on homepage
        When I go to homepage
        Then I should see an element with xpath "//link[contains(@href,'https://fonts.googleapis.com/css?family=Lato')]"

    Scenario: Organisation is in fact spelled Organisation (as opposed to Organization)
        When I go to organisation page
        Then I should see "Organisation"
        And I should not see "Organization"

    Scenario: When I create an organisation without a description, the display should not mention its absence
        Given "SysAdmin" as the persona
        When I log in
        And I go to organisation page
        And I click the link with text that contains "Add Organisation"
        Then I should see "Create an Organisation"
        When I fill in "title" with "Org without description"
        And I press the element with xpath "//button[contains(@class, 'btn-primary')]"
        Then I should see "Org without description"
        And I should see "No datasets found"
        And I should not see "There is no description"

    Scenario: When I create an organisation with a description, there should be a Read More link
        Given "SysAdmin" as the persona
        When I log in
        And I go to organisation page
        And I click the link with text that contains "Add Organisation"
        Then I should see "Create an Organisation"
        When I fill in "title" with "Org with description"
        And I fill in "description" with "Some description or other"
        And I press the element with xpath "//button[contains(@class, 'btn-primary')]"
        Then I should see "Org with description"
        And I should see "No datasets found"
        And I should see "Some description or other"
        And I should see an element with xpath "//a[text() = 'read more' and contains(@href, '/organization/about/org-with-description')]"

    Scenario: Explore button does not exist on dataset detail page
        When I go to dataset page
        And I click the link with text that contains "A Wonderful Story"
        Then I should not see "Explore"

    Scenario: Explore button does not exist on dataset detail page
        When I go to organisation page
        Then I should see "Organisations are Queensland Government departments, other agencies or legislative entities responsible for publishing open data on this portal."

    Scenario: Register user password must be 10 characters or longer
        When I go to register page
        And I fill in "name" with "name"
        And I fill in "fullname" with "fullname"
        And I fill in "email" with "email@test.com"
        And I fill in "password1" with "pass"
        And I fill in "password2" with "pass"
        And I press "Create Account"
        Then I should see "Password: Your password must be 10 characters or longer"

    Scenario: Register user password must contain at least one number, lowercase letter, capital letter, and symbol
        When I go to register page
        And I fill in "name" with "name"
        And I fill in "fullname" with "fullname"
        And I fill in "email" with "email@test.com"
        And I fill in "password1" with "password1234"
        And I fill in "password2" with "password1234"
        And I press "Create Account"
        Then I should see "Password: Must contain at least one number, lowercase letter, capital letter, and symbol"

    Scenario: As a publisher, when I create a resource with an API entry, I can download it in various formats
        Given "TestOrgEditor" as the persona
        When I log in
        And I resize the browser to 1024x2048
        And I create a dataset with license "other-open" and "CSV" resource file "csv_resource.csv"
        And I wait for 10 seconds
        And I click the link with text that contains "Test Resource"
        Then I should see an element with xpath "//a[contains(@class, 'btn-primary') and contains(@href, 'download/csv_resource.csv') and contains(text(), 'Download (CSV)')]"
        When I press the element with xpath "//button[@data-toggle='dropdown']"
        Then I should see an element with xpath "//a[contains(@href, '/datastore/dump/') and contains(text(), 'CSV')]"
        Then I should see an element with xpath "//a[contains(@href, '/datastore/dump/') and contains(@href, 'format=tsv') and contains(text(), 'TSV')]"
        Then I should see an element with xpath "//a[contains(@href, '/datastore/dump/') and contains(@href, 'format=json') and contains(text(), 'JSON')]"
        Then I should see an element with xpath "//a[contains(@href, '/datastore/dump/') and contains(@href, 'format=xml') and contains(text(), 'XML')]"
