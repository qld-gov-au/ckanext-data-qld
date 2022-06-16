@resource_freshness
Feature: Resource freshness

    Scenario Outline: An editor, admin or sysadmin user, when I go to the dataset new page, the text 'Next update due' should not be visible
        Given "<User>" as the persona
        When I log in
        And I go to "/dataset/new"
        Then I should not see "Next update due"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    Scenario Outline: An editor, admin or sysadmin user, when I go to the dataset new page and select 'monthly' update frequency, then the text 'Next update due' should be visible
        Given "<User>" as the persona
        When I log in
        And I go to "/dataset/new"
        And I select "monthly" from "update_frequency"
        Then I should see "Next update due"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    Scenario Outline: An editor, admin or sysadmin user, when I go to the edit dataset page, the text 'Next update due' should be visible
        Given "<User>" as the persona
        When I log in
        And I go to "/dataset/edit/warandpeace"
        And I select "monthly" from "update_frequency"
        Then I should see "Next update due"
        When I fill in "next_update_due" with "01/01/1970"
        And I press the element with xpath "//form[contains(@class, 'resource-form')]//button[contains(@class, 'btn-primary')]"
        And I wait for 3 seconds
        Then I should be able to patch dataset "warandpeace" via the API

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |
