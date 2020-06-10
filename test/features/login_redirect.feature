@login_redirect
Feature: Login Redirection

    @dashboard_login
    Scenario: As an unauthenticated user, when I visit the /dashboard URL I see the login page
        Given "Unathenticated" as the persona
        When I visit "/dashboard"
        Then I should see an element with xpath "//h1[contains(string(), 'Login')]"

    @dashboard_login
    Scenario: As an unauthenticated user, when I visit the /dashboard/ URL I see the login page
        Given "Unathenticated" as the persona
        When I visit "/dashboard/"
        Then I should see an element with xpath "//h1[contains(string(), 'Login')]"

    @user_edit
    Scenario: As an unauthenticated organisation member, when I visit the /user/edit URL I see the login page. Upon logging in I am taken to the /user/edit page
        Given "TestOrgMember" as the persona
        When I visit "/user/edit"
        Then I should see an element with xpath "//h1[contains(string(), 'Login')]"
        When I log in directly
        Then I should see "Change details"

    @dataset_setup
    Scenario: As a Sysadmin I set the visibility of a public record to private for the following scenarios
        Given "Admin" as the persona
        When I log in
        Then I visit "/dataset/edit/annakarenina"
        When I select "True" from "private"
        And I fill in "author_email" with "admin@localhost"
        And I press "Update Dataset"
        Then I should see an element with xpath "//span[contains(string(), 'Private')]"

    @private_dataset
    Scenario: As an unauthenticated user, when I visit the URL of a private dataset I see the login page
        Given "Unathenticated" as the persona
        When I visit "/dataset/annakarenina"
        Then I should see an element with xpath "//h1[contains(string(), 'Login')]"

    @private_dataset
    Scenario: As an unauthenticated organisation member, when I visit the URL of a private dataset I see the login page. Upon logging in I am taken to the private dataset
        Given "TestOrgMember" as the persona
        When I visit "/dataset/annakarenina"
        Then I should see an element with xpath "//h1[contains(string(), 'Login')]"
        When I log in directly
        Then I should see an element with xpath "//h1[contains(string(), 'A Novel By Tolstoy')]"
        And I should see an element with xpath "//span[contains(string(), 'Private')]"

    @private_dataset_resource
    Scenario: As an unauthenticated organisation member, when I visit the URL of a private dataset resource I see the login page. Upon logging in I am taken to the private dataset resource
        Given "TestOrgMember" as the persona
        When I visit "/dataset/annakarenina/resource/e5966553-46d7-404c-a08d-67d7331a099e"
        Then I should see an element with xpath "//h1[contains(string(), 'Login')]"
        When I log in directly
        Then I should see an element with xpath "//h1[contains(string(), 'Full text')]"
