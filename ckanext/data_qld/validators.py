import ckan.plugins.toolkit as toolkit


def validate_datarequest_opening(context, request_data):
    accepted_dataset_id = request_data.get('accepted_dataset_id', '')
    print('accepted_dataset_id: s%', accepted_dataset_id)
    if accepted_dataset_id:      
        raise toolkit.ValidationError({toolkit._('Accepted Dataset'): [toolkit._('Dataset has been assigned to this datarequest.')]})
        
