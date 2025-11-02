import json
from datetime import datetime, date
from typing import Dict, Optional

from django.db import transaction
from django.db.models import Max
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from .models import Board, Column, Card, OverviewLane

DEFAULT_COLUMNS = (
    ("Backlog", 0),
    ("In Progress", 1),
    ("Review", 2),
    ("Done", 3),
)

LANE_FILTER_KEYS = (
    "name",
    "board",
    "column",
    "assignee",
    "priority",
    "due_from",
    "due_to",
    "sort",
)


def _trimmed(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _normalise_lane_filters(raw: Optional[Dict[str, str]]) -> Dict[str, str]:
    if not isinstance(raw, dict):
        raw = {}
    normalised = {_key: _trimmed(raw.get(_key, "")) for _key in LANE_FILTER_KEYS}
    if not normalised["sort"]:
        normalised["sort"] = "due_date"
    return normalised


def _next_lane_position() -> int:
    max_pos = OverviewLane.objects.aggregate(max_pos=Max("position"))
    current = max_pos.get("max_pos") or 0
    return current + 1


def _serialize_lane(lane: OverviewLane) -> Dict[str, Dict[str, str]]:
    return {
        "id": str(lane.id),
        "filters": _normalise_lane_filters(lane.filters or {}),
    }


def _extract_lane_filters(request) -> Dict[str, str]:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    raw_filters = payload.get("filters")
    if not isinstance(raw_filters, dict):
        raw_filters = payload
    return _normalise_lane_filters(raw_filters)


def _create_default_columns(board: Board) -> None:
    Column.objects.bulk_create(
        [Column(board=board, name=name, order=order) for name, order in DEFAULT_COLUMNS]
    )


def _unique_board_name(base_name: str, *, exclude_id: Optional[int] = None) -> str:
    candidate = base_name
    suffix = 2
    conflict_qs = Board.objects.exclude(pk=exclude_id) if exclude_id else Board.objects
    while conflict_qs.filter(name=candidate).exists():
        candidate = f"{base_name} {suffix}"
        suffix += 1
    return candidate


def _ensure_default_board() -> Board:
    board = Board.objects.order_by("created_at", "id").first()
    if board:
        return board
    with transaction.atomic():
        board = Board.objects.create(name="Mein Board")
        _create_default_columns(board)
    return board


def board_view(request, board_id=None):
    default_board = _ensure_default_board()
    boards = list(Board.objects.order_by("created_at", "id"))
    active_board = None

    requested_id = board_id
    if requested_id is None:
        requested_id = request.GET.get("board")

    if requested_id is not None:
        try:
            requested_id = int(requested_id)
        except (TypeError, ValueError):
            requested_id = None

    if requested_id is not None:
        active_board = next((board for board in boards if board.id == requested_id), None)

    if active_board is None:
        active_board = default_board

    columns = (
        active_board.columns.prefetch_related("cards").all()
        if active_board
        else Column.objects.none()
    )

    return render(
        request,
        "board/board.html",
        {
            "boards": boards,
            "active_board": active_board,
            "columns": columns,
            "active_page": "board",
        },
    )


def overview_view(request):
    default_board = _ensure_default_board()
    boards = list(Board.objects.order_by("created_at", "id"))

    cards_qs = Card.objects.select_related("column__board").order_by("created_at")
    cards_payload = []
    for card in cards_qs:
        board = card.column.board
        cards_payload.append(
            {
                "id": card.id,
                "title": card.title,
                "description": card.description or "",
                "priority": card.priority or "",
                "priority_label": card.get_priority_display() if card.priority else "",
                "due_date": card.due_date.isoformat() if card.due_date else "",
                "assignee": card.assignee or "",
                "column": {
                    "id": card.column_id,
                    "name": card.column.name,
                },
                "board": {
                    "id": board.id,
                    "name": board.name,
                },
                "created_at": card.created_at.isoformat(),
                "link": reverse("board_detail", args=[board.id]),
            }
        )

    column_names = list(
        dict.fromkeys(
            Column.objects.order_by("order", "id").values_list("name", flat=True)
        )
    )

    available_assignees = (
        Card.objects.exclude(assignee="")
        .values_list("assignee", flat=True)
        .distinct()
        .order_by("assignee")
    )

    lanes = list(OverviewLane.objects.order_by("position", "created_at", "id"))
    lanes_payload = [_serialize_lane(lane) for lane in lanes]

    active_board = default_board if default_board in boards else (boards[0] if boards else None)

    return render(
        request,
        "board/overview.html",
        {
            "boards": boards,
            "active_board": active_board,
            "active_page": "overview",
            "priority_choices": Card.PRIORITY_CHOICES,
            "assignees": list(available_assignees),
            "today": date.today(),
            "cards_data": cards_payload,
            "columns": column_names,
            "lanes_data": lanes_payload,
        },
    )

@require_POST
def card_add(request):
    title = request.POST.get("title", "").strip()
    desc = request.POST.get("description", "").strip()
    column_id = request.POST.get("column_id")
    priority_val = request.POST.get("priority", "").strip() or None
    due_input = request.POST.get("due_date", "").strip()
    assignee = request.POST.get("assignee", "").strip()

    due_date = None
    if due_input:
        try:
            due_date = datetime.strptime(due_input, "%Y-%m-%d").date()
        except ValueError:
            due_date = None

    column = get_object_or_404(Column, id=column_id)
    board_id = column.board_id
    if title:
        order = column.cards.count()
        Card.objects.create(
            title=title,
            description=desc,
            priority=priority_val,
            due_date=due_date,
            assignee=assignee,
            column=column,
            order=order,
        )
    return redirect("board_detail", board_id=board_id)


@require_POST
def card_edit(request, pk):
    card = get_object_or_404(Card, pk=pk)
    title = request.POST.get("title", "").strip()
    desc = request.POST.get("description", "").strip()
    column_id = request.POST.get("column_id") or card.column_id
    priority_val = request.POST.get("priority", "").strip() or None
    due_input = request.POST.get("due_date", "").strip()
    assignee = request.POST.get("assignee", "").strip()

    due_date = None
    if due_input:
        try:
            due_date = datetime.strptime(due_input, "%Y-%m-%d").date()
        except ValueError:
            due_date = None

    if title:
        target_column = get_object_or_404(Column, id=column_id)
        board_id = target_column.board_id
        column_changed = target_column != card.column

        card.title = title
        card.description = desc
        card.priority = priority_val
        card.due_date = due_date
        card.assignee = assignee

        if column_changed:
            card.column = target_column
            card.order = target_column.cards.count()

        card.save()
    return redirect("board_detail", board_id=board_id if title else card.column.board_id)

@require_POST
def card_move(request, pk):
    card = get_object_or_404(Card, pk=pk)
    target_column_id = request.POST.get("target_column_id")
    target_column = get_object_or_404(Column, id=target_column_id)
    if target_column.board_id != card.column.board_id:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Invalid target board"}, status=400)
        return HttpResponseBadRequest("Invalid target board")
    card.column = target_column
    card.order = target_column.cards.count()
    card.save()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "column": target_column.id})
    return redirect("board_detail", board_id=target_column.board_id)

