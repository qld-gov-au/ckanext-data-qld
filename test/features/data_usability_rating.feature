@data_usability_rating
Feature: Data usability rating
    @wip
    Scenario: As an admin user of my organisation, when I create a dataset with a license that is not open, I can verify the score is 0
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-closed" and resource file "txt_resource.txt"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//div[contains(@class, 'qa openness-0')]"


    Scenario: As an admin user of my organisation, when I create a dataset with a open license and TXT resource, I can verify the score is 1
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and resource file "txt_resource.txt"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//div[contains(@class, 'qa openness-1')]"


    Scenario: As an admin user of my organisation, when I create a dataset with a open license and XLS resource, I can verify the score is 2
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and resource file "xls_resource.xls"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//div[contains(@class, 'qa openness-2')]"


    Scenario: As an admin user of my organisation, when I create a dataset with a open license and a CSV resource, I can verify the score is 3
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and resource file "csv_resource.csv"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//div[contains(@class, 'qa openness-3')]"


    Scenario: As an admin user of my organisation, when I create a dataset with a open license and a RDF resource, I can verify the score is 4
        Given "TestOrgAdmin" as the persona
        When I log in
        And I create a dataset with license "other-open" and resource file "rdf_resource.rdf"
        Then I wait for 10 seconds
        When I reload
        Then I should see "Data usability rating"
        And I should see an element with xpath "//div[contains(@class, 'qa openness-4')]"



