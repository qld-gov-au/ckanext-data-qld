Feature: Config

    Scenario: Assert that configuration values are available
        Given "Admin" as the persona
        When I log in
        And I visit "ckan-admin/config"
        Then I should see "Data Request Config"
        And I should see "Suggested Description"
        And I should see an element with id "field-ckanext.data_qld.datarequest_suggested_description"
