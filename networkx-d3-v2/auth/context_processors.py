from google.appengine.api import users


def google_user(request):
    """
    Inserts value "google_user" inside the template context with the
    currently logged user.
    """
    user = None
    if request.session.get('credentials', None):
        user = users.get_current_user()

    return {"google_user": user}
