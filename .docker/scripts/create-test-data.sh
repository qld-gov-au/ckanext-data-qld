
#!/usr/bin/env sh
##
# Create some example content for extension BDD tests.
#
set -e

CKAN_ACTION_URL=http://ckan:3000/api/action
PASTER="${APP_DIR}/bin/paster --plugin=ckan"

# We know the "admin" sysadmin account exists, so we'll use her API KEY to create further data
API_KEY=$($PASTER user admin -c ${CKAN_INI} | tr -d '\n' | sed -r 's/^(.*)apikey=(\S*)(.*)/\2/')

# Creating test data hierarchy which creates organisations assigend to datasets
$PASTER create-test-data hierarchy -c ${CKAN_INI}

# Creating basic test data which has datasets with resources
$PASTER create-test-data -c ${CKAN_INI}

echo "Updating annakarenina to use department-of-health Organisation:"
package_owner_org_update=$( \
    curl -L -s --header "Authorization: ${API_KEY}" \
    --data "id=annakarenina&organization_id=department-of-health" \
    ${CKAN_ACTION_URL}/package_owner_org_update
)
echo ${package_owner_org_update}
