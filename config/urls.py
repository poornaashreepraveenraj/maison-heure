from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic import RedirectView

admin.site.site_header = "Maison Heure Admin"
admin.site.site_title = "Maison Heure Admin"
admin.site.index_title = "Store management"

urlpatterns = [
    path("admin/", admin.site.urls),
    # Browsers ask for /favicon.ico regardless of the <link rel="icon"> tag.
    path("favicon.ico", RedirectView.as_view(url=static_url("img/favicon.svg"), permanent=True)),
    path("", include("store.urls")),
    path("", include("cart.urls")),
    path("", include("orders.urls")),
    path("", include("support.urls")),
    path("", include("accounts.urls")),
    path("", include("sell.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler400 = "support.views.bad_request"
handler403 = "support.views.permission_denied"
handler404 = "support.views.page_not_found"
handler500 = "support.views.server_error"
