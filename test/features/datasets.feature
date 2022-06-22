Feature: Dataset APIs

    Scenario: Creative Commons BY-NC-SA 4.0 licence is an option for datasets
        Given "SysAdmin" as the persona
        When I log in
        And I edit the "test-dataset" dataset
        Then I should see an element with xpath "//option[@value='cc-by-nc-sa-4']"
        And I press the element with xpath "//form[contains(@class, 'dataset-form')]//button[contains(@class, 'btn-primary')]"

        When I press the element with xpath "//a[contains(@href, '/dataset/activity/') and contains(string(), 'Activity Stream')]"
        Then I should see "created the dataset"
        When I click the link with text that contains "View this version"
        Then I should see "You're currently viewing an old version of this dataset."
        When I go to dataset "test-dataset"
        And I press the element with xpath "//a[contains(@href, '/dataset/activity/') and contains(string(), 'Activity Stream')]"
        And I click the link with text that contains "Changes"
        Then I should see "View changes from"
        And I should see an element with xpath "//select[@name='old_id']"
        And I should see an element with xpath "//select[@name='new_id']"
