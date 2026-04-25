from __future__ import annotations

from pydantic import BaseModel, Field


class SupportUser(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    team: str


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=3, max_length=128)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: SupportUser


class TicketSummary(BaseModel):
    id: int
    external_id: str
    customer_name: str
    customer_email: str
    subject: str
    status: str
    priority: str
    queue: str
    summary: str
    assigned_agent: str | None = None
    message_count: int
    created_at: str
    updated_at: str
    last_message_at: str


class TicketListResponse(BaseModel):
    items: list[TicketSummary]
    total: int
    query: str = ""
    status: str | None = None


class TicketMessage(BaseModel):
    id: int
    author_name: str
    author_role: str
    body: str
    created_at: str


class TicketDetail(TicketSummary):
    messages: list[TicketMessage]


class ReplyRequest(BaseModel):
    author_name: str = Field(min_length=2, max_length=120)
    body: str = Field(min_length=4, max_length=2000)
    status: str = Field(default="pending_customer", min_length=3, max_length=40)


class ReplyResponse(BaseModel):
    ticket: TicketDetail


class DashboardStats(BaseModel):
    open_tickets: int
    waiting_on_customer: int
    high_priority: int
    resolved_tickets: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    recent_tickets: list[TicketSummary]

