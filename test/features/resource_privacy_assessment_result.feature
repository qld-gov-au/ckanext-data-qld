Feature: Resource Privacy Assessment Result

    @fixture.dataset_with_schema:name=package-with-csv-res:de_identified_data=NO:owner_org=test-organisation
    Scenario: Add new resource metadata field 'Privacy assessment result' and display on the edit resource GUI page / editor
        Given "TestOrgEditor" as the persona
        When I log in
        And I go to dataset "package-with-csv-res"

        Then I press the element with xpath "//li[@class="resource-item"]/a"
        Then I press the element with xpath "//a[text()[contains(.,'Manage')]]"
        And I should see an element with xpath "//select[@name='request_privacy_assessment']/following::label[text()='Privacy assessment result']"
        And I should see an element with xpath "//input[@name='privacy_assessment_result' and @readonly]"
        And I should see an element with xpath "//label[text()='Privacy assessment result']/following::span[text()[contains(.,'Privacy assessment information, including the meaning of the Privacy assessment result, can be found')]]"
        And I should see "Privacy assessment information, including the meaning of the Privacy assessment result, can be found here."
        And I should see an element with xpath "//label[text()='Privacy assessment result']/following::a[text()='here']"

    @fixture.dataset_with_schema:name=package-with-csv-res:de_identified_data=NO:owner_org=test-organisation
    Scenario: Add new resource metadata field 'Privacy assessment result' and display on the edit resource GUI page / admin
        Given "TestOrgAdmin" as the persona
        When I log in
        And I go to dataset "package-with-csv-res"

        Then I press the element with xpath "//li[@class="resource-item"]/a"
        Then I press the element with xpath "//a[text()[contains(.,'Manage')]]"
        And I should see an element with xpath "//select[@name='request_privacy_assessment']/following::label[text()='Privacy assessment result']"
        And I should see an element with xpath "//input[@name='privacy_assessment_result' and @readonly]"
        And I should see an element with xpath "//label[text()='Privacy assessment result']/following::span[text()[contains(.,'Privacy assessment information, including the meaning of the Privacy assessment result, can be found')]]"
        And I should see "Privacy assessment information, including the meaning of the Privacy assessment result, can be found here."
        And I should see an element with xpath "//label[text()='Privacy assessment result']/following::a[text()='here']"

    @fixture.dataset_with_schema:name=package-with-csv-res:de_identified_data=NO:owner_org=test-organisation
    Scenario: API viewing of new resource metadata field `Privacy assessment result` / editor
        Given "TestOrgEditor" as the persona
        When I log in
        Then I visit "api/action/package_show?id=package-with-csv-res"
        And I should see an element with xpath "//body/*[contains(text(), '"privacy_assessment_result":')]"

    @fixture.dataset_with_schema:name=package-with-csv-res:de_identified_data=NO:owner_org=test-organisation
    Scenario: API viewing of new resource metadata field `Privacy assessment result` / admin
        Given "TestOrgAdmin" as the persona
        When I log in
        Then I visit "api/action/package_show?id=package-with-csv-res"
        And I should see an element with xpath "//body/*[contains(text(), '"privacy_assessment_result":')]"

    @fixture.dataset_with_schema:name=package-with-csv-res:de_identified_data=NO:owner_org=test-organisation
    Scenario: Sysadmin can edit `Privacy assessment result` in GUI
        Given "SysAdmin" as the persona
        When I log in
        Then I visit "api/action/package_show?id=package-with-csv-res"
        And I should see an element with xpath "//body/*[contains(text(), '"privacy_assessment_result":')]"

        Then I go to dataset "package-with-csv-res"
        Then I press the element with xpath "//li[@class="resource-item"]/a"
        Then I press the element with xpath "//a[text()[contains(.,'Manage')]]"
        And I should see an element with xpath "//input[@name='privacy_assessment_result']"

        Then I fill in "privacy_assessment_result" with "New privacy_assessment_result"
        And I press the element with xpath "//button[@name="save"]"
        Then I should see "New privacy_assessment_result"
