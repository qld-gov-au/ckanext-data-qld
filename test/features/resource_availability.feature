@resource_visibility
Feature: Re-identification risk governance acknowledgement or Resource visibility

    Scenario: Sysadmin creates datasets with de_identified_data, resource_visible and governance_acknowledgement values to test resource visibility feature
        Given "SysAdmin" as the persona
        When I log in
        And I create resource_availability test data with title:"Contains de-identified data YES visibility TRUE acknowledgment NO" de_identified_data:"YES" resource_name:"Hide Resource" resource_visible:"TRUE" governance_acknowledgement:"NO"
        And I create resource_availability test data with title:"Contains de-identified data NO visibility TRUE acknowledgment NO" de_identified_data:"NO" resource_name:"Show Resource" resource_visible:"TRUE" governance_acknowledgement:"NO"
        And I create resource_availability test data with title:"Contains de-identified data NO visibility FALSE acknowledgment NO" de_identified_data:"NO" resource_name:"Hide Resource" resource_visible:"FALSE" governance_acknowledgement:"NO"
        And I create resource_availability test data with title:"Contains de-identified data YES visibility TRUE acknowledgment YES" de_identified_data:"NO" resource_name:"Show Resource" resource_visible:"TRUE" governance_acknowledgement:"NO"


    Scenario Outline: Organisation users should see a hidden resource when de-identified data is YES and Resource visibility is TRUE and Acknowledgement is NO
        Given "<User>" as the persona
        When I log in
        And I go to "/dataset/contains-de-identified-data-yes-visibility-true-acknowledgment-no"
        And I press the element with xpath "//a[@title='Hide Resource']"
        Then I should see an element with xpath "//th[contains(text(), 'Resource visible')]"
        And I should see an element with xpath "//th[contains(text(), 'Re-identification risk governance completed?')]"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    Scenario: Unauthenticated user should not see a hidden resource when de-identified data is YES and Resource visibility is TRUE and Acknowledgement is NO
        Given "Unauthenticated" as the persona
        When I go to "/dataset/contains-de-identified-data-yes-visibility-true-acknowledged-no"
        Then I should not see an element with xpath "//a[@title='Hide Resource']"

    Scenario Outline: Organisation users should see a visible resource when de-identified data is NO and Resource visibility is TRUE and Acknowledgement is NO
        Given "<User>" as the persona
        And I log in
        And I go to "/dataset/contains-de-identified-data-no-visibility-true-acknowledgment-no"
        And I press the element with xpath "//a[@title='Show Resource']"
        Then I should see an element with xpath "//th[contains(text(), 'Resource visible')]"
        And I should see an element with xpath "//th[contains(text(), 'Re-identification risk governance completed?')]"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    Scenario: Unauthenticated user should see a visible resource when de-identified data is NO and Resource visibility is TRUE and Acknowledgement is NO
        Given "Unauthenticated" as the persona
        When I go to "/dataset/contains-de-identified-data-no-visibility-true-acknowledgment-no"
        And I press the element with xpath "//a[@title='Show Resource']"
        Then I should not see an element with xpath "//th[contains(text(), 'Resource visible')]"
        And I should not see an element with xpath "//th[contains(text(), 'Re-identification risk governance completed?')]"

    Scenario Outline: Organisation users should see a hidden resource when de-identified data is NO and Resource visibility is FALSE and Acknowledgement is NO
        Given "<User>" as the persona
        When I log in
        And I go to "/dataset/contains-de-identified-data-no-visibility-false-acknowledgment-no"
        And I press the element with xpath "//a[@title='Hide Resource']"
        Then I should see an element with xpath "//th[contains(text(), 'Resource visible')]"
        And I should see an element with xpath "//th[contains(text(), 'Re-identification risk governance completed?')]"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    Scenario: Unauthenticated user should not see a hidden visible resource when de-identified data is NO and Resource visibility is FALSE and Acknowledgement is NO
        Given "Unauthenticated" as the persona
        When I go to "/dataset/contains-de-identified-data-no-visibility-false-acknowledgment-no"
        Then I should not see an element with xpath "//a[@title='Hide Resource']"

    Scenario Outline: Organisation users should see a visible resource when de-identified data is YES and Resource visibility is TRUE and Acknowledgement is YES
        Given "<User>" as the persona
        When I log in
        And I go to "/dataset/contains-de-identified-data-yes-visibility-true-acknowledgment-yes"
        And I press the element with xpath "//a[@title='Show Resource']"
        Then I should see an element with xpath "//th[contains(text(), 'Resource visible')]"
        And I should see an element with xpath "//th[contains(text(), 'Re-identification risk governance completed?')]"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    Scenario: Unauthenticated user should see a visible resource when de-identified data is YES and Resource visibility is TRUE and Acknowledgement is YES
        Given "Unauthenticated" as the persona
        When I go to "/dataset/contains-de-identified-data-yes-visibility-true-acknowledgment-yes"
        And I press the element with xpath "//a[@title='Show Resource']"
        Then I should not see an element with xpath "//th[contains(text(), 'Resource visible')]"
        And I should not see an element with xpath "//th[contains(text(), 'Re-identification risk governance completed?')]"

    Scenario Outline: Create resource and verify default values are set correct for resource visibility
        Given "<User>" as the persona
        When I create a resource with name "Resource created by <User> with default values" and URL "https://example.com"
        And I press the element with xpath "//a[@title='Resource created by <User> with default values']"
        Then I should not see "Visibility/Governance Acknowledgment"
        And I should see an element with xpath "//th[contains(text(), 'Resource visible')]/following-sibling::td[contains(text(), 'TRUE')]"
        And I should see an element with xpath "//th[contains(text(), 'Re-identification risk governance completed?')]/following-sibling::td[contains(text(), 'NO')]"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    @fixture.dataset_with_schema::name=random_package::owner_org=test-organisation
    @fixture.create_resource_for_dataset_with_params::package_id=random_package::name=invisible-resource::resource_visible=FALSE
    Scenario Outline: resource with resource_visible=False must be visible for org editor, org admin, sysadmin
        Given "<User>" as the persona
        When I log in
        Then I go to dataset "random_package"
        And I should see "invisible-resource"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |

    @fixture.dataset_with_schema::name=random_package::owner_org=test-organisation
    @fixture.create_resource_for_dataset_with_params::package_id=random_package::name=invisible-resource::resource_visible=FALSE
    Scenario Outline: resource with resource_visible=False mustnt be visible for regular user, org editor/admin from different org
        Given "<User>" as the persona
        When I log in
        Then I go to dataset "random_package"
        And I should not see "invisible-resource"

        Examples: Users
            | User                  |
            | CKANUser              |
            | DataRequestOrgEditor  |
            | DataRequestOrgMember  |


    @fixture.dataset_with_schema::name=random_package::owner_org=test-organisation
    @fixture.create_resource_for_dataset_with_params::package_id=random_package::name=visible-resource::request_privacy_assessment=YES::governance_acknowledgement=YES::resource_visible=TRUE
    Scenario Outline: Resource visible, governance_acknowledgement & request_privacy_assessment & not de_identified_data
        Given "<User>" as the persona
        When I log in
        Then I go to dataset "random_package"
        And I should see "visible-resource"

        Examples: Users
            | User                  |
            | CKANUser              |
            | DataRequestOrgEditor  |
            | DataRequestOrgMember  |


    @fixture.dataset_with_schema::name=random_package::owner_org=test-organisation::de_identified_data=YES
    @fixture.create_resource_for_dataset_with_params::package_id=random_package::name=visible-resource::request_privacy_assessment=NO::governance_acknowledgement=YES::resource_visible=TRUE
    Scenario Outline: Resource visible, governance_acknowledgement & not request_privacy_assessment & de_identified_data
        Given "<User>" as the persona
        When I log in
        Then I go to dataset "random_package"
        And I should see "visible-resource"

        Examples: Users
            | User                  |
            | CKANUser              |
            | DataRequestOrgEditor  |
            | DataRequestOrgMember  |

    @fixture.dataset_with_schema::name=random_package::owner_org=test-organisation::de_identified_data=YES
    @fixture.create_resource_for_dataset_with_params::package_id=random_package::name=invisible-resource::request_privacy_assessment=YES::governance_acknowledgement=NO::resource_visible=TRUE
    Scenario Outline: Resource visible, not governance_acknowledgement & not request_privacy_assessment & de_identified_data
        Given "<User>" as the persona
        When I log in
        Then I go to dataset "random_package"
        And I should not see "invisible-resource"

        Examples: Users
            | User                  |
            | CKANUser              |
            | DataRequestOrgEditor  |
            | DataRequestOrgMember  |

    @fixture.dataset_with_schema::name=random_package::owner_org=test-organisation::de_identified_data=YES
    @fixture.create_resource_for_dataset_with_params::package_id=random_package::name=invisible-resource::request_privacy_assessment=YES::governance_acknowledgement=YES::resource_visible=TRUE
    Scenario Outline: Resource visible, governance_acknowledgement & request_privacy_assessment & de_identified_data
        Given "<User>" as the persona
        When I log in
        Then I go to dataset "random_package"
        And I should not see "invisible-resource"

        Examples: Users
            | User                  |
            | CKANUser              |
            | DataRequestOrgEditor  |
            | DataRequestOrgMember  |

    @fixture.dataset_with_schema::name=random_package::owner_org=test-organisation
    @fixture.create_resource_for_dataset_with_params::package_id=random_package::name=invisible-resource::resource_visible=FALSE
    Scenario Outline: update the invisible resource
        Given "<User>" as the persona
        When I log in
        Then I go to dataset "random_package"
        And I click the link with text that contains "invisible-resource"
        And I click the link with text that contains "Manage"
        And I should not see an element with xpath "//label[@for="field-request_privacy_assessment"]//*[@class="control-required"]"
        And I should see an element with xpath "//select[@id="field-request_privacy_assessment"]//option[@value="" or @value="YES" or @value="NO"]"
        And I press the element with xpath "//button[text()='Update Resource']"
        And I should see an element with xpath "//th[text()='Request privacy assessment']/following-sibling::td[not(text())]"

        Examples: Users
            | User          |
            | SysAdmin      |
            | TestOrgAdmin  |
            | TestOrgEditor |
