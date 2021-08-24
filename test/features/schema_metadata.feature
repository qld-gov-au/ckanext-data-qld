@schema_metadata
Feature: SchemaMetadata


    Scenario: When a go to the dataset new page, the field field-author_email should not be visible
        Given "Admin" as the persona
        When I log in
        And I go to "/dataset/new"
        Then I should see an element with id "field-author_email"

    Scenario: When a go to the dataset new page, the field field-maintainer_email should not be visible
        Given "Admin" as the persona
        When I log in
        And I go to "/dataset/new"
        Then I should not see an element with id "field-maintainer_email"

    Scenario: When I create resource without a description, I should see the following error  Description: Missing value
        Given "Admin" as the persona
        When I log in
        And I go to "/dataset/new_resource/warandpeace"
        And I press the element with xpath "//button[contains(string(), 'Add')]"
        Then I should see "Description: Missing value"

    Scenario: When I create resource without a name, I should see the following error  Name: Missing value
        Given "Admin" as the persona
        When I log in
        When I visit "/dataset/new_resource/warandpeace"
        And I press the element with xpath "//button[contains(string(), 'Add')]"
        Then I should see "Name: Missing value"

    Scenario: When viewing the HTML source code of a dataset page, the structured data script is visible
        Given "Admin" as the persona
        When I log in
        When I go to "/dataset/warandpeace"
        Then I should see an element with xpath "//link[@type='application/ld+json']"
