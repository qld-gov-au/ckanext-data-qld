@dataset_deletion
Feature: Dataset deletion

    Scenario: Sysadmin creates and deletes a dataset
        Given "SysAdmin" as the persona
        When I log in
        And I create a dataset and resource with key-value parameters "title=Dataset deletion" and "url=default"
        And I edit the "$last_generated_name" dataset
        When I press the element with xpath "//a[@data-module='confirm-action']"
        Then I should see "Briefly describe the reason for deleting this dataset"
        And I should see an element with xpath "//div[@class='modal-footer']//button[@class='btn btn-primary' and @disabled='disabled']"
        When I fill in "deletion-reason" with "it should be longer than 10 characters" if present
        Then I should not see an element with xpath "//div[@class='modal-footer']//button[@class='btn btn-primary' and @disabled='disabled']"
        When I press the element with xpath "//button[@class='btn btn-primary' and contains(string(), 'Confirm') ]"
        And I reload page every 2 seconds until I see an element with xpath "//div[contains(@class, "alert") and contains(string(), "Dataset has been deleted")]" but not more than 5 times
        Then I should not see "Dataset deletion"
        When I go to "/ckan-admin/trash"
        Then I should see "Dataset deletion"
        When I press the element with xpath "//form[contains(@id, 'form-purge-package')]//*[contains(string(), 'Purge')]"
        And I confirm the dialog containing "Are you sure you want to purge datasets?" if present
        Then I should see "datasets have been purged"
