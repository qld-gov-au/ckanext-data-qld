@dataset_deletion
Feature: Dataset deletion

    Scenario: Sysadmin creates and deletes a dataset
        Given "SysAdmin" as the persona
        When I log in
        And I create a dataset with name "dataset-deletion" and title "Dataset deletion"
        And I edit the "dataset-deletion" dataset
        Then I press the element with xpath "//a[@data-module='confirm-action']"
        Then I should see "Briefly describe the reason for deleting this dataset"
        And I should see an element with xpath "//div[@class='modal-footer']//button[@class='btn btn-primary' and @disabled='disabled']"
        When I fill in "deletion_reason" with "it should be longer than 10 characters"
        Then I should not see an element with xpath "//div[@class='modal-footer']//button[@class='btn btn-primary' and @disabled='disabled']"
        Then I press the element with xpath "//div[@class='modal-footer']//button[@class='btn btn-primary']"
        And I reload page every 2 seconds until I see an element with xpath "//div[contains(@class, "alert") and contains(text(), "Dataset has been deleted")]" but not more than 5 times
        And I should not see "Dataset deletion"
        When I go to "/ckan-admin/trash"
        Then I should see "Dataset deletion"
        Then I press the element with xpath "//form[contains(@id, 'form-purge-package')]//*[contains(text(), 'Purge')]"
