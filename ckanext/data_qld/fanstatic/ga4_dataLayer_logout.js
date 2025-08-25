/* notify GA4 that client has logged out */
dataLayer.push({
'user_id': null,
'userId': null,  // Used in some parts - user_id is primary
'app_user_id': null // Used in some parts - user_id is primary
});
dataLayer.push({
  'event': 'logged_out'
});
