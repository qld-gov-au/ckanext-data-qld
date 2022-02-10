@config
Feature: Config

    Scenario: Assert that configuration values are available
        Given "SysAdmin" as the persona
        When I log in
        And I visit "ckan-admin/config"
        And I should see "Suggested Description"
        Then I should see an element with id "field-ckanext.data_qld.datarequest_suggested_description"
        And I should not see an element with id "field-ckan-main-css"
        And I should not see an element with id "field-ckan-site-custom-css"
