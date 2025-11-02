from django.urls import path

from . import views

urlpatterns = [
    path("", views.overview_view, name="overview"),
    path("overview/lanes/", views.overview_lane_collection, name="overview_lane_collection"),
    path(
        "overview/lanes/<uuid:lane_id>/",
        views.overview_lane_detail,
        name="overview_lane_detail",
    ),
    path("boards/", views.board_view, name="board"),
    path("boards/create/", views.board_create, name="board_create"),
    path("boards/<int:pk>/rename/", views.board_rename, name="board_rename"),
    path("boards/<int:pk>/delete/", views.board_delete, name="board_delete"),
    path("boards/<int:board_id>/", views.board_view, name="board_detail"),
    path("card/add/", views.card_add, name="card_add"),
    path("card/<int:pk>/edit/", views.card_edit, name="card_edit"),
    path("card/<int:pk>/move/", views.card_move, name="card_move"),
    path("card/<int:pk>/delete/", views.card_delete, name="card_delete"),
]
