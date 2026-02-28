from django.shortcuts import redirect


# URLs under /admin/ that must always pass through so the login flow works
_ADMIN_PASSTHROUGH = (
    '/admin/login/',
    '/admin/logout/',
    '/admin/jsi18n/',
    '/admin/password_',
)


class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Always let the admin's own auth URLs pass through unmodified.
        # Intercepting /admin/login/ would create an infinite redirect loop
        # and prevent login form submissions from ever being processed.
        if any(path.startswith(p) for p in _ADMIN_PASSTHROUGH):
            return self.get_response(request)

        if path.startswith('/admin/') and request.user.is_authenticated:
            if not request.user.is_superuser:
                try:
                    profile = request.user.admin_profile
                    if not profile.is_active:
                        # Redirect to appropriate login
                        return redirect('/super-admin/login/' if profile.is_super_admin else '/admin/login/')
                except AttributeError:
                    # No AdminProfile — deny access
                    return redirect('/')

        # Redirect unauthenticated /admin/ access to appropriate login
        if path.startswith('/admin/') and not request.user.is_authenticated:
            if 'next' in request.GET:
                next_url = request.GET.get('next')
                if '/super-admin/' in next_url:
                    return redirect(f'/super-admin/login/?next={next_url}')
            return redirect('/admin/login/')

        return self.get_response(request)
