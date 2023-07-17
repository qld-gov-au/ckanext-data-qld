#!/usr/bin/env sh
##
# Create some example content for extension BDD tests.
#
set -e
set -x

CKAN_ACTION_URL=${CKAN_SITE_URL}api/action
CKAN_USER_NAME="${CKAN_USER_NAME:-admin}"
CKAN_DISPLAY_NAME="${CKAN_DISPLAY_NAME:-Administrator}"
CKAN_USER_EMAIL="${CKAN_USER_EMAIL:-admin@localhost}"

. ${APP_DIR}/bin/activate

add_user_if_needed () {
    echo "Adding user '$2' ($1) with email address [$3]"
    ckan_cli user show "$1" | grep "$1" || ckan_cli user add "$1"\
        fullname="$2"\
        email="$3"\
        password="${4:-Password123!}"
}

add_user_if_needed "$CKAN_USER_NAME" "$CKAN_DISPLAY_NAME" "$CKAN_USER_EMAIL"
ckan_cli sysadmin add "${CKAN_USER_NAME}"

API_KEY=$(ckan_cli user show "${CKAN_USER_NAME}" | tr -d '\n' | sed -r 's/^(.*)apikey=(\S*)(.*)/\2/')
if [ "$API_KEY" = "None" ]; then
    echo "No API Key found on ${CKAN_USER_NAME}, generating API Token..."
    API_KEY=$(ckan_cli user token add "${CKAN_USER_NAME}" test_setup |tail -1 | tr -d '[:space:]')
fi

##
# BEGIN: Add sysadmin config values.
# This needs to be done before closing datarequests as they require the below config values
#
echo "Adding sysadmin config:"

curl -LsH "Authorization: ${API_KEY}" \
    --header "Content-Type: application/json" \
    --data '{
        "ckan.comments.profanity_list": "",
        "ckan.datarequests.closing_circumstances": "Released as open data|nominate_dataset\r\nOpen dataset already exists|nominate_dataset\r\nPartially released|nominate_dataset\r\nTo be released as open data at a later date|nominate_approximate_date\r\nData openly available elsewhere\r\nNot suitable for release as open data\r\nRequested data not available/cannot be compiled\r\nRequestor initiated closure",
        "ckanext.data_qld.resource_formats": "CSV\r\nHTML\r\nJSON\r\nRDF\r\nTXT\r\nXLS",
        "ckanext.data_qld.excluded_display_name_words": "gov"
    }' \
    ${CKAN_ACTION_URL}/config_option_update

##
# END.
#

##
# BEGIN: Create a test organisation with test users for admin, editor and member
#
TEST_ORG_NAME=test-organisation
TEST_ORG_TITLE="Test Organisation"

echo "Creating test users for ${TEST_ORG_TITLE} Organisation:"

add_user_if_needed ckan_user "CKAN User" ckan_user@localhost
add_user_if_needed test_org_admin "Test Admin" test_org_admin@localhost
add_user_if_needed test_org_editor "Test Editor" test_org_editor@localhost
add_user_if_needed test_org_member "Test Member" test_org_member@localhost

echo "Creating ${TEST_ORG_TITLE} organisation:"

TEST_ORG=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "'"${TEST_ORG_NAME}"'", "title": "'"${TEST_ORG_TITLE}"'",
        "description": "Organisation for testing issues"}' \
    ${CKAN_ACTION_URL}/organization_create
)

TEST_ORG_ID=$(echo $TEST_ORG | $PYTHON ${APP_DIR}/bin/extract-id.py)

echo "Assigning test users to '${TEST_ORG_TITLE}' organisation (${TEST_ORG_ID}):"

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "'"${TEST_ORG_ID}"'", "object": "test_org_admin", "object_type": "user", "capacity": "admin"}' \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "'"${TEST_ORG_ID}"'", "object": "test_org_editor", "object_type": "user", "capacity": "editor"}' \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "'"${TEST_ORG_ID}"'", "object": "test_org_member", "object_type": "user", "capacity": "member"}' \
    ${CKAN_ACTION_URL}/member_create
##
# END.
#

# Creating test data hierarchy which creates organisations assigned to datasets
echo "Creating food-standards-agency organisation:"
organisation_create=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data "name=food-standards-agency&title=Food%20Standards%20Agency" \
    ${CKAN_ACTION_URL}/organization_create
)
echo ${organisation_create}

add_user_if_needed foodie "Foodie" foodie@localhost
add_user_if_needed group_admin "Group Admin" group_admin@localhost
add_user_if_needed walker "Walker" walker@localhost

# Create private test dataset with our standard fields
curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "test-dataset", "owner_org": "'"${TEST_ORG_ID}"'", "private": true,
"update_frequency": "monthly", "author_email": "admin@localhost", "version": "1.0",
"license_id": "other-open", "data_driven_application": "NO", "security_classification": "PUBLIC",
"notes": "private test", "de_identified_data": "NO"}' \
    ${CKAN_ACTION_URL}/package_create

# Create public test dataset with our standard fields
curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "public-test-dataset", "owner_org": "'"${TEST_ORG_ID}"'",
"update_frequency": "monthly", "author_email": "admin@example.com", "version": "1.0",
"license_id": "other-open", "data_driven_application": "NO", "security_classification": "PUBLIC",
"notes": "public test", "de_identified_data": "NO", "resources": [
    {"name": "test-resource", "description": "Test resource description",
     "url": "https://example.com", "format": "HTML", "size": 1024}
]}' \
    ${CKAN_ACTION_URL}/package_create

# Datasets need to be assigned to an organisation

echo "Assigning test Datasets to Organisation..."

