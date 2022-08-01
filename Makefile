###############################################################################
#                             requirements: start                             #
###############################################################################
# ckan_tag = ckan-2.9.5
remote-ckan = https://github.com/qld-gov-au/ckan.git tag ckan-2.9.5-qgov.7

ext_list = dcat datarequests csrf-filter xloader datajson ytp-comments validation ssm-config scheming s3filestore resource-type-validation report ex-qgov archiver qa odi-certificates harvester-data-qld-geoscience harvest

remote-archiver = https://github.com/qld-gov-au/ckanext-archiver.git tag  2.1.1-qgov.8
remote-harvester-data-qld-geoscience = https://github.com/qld-gov-au/ckanext-harvester-data-qld-geoscience tag  v0.0.5
remote-odi-certificates = https://github.com/qld-gov-au/ckanext-odi-certificates.git tag  1.0.1
remote-qa = https://github.com/qld-gov-au/ckanext-qa.git tag  2.0.3-qgov.4
remote-ex-qgov = https://github.com/qld-gov-au/ckan-ex-qgov.git tag  5.0.2
remote-report = https://github.com/qld-gov-au/ckanext-report.git tag  0.3
remote-resource-type-validation = https://github.com/qld-gov-au/ckanext-resource-type-validation.git tag  1.0.2
remote-s3filestore = https://github.com/qld-gov-au/ckanext-s3filestore.git tag  0.7.7-qgov.2
remote-scheming = https://github.com/ckan/ckanext-scheming.git tag  release-2.1.0
remote-ssm-config = https://github.com/qld-gov-au/ckanext-ssm-config.git tag  0.0.2

remote-validation = https://github.com/qld-gov-au/ckanext-validation.git tag  v0.0.8-qgov.4
develop-validation = https://github.com/qld-gov-au/ckanext-validation.git branch develop

remote-ytp-comments = https://github.com/qld-gov-au/ckanext-ytp-comments.git tag  2.5.0-qgov.2
remote-datajson = https://github.com/GSA/ckanext-datajson.git branch main
remote-xloader = https://github.com/qld-gov-au/ckanext-xloader.git tag 0.10.0-qgov.1
remote-csrf-filter = https://github.com/qld-gov-au/ckanext-csrf-filter.git tag 1.1.3

remote-datarequests = https://github.com/qld-gov-au/ckanext-datarequests.git tag 2.2.0-qgov
remote-dcat = https://github.com/ckan/ckanext-dcat.git tag v1.1.3
remote-harvest = https://github.com/ckan/ckanext-harvest.git commit 89b1a32

###############################################################################
#                              requirements: end                              #
###############################################################################

_version = master

-include deps.mk

prepare:
	curl -O https://raw.githubusercontent.com/DataShades/ckan-deps-installer/$(_version)/deps.mk
