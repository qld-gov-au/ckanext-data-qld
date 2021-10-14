@comments
Feature: Comments

    Scenario: The Add Comment form should not display for a non-logged-in user - instead they see a 'Login to comment' button
        Given "Unauthenticated" as the persona
        When I go to dataset "warandpeace" comments
        Then I should see an element with xpath "//a[contains(string(), 'Login to comment')]"
        And I should not see "Add a comment"

    Scenario: Logged-in users see the add comment form
        Given "CKANUser" as the persona
        When I log in
        Then I go to dataset "warandpeace" comments
        Then I should see an element with xpath "//h3[contains(string(), 'Add a comment')]"

    @comment-add
    Scenario: When a logged-in user submits a comment on a Dataset the comment should display within 10 seconds
        Given "CKANUser" as the persona
        When I log in
        Then I go to dataset "warandpeace" comments
        Then I should see an element with xpath "//h3[contains(string(), 'Add a comment')]"
        Then I submit a comment with subject "Test subject" and comment "This is a test comment"
        Then I should see "This is a test comment" within 10 seconds

    @comment-add @comment-profane
    Scenario: When a logged-in user submits a comment containing whitelisted profanity on a Dataset the comment should display within 10 seconds
        Given "CKANUser" as the persona
        When I log in
        Then I go to dataset "warandpeace" comments
        Then I should see an element with xpath "//h3[contains(string(), 'Add a comment')]"
        Then I submit a comment with subject "Test subject" and comment "sex"
        Then I should see "sex" within 10 seconds

    @comment-report
    Scenario: When a logged-in user reports a comment on a Dataset the comment should be marked as reported and an email sent to the admins of the organisation
        Given "CKANUser" as the persona
        When I log in
        Then I go to dataset "warandpeace" comments
        And I press the element with xpath "//a[contains(string(), 'Report')]"
        Then I should see "Reported" within 5 seconds
        When I wait for 3 seconds
        Then I should receive an email at "test_org_admin@localhost" with subject "Queensland Government Open Data - Comments"

    @comment-reply
    Scenario: When a logged-in user submits a reply comment on a Dataset, the comment should display within 10 seconds
        Given "CKANUser" as the persona
        When I log in
        Then I go to dataset "warandpeace" comments
        Then I submit a reply with comment "This is a reply"
        Then I should see "This is a reply" within 10 seconds

    @comment-delete
    Scenario: When an Org Admin visits a dataset belonging to their organisation, they can delete a comment and should not see text 'This comment was deleted.'
        Given "TestOrgAdmin" as the persona
        When I log in
        Then I go to dataset "warandpeace" comments
        And I press the element with xpath "//a[@title='Delete comment']"
        Then I should see "Are you sure you want to delete this comment?" within 1 seconds
        Then I press the element with xpath "//button[contains(string(), 'Confirm')]"
        Then I should not see "This comment was deleted." within 2 seconds

    @comment-add
    Scenario: When a logged-in user submits a comment on a Dataset the page should be scrolled to the highlighted comment they just posted.
        Given "CKANUser" as the persona
        When I log in
        Then I go to dataset "warandpeace" comments
        Then I should see an element with xpath "//h3[contains(string(), 'Add a comment')]"
        Then I submit a comment with subject "Test subject" and comment "This is a test comment"
        Then I wait for 3 seconds
        Then I should see an element with xpath "//div[contains(@class, 'comment-wrapper highlight') and contains(string(), 'This is a test comment')]"

    @comment-delete
    Scenario: When an Org Admin visits a dataset belonging to their organisation, they can delete a comment and the comment will be marked with delete by username.
        Given "TestOrgAdmin" as the persona
        When I log in
        Then I go to dataset "warandpeace" comments
        And I press the element with xpath "//a[@title='Delete comment']"
        Then I should see "Are you sure you want to delete this comment?" within 1 seconds
        Then I press the element with xpath "//button[contains(string(), 'Confirm')]"
        Then I should see "Comment deleted by Test Admin." within 2 seconds

    @comment-delete
    Scenario: When an Org Admin visits a data request belonging to their organisation, they can delete a comment and the comment will be marked with delete by username.
        Given "SysAdmin" as the persona
        When I log in
        And I go to data request "Test Request" comments
        And I press the element with xpath "//a[@title='Delete comment']"
        Then I should see "Are you sure you want to delete this comment?" within 1 seconds
        Then I press the element with xpath "//button[contains(string(), 'Confirm')]"
        Then I should see "Comment deleted by Administrator." within 2 seconds

    @comment-tab
    Scenario: Non-logged in users should not see comment form in dataset tab
        Given "Unauthenticated" as the persona
        When I go to dataset "warandpeace"
        Then I should not see an element with id "comment_form"

    @comment-tab
    Scenario: Logged in users should not see comment form in dataset tab
        Given "CKANUser" as the persona
        When I go to dataset "warandpeace"
        Then I should not see an element with id "comment_form"

    @comment-tab
    Scenario: Users should see comment tab on dataset
        Given "Unauthenticated" as the persona
        Then I go to dataset "warandpeace"
        Then I should see an element with xpath "//a[contains(string(), 'Comments')]"

    @comment-tab
    Scenario: Users should see comment badge count of 2 on dataset
        Given "Unauthenticated" as the persona
        Then I go to dataset "warandpeace"
        Then I should see an element with xpath "//span[contains(@class, 'badge') and contains(string(), '2')]"