echo "Updating warandpeace to use ${TEST_ORG_TITLE} organisation:"
package_owner_org_update=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "warandpeace", "organization_id": "'"${TEST_ORG_NAME}"'"}' \
    ${CKAN_ACTION_URL}/package_owner_org_update
)
echo ${package_owner_org_update}

echo "Updating foodie to have admin privileges in the food-standards-agency Organisation:"
foodie_update=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "food-standards-agency", "username": "foodie", "role": "admin"}' \
    ${CKAN_ACTION_URL}/organization_member_create
)
echo ${foodie_update}

echo "Creating non-organisation group:"
group_create=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "silly-walks"}' \
    ${CKAN_ACTION_URL}/group_create
)
echo ${group_create}

echo "Creating Dave's Books group:"
group_create=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "dave", "title": "Dave'"'"'s books", "description": "These are books that David likes."}' \
    ${CKAN_ACTION_URL}/group_create
)
echo ${group_create}

echo "Updating group_admin to have admin privileges in the silly-walks group:"
group_admin_update=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "silly-walks", "username": "group_admin", "role": "admin"}' \
    ${CKAN_ACTION_URL}/group_member_create
)
echo ${group_admin_update}

echo "Updating walker to have editor privileges in the silly-walks group:"
walker_update=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "silly-walks", "username": "walker", "role": "editor"}' \
    ${CKAN_ACTION_URL}/group_member_create
)
echo ${walker_update}

##
# BEGIN: Create a Data Request organisation with test users for admin, editor and member and default data requests
#
# Data Requests requires a specific organisation to exist in order to create DRs for Data.Qld
DR_ORG_NAME=open-data-administration-data-requests
DR_ORG_TITLE="Open Data Administration (data requests)"

echo "Creating test users for ${DR_ORG_TITLE} Organisation:"

add_user_if_needed dr_admin "Data Request Admin" dr_admin@localhost
add_user_if_needed dr_editor "Data Request Editor" dr_editor@localhost
add_user_if_needed dr_member "Data Request Member" dr_member@localhost

echo "Creating ${DR_ORG_TITLE} Organisation:"

DR_ORG=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "'"${DR_ORG_NAME}"'", "title": "'"${DR_ORG_TITLE}"'"}' \
    ${CKAN_ACTION_URL}/organization_create
)

DR_ORG_ID=$(echo $DR_ORG | $PYTHON $APP_DIR/bin/extract-id.py)

echo "Assigning test users to ${DR_ORG_TITLE} Organisation:"

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "'"${DR_ORG_ID}"'", "object": "dr_admin", "object_type": "user", "capacity": "admin"}' \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "'"${DR_ORG_ID}"'", "object": "dr_editor", "object_type": "user", "capacity": "editor"}' \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "'"${DR_ORG_ID}"'", "object": "dr_member", "object_type": "user", "capacity": "member"}' \
    ${CKAN_ACTION_URL}/member_create

echo "Creating test dataset for data request organisation:"

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "data_request_dataset", "title": "Dataset for data requests", "owner_org": "'"${DR_ORG_ID}"'",
"update_frequency": "near-realtime", "author_email": "dr_admin@localhost", "version": "1.0", "license_id": "cc-by-4",
"data_driven_application": "NO", "security_classification": "PUBLIC", "notes": "test", "de_identified_data": "NO"}'\
    ${CKAN_ACTION_URL}/package_create

echo "Creating test Data Request:"

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"title": "Test Request", "description": "This is an example", "organization_id": "'"${TEST_ORG_ID}"'"}' \
    ${CKAN_ACTION_URL}/create_datarequest

##
# END.
#

##
# BEGIN: Create a Reporting organisation with test users
#

REPORT_ORG_NAME=reporting-org
REPORT_ORG_TITLE="Reporting Organisation"

echo "Creating test users for ${REPORT_ORG_TITLE} Organisation:"

add_user_if_needed report_admin "Reporting Admin" report_admin@localhost
add_user_if_needed report_editor "Reporting Editor" report_editor@localhost

echo "Creating ${REPORT_ORG_TITLE} Organisation:"

REPORT_ORG=$( \
    curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "'"${REPORT_ORG_NAME}"'", "title": "'"${REPORT_ORG_TITLE}"'"}' \
    ${CKAN_ACTION_URL}/organization_create
)

REPORT_ORG_ID=$(echo $REPORT_ORG | $PYTHON $APP_DIR/bin/extract-id.py)

echo "Assigning test users to ${REPORT_ORG_TITLE} Organisation:"

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "'"${REPORT_ORG_ID}"'", "object": "report_admin", "object_type": "user", "capacity": "admin"}' \
    ${CKAN_ACTION_URL}/member_create

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"id": "'"${REPORT_ORG_ID}"'", "object": "report_editor", "object_type": "user", "capacity": "editor"}' \
    ${CKAN_ACTION_URL}/member_create

echo "Creating test dataset for reporting:"

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"name": "reporting-dataset", "title": "Dataset for reporting", "owner_org": "'"${REPORT_ORG_ID}"'",
"update_frequency": "near-realtime", "author_email": "report_admin@localhost", "version": "1.0", "license_id": "cc-by-4",
"data_driven_application": "NO", "security_classification": "PUBLIC", "notes": "test", "de_identified_data": "NO"}'\
    ${CKAN_ACTION_URL}/package_create

echo "Creating test Data Request for reporting:"

curl -LsH "Authorization: ${API_KEY}" \
    --data '{"title": "Reporting Request", "description": "Data Request for reporting", "organization_id": "'"${REPORT_ORG_ID}"'"}' \
    ${CKAN_ACTION_URL}/create_datarequest

##
# END.
#

. ${APP_DIR}/bin/deactivate
