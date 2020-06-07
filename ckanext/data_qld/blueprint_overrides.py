import ckan.lib.helpers as h
from ckan.common import _, g, request
from ckan.views.user import login, me
from ckan.views.dashboard import index


def dashboard_override(offset=0):
    """
    Override default CKAN behaviour of throwing 403 Unauthorised exception for /dashboard[/] page and instead
    redirect the user to the login page.
    Ref.: ckan/views/dashboard.py > def index(...)
    :param offset:
    :return:
    """
    return index(offset) if g.user else h.redirect_to(h.url_for(u'user.login'))


def logged_in_override():
    """
    Override default CKAN behaviour to only redirect user to `came_from` URL if they are logged in.
    Ref.: ckan/views/user.py > def logged_in()
    :return:
    """
    if g.user:
        came_from = request.params.get(u'came_from', None)
        return h.redirect_to(str(came_from)) if came_from and h.url_is_local(came_from) else me()
    else:
        h.flash_error(_(u'Login failed. Bad username or password.'))
        return login()
