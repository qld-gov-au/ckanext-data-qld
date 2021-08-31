@schema_metadata
Feature: Resource freshness

Scenario Outline: An editor, admin or sysadmin user, when I go to the dataset new page, the field field-next_update_due should not be visible
        Given "<User>" as the persona
        When I log in
        And I go to "/dataset/new"
        Then I shold not see an element with id "field-next_update_due"


        Examples: Users
        | User              |
        | Admin             |


Scenario Outline: An editor, admin or sysadmin user, when I go to the dataset new page, the field field-next_update_due should be visible
    Given "<User>" as the persona
    When I log in
    And I go to "/dataset/new"
    Then I should see an element with id "field-update_frequency"
    Then I should select an element with xpath "//*[@id='field-update_frequency']/option[6]"
    Then I shold see an element with id "field-next_update_due"


        Examples: Users
        | User              |
        | Admin             |



Scenario Outline: An editor, admin or sysadmin user, when I go to the edit dataset page, the field field-de_identified_data should be visible
    Given "<User>" as the persona
    When I log in
    And I go to "/dataset/edit/warandpeace"
    Then I should see an element with id "field-update_frequency"
    Then I should select an element with xpath "//*[@id='field-update_frequency']/option[6]"
    Then I shold see an element with id "field-next_update_due"

        Examples: Users
        | User              |
        | Admin             |
