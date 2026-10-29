from django.urls import path

from kmartists.controllers.articles import ArticleCollectionController, ArticleController, GenreCollectionController
from kmartists.controllers.events import EventCollectionController, EventController

urlpatterns = [
    path("kmartists/artists/", ArticleCollectionController.as_view(), name="article-collection"),
    path("kmartists/artists/<uuid:article_id>/", ArticleController.as_view(), name="article-detail"),
    path("kmartists/genres/", GenreCollectionController.as_view(), name="genre-collection"),
    path("kmartists/events/", EventCollectionController.as_view(), name="event-collection"),
    path("kmartists/events/<uuid:event_id>/", EventController.as_view(), name="event-detail"),
]

handler404 = "kmartists.utils.error_handling.not_found"
handler500 = "kmartists.utils.error_handling.server_error"
