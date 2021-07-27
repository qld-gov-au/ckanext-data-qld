
#!/usr/bin/env sh
##
# Create some example content for extension BDD tests.
#
set -e

CKAN_ACTION_URL=http://ckan:3000/api/action

. ${APP_DIR}/bin/activate

# We know the "admin" sysadmin account exists, so we'll use her API KEY to create further data
API_KEY=$(ckan_cli user admin | tr -d '\n' | sed -r 's/^(.*)apikey=(\S*)(.*)/\2/')

##
# BEGIN: Create a test organisation with test users for admin, editor and member
#
TEST_ORG_NAME=test
TEST_ORG_TITLE="Test"

echo "Creating test users for ${TEST_ORG_TITLE} Organisation:"

ckan_cli user add ckan_user email=ckan_user@localhost password=password
ckan_cli user add test_org_admin email=test_org_admin@localhost password=password
ckan_cli user add test_org_editor email=test_org_editor@localhost password=password
ckan_cli user add test_org_member email=test_org_member@localhost password=password

echo "Creating ${TEST_ORG_TITLE} Organisation:"

TEST_ORG=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data "name=${TEST_ORG_NAME}&title=${TEST_ORG_TITLE}" \
    ${CKAN_ACTION_URL}/organization_create
)
echo $TEST_ORG

TEST_ORG_ID=$(echo $TEST_ORG | sed -r 's/^(.*)"id": "(.*)",(.*)/\2/')

echo "Assigning test users to ${TEST_ORG_TITLE} Organisation:"

curl -LsH "Authorization: ${API_KEY}" \
    --data "id=${TEST_ORG_ID}&object=test_org_admin&object_type=user&capacity=admin" \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data "id=${TEST_ORG_ID}&object=test_org_editor&object_type=user&capacity=editor" \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data "id=${TEST_ORG_ID}&object=test_org_member&object_type=user&capacity=member" \
    ${CKAN_ACTION_URL}/member_create
##
# END.
#

# Creating basic test data which has datasets with resources
ckan_cli create-test-data

# Datasets need to be assigned to an organisation

echo "Assigning test Datasets to Organisation..."

echo "Updating annakarenina to use ${TEST_ORG_TITLE} organisation:"
package_owner_org_update=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data "id=annakarenina&organization_id=${TEST_ORG_NAME}" \
    ${CKAN_ACTION_URL}/package_owner_org_update
)
echo ${package_owner_org_update}

echo "Updating warandpeace to use ${TEST_ORG_TITLE} organisation:"
package_owner_org_update=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data "id=warandpeace&organization_id=${TEST_ORG_NAME}" \
    ${CKAN_ACTION_URL}/package_owner_org_update
)
echo ${package_owner_org_update}


# Data Requests requires a specific organisation to exist in order to create DRs for Data.Qld
DR_ORG_NAME=open-data-administration-data-requests
DR_ORG_TITLE="Open Data Administration (data requests)"

echo "Creating test users for ${DR_ORG_TITLE} Organisation:"

ckan_cli user add dr_admin email=dr_admin@localhost password=password
ckan_cli user add dr_editor email=dr_editor@localhost password=password
ckan_cli user add dr_member email=dr_member@localhost password=password

echo "Creating Data Request Organisation:"

DR_ORG=$( \
    curl -L -s \
    --header "Authorization: ${API_KEY}" \
    --data "name=${DR_ORG_NAME}&title=${DR_ORG_TITLE}" \
    ${CKAN_ACTION_URL}/organization_create
)

DR_ORG_ID=$(echo $DR_ORG | sed -r 's/^(.*)"id": "(.*)",(.*)/\2/')

echo "Assigning test users to Data Request Organisation:"

curl -LsH "Authorization: ${API_KEY}" \
    --data "id=${DR_ORG_ID}&object=dr_admin&object_type=user&capacity=admin" \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data "id=${DR_ORG_ID}&object=dr_editor&object_type=user&capacity=editor" \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data "id=${DR_ORG_ID}&object=dr_member&object_type=user&capacity=member" \
    ${CKAN_ACTION_URL}/member_create


echo "Creating test Data Request:"

curl -LsH "Authorization: ${API_KEY}" \
    --data "title=Test Request&description=This is an example&organization_id=${TEST_ORG_ID}" \
    ${CKAN_ACTION_URL}/create_datarequest

echo "Creating config value for resource formats:"

curl -LsH "Authorization: ${API_KEY}" \
    --data "ckanext.data_qld.resource_formats=JSON" \
    ${CKAN_ACTION_URL}/config_option_update

deactivate
