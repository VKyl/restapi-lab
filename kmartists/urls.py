from django.urls import path

from kmartists.controllers.articles import ArticleCollectionController, ArticleController
from kmartists.controllers.events import EventCollectionController, EventController

urlpatterns = [
    path("artists/", ArticleCollectionController.as_view(), name="article-collection"),
    path("artists/<uuid:article_id>/", ArticleController.as_view(), name="article-detail"),
    path("events/", EventCollectionController.as_view(), name="event-collection"),
    path("events/<uuid:event_id>/", EventController.as_view(), name="event-detail"),
]

handler404 = "kmartists.utils.error_handling.not_found"
handler500 = "kmartists.utils.error_handling.server_error"
