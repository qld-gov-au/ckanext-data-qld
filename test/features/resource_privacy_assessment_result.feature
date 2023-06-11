Feature: Resource Privacy Assessment Result

    Scenario: As a publisher, when I edit a resource, I should see the read-only 'Privacy assessment result' field
        Given "TestOrgEditor" as the persona
        When I log in
        And I go to dataset "public-test-dataset"
        And I go to the first resource in the dataset
        And I press the element with xpath "//a[text()[contains(.,'Manage')]]"
        Then I should see an element with xpath "//select[@name='request_privacy_assessment']/following::label[text()='Privacy assessment result']"
        And I should see an element with xpath "//input[@name='privacy_assessment_result' and @readonly]"
        And I should see an element with xpath "//label[text()='Privacy assessment result']/following::span[contains(translate(text(), 'PA', 'pa'),'privacy assessment')]"

        When I visit "api/action/package_show?id=public-test-dataset"
        Then I should see an element with xpath "//body/*[contains(text(), '"privacy_assessment_result":')]"

    Scenario: As a Sysadmin, when I edit a resource, I can edit the 'Privacy assessment result' field
        Given "SysAdmin" as the persona
        When I log in
        And I create a dataset with key-value parameters "name=privacy-assessment-package"
        And I visit "api/action/package_show?id=privacy-assessment-package"
        Then I should see an element with xpath "//body/*[contains(text(), '"privacy_assessment_result":')]"

        When I go to dataset "privacy-assessment-package"
        And I go to the first resource in the dataset
        And I press the element with xpath "//a[text()[contains(.,'Manage')]]"
        Then I should see an element with xpath "//input[@name='privacy_assessment_result']"

        When I fill in "privacy_assessment_result" with "New privacy_assessment_result"
        And I press the element with xpath "//button[@name="save"]"
        Then I should see "New privacy_assessment_result"

    Scenario: Email to dataset contact when result of requested privacy assessment is posted
        Given "SysAdmin" as the persona
        When I log in
        And I create a dataset and resource with key-value parameters "name=package-with-new-privacy-assessment::author_email=test@gmail.com" and "name=pending-assessment-resource::request_privacy_assessment=YES"
        And I edit the "package-with-new-privacy-assessment" dataset
        And I fill in "privacy_assessment_result" with "New privacy_assessment_result"
        And I press the element with xpath "//button[@name="save"]"
        And I trigger notification about updated privacy assessment results
        Then I should receive an email at "test@gmail.com" containing "A privacy risk assessment was requested for a resource. The result of that assessment has been published to data.qld.gov.au."
        And I should receive an email at "test@gmail.com" containing "Resource/s"
        And I should receive an email at "test@gmail.com" containing "Refer to ‘https://www.data.qld.gov.au/article/standards-and-guidance/publishing-guides-standards/open-data-portal-publishing-guide’ for assistance or contact opendata@qld.gov.au."
        And I should receive an email at "test@gmail.com" containing "Do not reply to this email."
        When I click the resource link in the email I received at "test@gmail.com"
        Then I should see "New privacy_assessment_result"