@require_POST
def card_delete(request, pk):
    card = get_object_or_404(Card, pk=pk)
    board_id = card.column.board_id
    card.delete()
    return redirect("board_detail", board_id=board_id)


@require_http_methods(["POST"])
def overview_lane_collection(request):
    filters = _extract_lane_filters(request)
    lane = OverviewLane.objects.create(filters=filters, position=_next_lane_position())
    return JsonResponse(_serialize_lane(lane), status=201)


@require_http_methods(["PATCH", "DELETE"])
def overview_lane_detail(request, lane_id):
    lane = get_object_or_404(OverviewLane, pk=lane_id)
    if request.method == "PATCH":
        filters = _extract_lane_filters(request)
        lane.filters = filters
        lane.save(update_fields=["filters"])
        return JsonResponse(_serialize_lane(lane))

    lane.delete()
    return JsonResponse({"success": True})


@require_POST
def board_create(request):
    name = request.POST.get("name", "").strip() or "New Board"
    unique_name = _unique_board_name(name)
    with transaction.atomic():
        board = Board.objects.create(name=unique_name)
        _create_default_columns(board)
    return redirect("board_detail", board_id=board.id)


@require_POST
def board_rename(request, pk):
    board = get_object_or_404(Board, pk=pk)
    name = request.POST.get("name", "").strip()
    if name:
        board.name = _unique_board_name(name, exclude_id=board.pk)
        board.save(update_fields=["name"])
    return redirect("board_detail", board_id=board.id)


@require_POST
def board_delete(request, pk):
    board = get_object_or_404(Board, pk=pk)
    boards = list(Board.objects.order_by("created_at", "id"))
    if len(boards) <= 1:
        return redirect("board_detail", board_id=board.id)

    try:
        idx = boards.index(board)
    except ValueError:
        idx = 0

    next_board = None
    for candidate in boards[idx + 1 :] + boards[:idx]:
        if candidate.id != board.id:
            next_board = candidate
            break

    board.delete()

    if next_board is None:
        next_board = _ensure_default_board()
    return redirect("board_detail", board_id=next_board.id)
