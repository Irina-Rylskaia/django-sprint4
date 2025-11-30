from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("pages/", include(("pages.urls", "pages"), namespace="pages")),
    path(
        "auth/registration/",
        TemplateView.as_view(
            template_name="registration/registration_form.html"
        ),
        name="registration",
    ),
    path("", include(("blog.urls", "blog"), namespace="blog")),
    path("auth/", include("django.contrib.auth.urls")),
]

handler404 = "pages.views.page_not_found"
handler500 = "pages.views.server_error"
handler403 = "pages.views.csrf_failure"
