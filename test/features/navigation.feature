@smoke
Feature: Navigation

    Scenario: DQL-65 BDD-1 "Request data" link in header (non-logged in user)
        When I go to homepage
        # Make the comparison case-insensitive
        Then I should see an element with xpath "//a[contains(translate(., 'RD', 'rd'), "request data")]"

    Scenario: DQL-65 BDD-2 "Request data" link in header (logged in user)
        Given "Admin" as the persona
        When I log in
        Then I go to homepage
        # Make the comparison case-insensitive
        Then I should see an element with xpath "//a[contains(translate(., 'RD', 'rd'), "request data")]"

    Scenario: DQL-65 BDD-3 "Copyright" link in footer (non-logged in user)
        When I go to homepage
        Then I should see an element with xpath "//footer/div/ul/li/a[contains(string(), "Copyright")]"

    Scenario: DQL-65 BDD-4 "Disclaimer" link in footer (non-logged in user)
        When I go to homepage
        Then I should see an element with xpath "//footer/div/ul/li/a[contains(string(), "Disclaimer")]"

