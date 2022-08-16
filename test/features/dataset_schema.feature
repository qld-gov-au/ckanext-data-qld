@schema_metadata
Feature: Dataset Schema

    Scenario Outline: Add new dataset metadata fields for default data schema validation
        Given "<User>" as the persona
        When I log in
        And I visit "/dataset/new"

        And I should see an element with xpath "//label[text()="Data Schema"]"
        And I should see an element with xpath "//label[@for="field-de_identified_data"]/following::div[@id="resource-schema-buttons"]"

        Then I should see "Upload"
        And I should see "Link"
        And I should see "JSON"

        And field "default_data_schema" should not be required
        And field "schema_upload" should not be required
        And field "schema_url" should not be required
        And field "schema_json" should not be required

        Then I should see an element with xpath "//div[@id="resource-schema-buttons"]/following::label[@for="field-validation_options"]"
        And field "validation_options" should not be required

        Examples: roles
        | User              |
        | SysAdmin             |
        | DataRequestOrgAdmin  |
        | DataRequestOrgEditor |
