from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import ensure_database, resolve_db_path
from .repository import add_ticket_reply, get_agent_by_email, get_dashboard_data, get_ticket_detail, list_tickets
from .schemas import (
    DashboardResponse,
    LoginRequest,
    LoginResponse,
    ReplyRequest,
    ReplyResponse,
    SupportUser,
    TicketDetail,
    TicketListResponse,
)
from .security import build_access_token, verify_password

APP_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"


def create_app(db_path: Path | str | None = None) -> FastAPI:
    resolved_db_path = resolve_db_path(db_path)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.db_path = ensure_database(resolved_db_path)
        yield

    app = FastAPI(
        title="PulseDesk Demo",
        version="0.1.0",
        description="Prepared support inbox repo for Agent Graph demos.",
        lifespan=lifespan,
    )
    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request) -> HTMLResponse:
        dashboard = get_dashboard_data(request.app.state.db_path)
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"dashboard": dashboard, "page_title": "PulseDesk Overview"},
        )

    @app.get("/inbox", response_class=HTMLResponse)
    async def inbox(
        request: Request,
        q: str = Query(default="", alias="q"),
        status: str | None = Query(default=None),
    ) -> HTMLResponse:
        tickets = list_tickets(request.app.state.db_path, query=q, status=status, limit=25)
        return templates.TemplateResponse(
            request=request,
            name="inbox.html",
            context={
                "tickets": tickets,
                "query": q,
                "status": status or "",
                "page_title": "Support Inbox",
            },
        )

    @app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
    async def ticket_detail_page(request: Request, ticket_id: int) -> HTMLResponse:
        ticket = get_ticket_detail(request.app.state.db_path, ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")

        return templates.TemplateResponse(
            request=request,
            name="ticket_detail.html",
            context={"ticket": ticket, "page_title": ticket["external_id"]},
        )

    @app.post("/api/login", response_model=LoginResponse)
    async def login(payload: LoginRequest, request: Request) -> LoginResponse:
        agent = get_agent_by_email(request.app.state.db_path, payload.email)
        if agent is None or not verify_password(payload.password, str(agent["password_hash"])):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not bool(agent["is_active"]):
            raise HTTPException(status_code=403, detail="Account is inactive")

        return LoginResponse(
            access_token=build_access_token(int(agent["id"]), str(agent["email"])),
            user=SupportUser(
                id=int(agent["id"]),
                email=str(agent["email"]),
                full_name=str(agent["full_name"]),
                role=str(agent["role"]),
                team=str(agent["team"]),
            ),
        )

    @app.get("/api/dashboard", response_model=DashboardResponse)
    async def dashboard(request: Request) -> DashboardResponse:
        data = get_dashboard_data(request.app.state.db_path)
        return DashboardResponse(**data)

    @app.get("/api/tickets", response_model=TicketListResponse)
    async def tickets(
        request: Request,
        q: str = Query(default="", alias="q"),
        status: str | None = Query(default=None),
        limit: int = Query(default=25, ge=1, le=50),
    ) -> TicketListResponse:
        items = list_tickets(request.app.state.db_path, query=q, status=status, limit=limit)
        return TicketListResponse(items=items, total=len(items), query=q, status=status)

    @app.get("/api/tickets/{ticket_id}", response_model=TicketDetail)
    async def ticket_detail(request: Request, ticket_id: int) -> TicketDetail:
        ticket = get_ticket_detail(request.app.state.db_path, ticket_id)
        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return TicketDetail(**ticket)

    @app.post("/api/tickets/{ticket_id}/reply", response_model=ReplyResponse)
    async def reply_to_ticket(ticket_id: int, payload: ReplyRequest, request: Request) -> ReplyResponse:
        ticket = add_ticket_reply(
            request.app.state.db_path,
            ticket_id=ticket_id,
            author_name=payload.author_name,
            body=payload.body,
            status=payload.status,
        )
        if ticket is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return ReplyResponse(ticket=TicketDetail(**ticket))

    return app


app = create_app()
