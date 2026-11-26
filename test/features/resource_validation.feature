@OpenData
@multi_plugin
@resource_validation
Feature: Resource validation

    Scenario: As an editor, I can create and update a resource with an uploaded validation schema
        Given "TestOrgEditor" as the persona
        When I log in
        And I create a dataset and resource with key-value parameters "notes=Test uploaded schema" and "name=Test validation schema::upload=test.csv::format=CSV::description=Testing validation schema::schema_upload=test_schema.json"
        Then I should see "Test validation schema"

        When I click the link with text that contains "Test validation schema"
        And I press the resource edit button
        Then the "field-schema-json" field should contain:
            | "fields": [      |
            | "name": "field1" |
            | "name": "field2" |
        When I upload schema file "test_schema2.json" to resource
        And I take a debugging screenshot
        And I submit the main form
        Then I should see "Test validation schema"
        When I press "Test validation schema"
        And I press the resource edit button
        Then the "field-schema-json" field should contain:
            | "fields"                 |
            | "name": "field1"         |
            | "name": "field2"         |
            | "title": "First column"  |
            | "title": "Second column" |

    Scenario: As an editor, I can create and update a resource with validation options
        Given "TestOrgEditor" as the persona
        When I log in
        And I create a dataset with key-value parameters "notes=Test validation options"
        And I open the new resource form for dataset "$last_generated_name"
        And I upload "test.csv" of type "CSV" to resource
        And I fill in "name" with "Test validation options"
        And I fill in "description" with "Testing validation options"
        And I upload schema file "test_schema.json" to resource
        And I fill in "validation_options" with "{"headers": 1}"
        And I execute the script "document.getElementById('field-format').value='CSV'"
        And I submit the main form
        Then I should see "Test validation options"

        When I click the link with text that contains "Test validation options"
        And I press the resource edit button
        Then the "field-schema-json" field should contain:
            | "headers": 1 |

        When I click the link with text that contains "Test validation options"
        And I press the resource edit button
        And I fill in "validation_options" with "{"delimiter": ","}"

        And I submit the main form
        Then I should see an element with xpath "//h1[contains(string(), 'Test validation options')]"
        When I click the link with text that contains "Test validation options"
        And I press the resource edit button
        Then the "field-schema-json" field should contain:
            | "delimiter": "," |

    Scenario: As an editor, I can create a resource with a valid CSV and see a success status
        Given "TestOrgEditor" as the persona
        When I log in
        And I create a dataset with key-value parameters "notes=Test valid CSV"
        And I open the new resource form for dataset "$last_generated_name"
        And I upload "test.csv" of type "CSV" to resource
        And I fill in "name" with "Test valid CSV create"
        And I upload schema file "test_schema.json" to resource
        And I fill in "description" with "Testing validation that should pass"
        And I execute the script "document.getElementById('field-format').value='CSV'"
        And I submit the main form
        Then I should see "Test valid CSV"
        When I click the link with text that contains "Test valid CSV"
        And I reload page every 3 seconds until I see an element with xpath "//th[string() = 'Validation status']/../td[string() = 'success']" but not more than 10 times
        Then I should see a validation timestamp

    Scenario: As an editor, I can update a resource with a valid CSV and see a success status
        Given "TestOrgEditor" as the persona
        When I log in
        And I create a dataset and resource with key-value parameters "notes=Test valid CSV" and "name=Test valid CSV update::upload=invalid.csv::format=CSV::description=Testing validation that should pass on update"
        Then I should see "Test valid CSV update"
        When I press "Test valid CSV update"
        And I press the resource edit button
        And I upload "test.csv" of type "CSV" to resource
        And I upload schema file "test_schema.json" to resource
        And I submit the main form
        And I click the link with text that contains "Test valid CSV update"
        And I reload page every 3 seconds until I see an element with xpath "//th[string() = 'Validation status']/../td[string() = 'success']" but not more than 10 times
        Then I should see a validation timestamp

    Scenario: As an editor, I can update a resource with an invalid CSV and see a validation error
        Given "TestOrgEditor" as the persona
        When I log in
        And I create a dataset and resource with key-value parameters "notes=Test invalid CSV" and "name=Test invalid CSV update::upload=test.csv::format=CSV::schema_upload=test_schema.json::description=Testing validation that should fail on update"
        Then I should see "Test invalid CSV update"
        When I press "Test invalid CSV update"
        And I press the resource edit button
        And I upload "invalid.csv" of type "CSV" to resource
        And I submit the main form
        And I reload page every 3 seconds until I see an element with xpath "//th[string() = 'Validation status']/../td[string() = 'failure']" but not more than 10 times
        Then I should see an element with xpath "//a[contains(@class, 'validation-badge')]"
        When I press the element with xpath "//a[contains(@class, 'validation-badge')]"
        Then I should see "Validation Report"
        And I should see "Duration: 0."
