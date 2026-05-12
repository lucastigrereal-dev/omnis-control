"""Models for App Factory — AppIdea, AppRequirement, AppBlueprint, AppArtifact."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# ── Domain constants ──────────────────────────────────────────────────────────

STATUS_DRAFT = "draft"
STATUS_PLANNED = "planned"
STATUS_GENERATED = "generated"
STATUS_FAILED = "failed"

APP_TYPE_WEB = "web"
APP_TYPE_CLI = "cli"
APP_TYPE_API = "api"
APP_TYPE_MOBILE = "mobile"
APP_TYPE_DESKTOP = "desktop"
APP_TYPE_LIBRARY = "library"


def _make_id(prefix: str) -> str:
    raw = os.urandom(8)
    return f"{prefix}_{hashlib.sha256(raw).hexdigest()[:10]}"


# ── AppIdea ───────────────────────────────────────────────────────────────────

@dataclass
class AppIdea:
    """Raw idea submitted by a user before any processing."""
    idea_id: str
    title: str
    description: str
    target_audience: str
    features: list[str]
    constraints: list[str]
    domain: str
    submitted_at: str
    status: str

    @classmethod
    def new(
        cls,
        title: str,
        description: str = "",
        target_audience: str = "",
        features: Optional[list[str]] = None,
        constraints: Optional[list[str]] = None,
        domain: str = "",
    ) -> "AppIdea":
        return cls(
            idea_id=_make_id("idea"),
            title=title.strip(),
            description=description.strip(),
            target_audience=target_audience.strip(),
            features=list(features) if features else [],
            constraints=list(constraints) if constraints else [],
            domain=domain.strip(),
            submitted_at=datetime.now(timezone.utc).isoformat(),
            status=STATUS_DRAFT,
        )

    def to_dict(self) -> dict:
        return {
            "idea_id": self.idea_id,
            "title": self.title,
            "description": self.description,
            "target_audience": self.target_audience,
            "features": self.features,
            "constraints": self.constraints,
            "domain": self.domain,
            "submitted_at": self.submitted_at,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AppIdea":
        return cls(
            idea_id=d["idea_id"],
            title=d["title"],
            description=d.get("description", ""),
            target_audience=d.get("target_audience", ""),
            features=d.get("features", []),
            constraints=d.get("constraints", []),
            domain=d.get("domain", ""),
            submitted_at=d.get("submitted_at", ""),
            status=d.get("status", STATUS_DRAFT),
        )

    def validate(self) -> list[str]:
        """Return list of validation issues (empty = valid)."""
        issues: list[str] = []
        if not self.title:
            issues.append("title is required")
        if not self.description:
            issues.append("description is required")
        if len(self.title) > 200:
            issues.append("title exceeds 200 characters")
        return issues

    @property
    def is_valid(self) -> bool:
        return len(self.validate()) == 0


# ── AppRequirement ────────────────────────────────────────────────────────────

@dataclass
class AppRequirement:
    """Structured requirements derived deterministically from an AppIdea."""
    requirement_id: str
    idea_id: str
    functional: list[str]
    non_functional: list[str]
    domain_entities: list[str]
    user_roles: list[str]
    app_type: str
    generated_at: str

    @classmethod
    def from_idea(cls, idea: AppIdea) -> "AppRequirement":
        functional, non_functional, entities, roles, app_type = _extract_requirements(idea)
        return cls(
            requirement_id=_make_id("req"),
            idea_id=idea.idea_id,
            functional=functional,
            non_functional=non_functional,
            domain_entities=entities,
            user_roles=roles,
            app_type=app_type,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "requirement_id": self.requirement_id,
            "idea_id": self.idea_id,
            "functional": self.functional,
            "non_functional": self.non_functional,
            "domain_entities": self.domain_entities,
            "user_roles": self.user_roles,
            "app_type": self.app_type,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AppRequirement":
        return cls(
            requirement_id=d["requirement_id"],
            idea_id=d["idea_id"],
            functional=d.get("functional", []),
            non_functional=d.get("non_functional", []),
            domain_entities=d.get("domain_entities", []),
            user_roles=d.get("user_roles", []),
            app_type=d.get("app_type", APP_TYPE_WEB),
            generated_at=d.get("generated_at", ""),
        )


# ── AppBlueprint ──────────────────────────────────────────────────────────────

@dataclass
class AppBlueprint:
    """Architectural blueprint derived from AppRequirements."""
    blueprint_id: str
    requirement_id: str
    modules: list[dict]
    data_models: list[dict]
    api_endpoints: list[dict]
    component_tree: dict
    tech_stack: dict
    generated_at: str

    @classmethod
    def from_requirement(cls, req: AppRequirement) -> "AppBlueprint":
        modules = _design_modules(req)
        data_models = _design_data_models(req)
        api_endpoints = _design_api_endpoints(req)
        component_tree = _design_component_tree(req)
        tech_stack = _pick_tech_stack(req)
        return cls(
            blueprint_id=_make_id("bp"),
            requirement_id=req.requirement_id,
            modules=modules,
            data_models=data_models,
            api_endpoints=api_endpoints,
            component_tree=component_tree,
            tech_stack=tech_stack,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "blueprint_id": self.blueprint_id,
            "requirement_id": self.requirement_id,
            "modules": self.modules,
            "data_models": self.data_models,
            "api_endpoints": self.api_endpoints,
            "component_tree": self.component_tree,
            "tech_stack": self.tech_stack,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AppBlueprint":
        return cls(
            blueprint_id=d["blueprint_id"],
            requirement_id=d["requirement_id"],
            modules=d.get("modules", []),
            data_models=d.get("data_models", []),
            api_endpoints=d.get("api_endpoints", []),
            component_tree=d.get("component_tree", {}),
            tech_stack=d.get("tech_stack", {}),
            generated_at=d.get("generated_at", ""),
        )


# ── AppArtifact ───────────────────────────────────────────────────────────────

@dataclass
class AppArtifact:
    """Final deliverable: PRD markdown + project structure plan."""
    artifact_id: str
    blueprint_id: str
    prd_markdown: str
    project_structure: dict
    tech_stack_summary: dict
    generated_at: str

    @classmethod
    def from_blueprint(cls, blueprint: AppBlueprint, prd_md: str, structure: dict) -> "AppArtifact":
        return cls(
            artifact_id=_make_id("art"),
            blueprint_id=blueprint.blueprint_id,
            prd_markdown=prd_md,
            project_structure=structure,
            tech_stack_summary=blueprint.tech_stack,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "blueprint_id": self.blueprint_id,
            "prd_markdown": self.prd_markdown,
            "project_structure": self.project_structure,
            "tech_stack_summary": self.tech_stack_summary,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AppArtifact":
        return cls(
            artifact_id=d["artifact_id"],
            blueprint_id=d["blueprint_id"],
            prd_markdown=d.get("prd_markdown", ""),
            project_structure=d.get("project_structure", {}),
            tech_stack_summary=d.get("tech_stack_summary", {}),
            generated_at=d.get("generated_at", ""),
        )


# ── Deterministic requirement extraction ──────────────────────────────────────

_KEYWORD_ROLES: dict[str, list[str]] = {
    "admin": ["admin", "administrador", "dashboard", "painel"],
    "user": ["user", "usuario", "cliente", "customer", "assinante", "subscriber"],
    "editor": ["editor", "author", "autor", "content", "conteudo"],
    "viewer": ["viewer", "visitante", "guest", "convidado"],
}

_KEYWORD_ENTITIES: dict[str, list[str]] = {
    "user": ["user", "usuario", "account", "conta", "profile", "perfil"],
    "product": ["product", "produto", "item", "catalog", "catalogo"],
    "order": ["order", "pedido", "purchase", "compra", "cart", "carrinho"],
    "content": ["post", "article", "artigo", "page", "pagina", "blog"],
    "task": ["task", "tarefa", "todo", "kanban", "project", "projeto"],
    "payment": ["payment", "pagamento", "invoice", "fatura", "billing", "cobranca"],
    "notification": ["notification", "notificacao", "alert", "alerta", "email"],
    "analytics": ["analytics", "metric", "metrica", "dashboard", "report", "relatorio"],
    "file": ["file", "arquivo", "upload", "document", "documento", "media"],
}

_REQUIREMENT_TEMPLATES: dict[str, dict] = {
    "auth": {
        "functional": ["User registration", "User login/logout", "Password reset", "Session management"],
        "non_functional": ["Passwords hashed with bcrypt/argon2", "Session timeout after 30min inactivity"],
    },
    "crud": {
        "functional": ["Create resource", "Read/list resources", "Update resource", "Delete resource", "Pagination support"],
        "non_functional": ["Response time < 200ms for list endpoints"],
    },
    "search": {
        "functional": ["Full-text search", "Filtered search", "Sort results"],
        "non_functional": ["Search results < 500ms"],
    },
}


def _detect_roles(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for role, keywords in _KEYWORD_ROLES.items():
        if any(kw in lower for kw in keywords):
            found.append(role)
    return found if found else ["user"]


def _detect_entities(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for entity, keywords in _KEYWORD_ENTITIES.items():
        if any(kw in lower for kw in keywords):
            found.append(entity)
    return found


def _detect_app_type(features: list[str], description: str) -> str:
    combined = " ".join(features).lower() + " " + description.lower()
    if any(kw in combined for kw in ["api", "rest", "graphql", "endpoint", "microservice"]):
        return APP_TYPE_API
    if any(kw in combined for kw in ["mobile", "ios", "android", "app store", "pwa"]):
        return APP_TYPE_MOBILE
    if any(kw in combined for kw in ["cli", "command-line", "terminal", "script"]):
        return APP_TYPE_CLI
    if any(kw in combined for kw in ["desktop", "gui", "tkinter", "electron", "tauri"]):
        return APP_TYPE_DESKTOP
    if any(kw in combined for kw in ["library", "package", "sdk", "module"]):
        return APP_TYPE_LIBRARY
    return APP_TYPE_WEB


def _extract_requirements(idea: AppIdea) -> tuple[list[str], list[str], list[str], list[str], str]:
    combined_text = f"{idea.title} {idea.description} {' '.join(idea.features)}"
    combined_lower = combined_text.lower()

    functional: list[str] = []
    non_functional: list[str] = []

    # Map features to requirements
    for feature in idea.features:
        functional.append(feature if feature.endswith(".") else feature)

    # Apply templates based on keyword detection
    if any(kw in combined_lower for kw in ["login", "auth", "signup", "cadastro", "autentic", "password", "senha"]):
        t = _REQUIREMENT_TEMPLATES["auth"]
        functional.extend(t["functional"])
        non_functional.extend(t["non_functional"])

    if any(kw in combined_lower for kw in ["crud", "create", "edit", "delete", "manage", "gerenci", "admin"]):
        t = _REQUIREMENT_TEMPLATES["crud"]
        functional.extend(t["functional"])
        non_functional.extend(t["non_functional"])

    if any(kw in combined_lower for kw in ["search", "busca", "filter", "filtro", "query"]):
        t = _REQUIREMENT_TEMPLATES["search"]
        functional.extend(t["functional"])
        non_functional.extend(t["non_functional"])

    # Default: always add basic CRUD + health
    if not functional:
        functional = [
            "System health check endpoint",
            "Create resource",
            "List resources with pagination",
            "Get resource by ID",
            "Update resource",
            "Delete resource",
        ]
        non_functional = [
            "Response time < 500ms p95",
            "99.9% uptime target",
        ]

    # Deduplicate while preserving order
    seen_f = set()
    functional = [x for x in functional if not (x in seen_f or seen_f.add(x))]
    seen_nf = set()
    non_functional = [x for x in non_functional if not (x in seen_nf or seen_nf.add(x))]

    roles = _detect_roles(combined_text)
    entities = _detect_entities(combined_text)
    app_type = _detect_app_type(idea.features, idea.description)

    return functional, non_functional, entities or ["resource"], roles, app_type


# ── Deterministic blueprint design functions ───────────────────────────────────

def _design_modules(req: AppRequirement) -> list[dict]:
    modules: list[dict] = []

    modules.append({"name": "core", "purpose": "Configuration, exceptions, base classes", "depends_on": []})

    if any("auth" in f.lower() or "login" in f.lower() or "regist" in f.lower() for f in req.functional):
        modules.append({"name": "auth", "purpose": "Authentication and authorization", "depends_on": ["core"]})

    for entity in req.domain_entities:
        modules.append({"name": entity, "purpose": f"CRUD operations for {entity}", "depends_on": ["core"]})

    if any("search" in f.lower() or "busca" in f.lower() for f in req.functional):
        modules.append({"name": "search", "purpose": "Full-text search engine", "depends_on": ["core"]})

    if any("notif" in f.lower() or "email" in f.lower() or "alert" in f.lower() for f in req.functional):
        modules.append({"name": "notifications", "purpose": "Email, push, and in-app notifications", "depends_on": ["core"]})

    if req.app_type == APP_TYPE_WEB or req.app_type == APP_TYPE_MOBILE:
        modules.append({"name": "web", "purpose": "HTTP routes, middleware, templating", "depends_on": ["core", "auth"]})

    modules.append({"name": "tests", "purpose": "Test suite covering all modules", "depends_on": []})

    return modules


def _design_data_models(req: AppRequirement) -> list[dict]:
    models: list[dict] = []
    for entity in req.domain_entities:
        model = {
            "name": entity.capitalize(),
            "table": entity.lower() + "s",
            "fields": [
                {"name": "id", "type": "UUID", "pk": True},
                {"name": "created_at", "type": "datetime", "nullable": False},
                {"name": "updated_at", "type": "datetime", "nullable": False},
            ],
            "relationships": [],
        }
        models.append(model)

    # Add user model if auth is present
    if "user" not in req.domain_entities and any(r in str(req.functional).lower() for r in ["auth", "login", "user"]):
        models.insert(0, {
            "name": "User",
            "table": "users",
            "fields": [
                {"name": "id", "type": "UUID", "pk": True},
                {"name": "email", "type": "str", "unique": True, "nullable": False},
                {"name": "password_hash", "type": "str", "nullable": False},
                {"name": "role", "type": "str", "nullable": False},
                {"name": "created_at", "type": "datetime", "nullable": False},
                {"name": "updated_at", "type": "datetime", "nullable": False},
            ],
            "relationships": [],
        })

    return models


def _design_api_endpoints(req: AppRequirement) -> list[dict]:
    endpoints: list[dict] = []
    endpoints.append({"method": "GET", "path": "/health", "description": "Health check"})

    entity_names = req.domain_entities if req.domain_entities else ["resource"]
    for entity in entity_names:
        base = f"/api/{entity}s"
        endpoints.append({"method": "POST", "path": base, "description": f"Create {entity}"})
        endpoints.append({"method": "GET", "path": base, "description": f"List {entity}s"})
        endpoints.append({"method": "GET", "path": f"{base}/{{id}}", "description": f"Get {entity} by ID"})
        endpoints.append({"method": "PUT", "path": f"{base}/{{id}}", "description": f"Update {entity}"})
        endpoints.append({"method": "DELETE", "path": f"{base}/{{id}}", "description": f"Delete {entity}"})

    if any("auth" in f.lower() for f in req.functional):
        endpoints.extend([
            {"method": "POST", "path": "/api/auth/register", "description": "Register new user"},
            {"method": "POST", "path": "/api/auth/login", "description": "Login user"},
            {"method": "POST", "path": "/api/auth/logout", "description": "Logout user"},
        ])

    return endpoints


def _design_component_tree(req: AppRequirement) -> dict:
    if req.app_type in (APP_TYPE_CLI, APP_TYPE_LIBRARY):
        return {"type": "cli", "components": []}

    tree: dict = {
        "type": "web_app",
        "layout": "AppLayout",
        "components": [
            {"name": "Navbar", "children": []},
            {"name": "Sidebar", "children": []},
            {"name": "MainContent", "children": [
                {"name": "RouterView", "children": []},
            ]},
            {"name": "Footer", "children": []},
        ],
    }

    if any("auth" in f.lower() for f in req.functional):
        tree["components"].append({
            "name": "AuthPages",
            "children": [
                {"name": "LoginPage", "children": []},
                {"name": "RegisterPage", "children": []},
            ],
        })

    if "admin" in req.user_roles:
        tree["components"].append({
            "name": "AdminDashboard",
            "children": [
                {"name": "UserManagement", "children": []},
                {"name": "SystemMetrics", "children": []},
            ],
        })

    for entity in req.domain_entities:
        entity_title = entity.capitalize()
        tree["components"].append({
            "name": f"{entity_title}Pages",
            "children": [
                {"name": f"{entity_title}List", "children": []},
                {"name": f"{entity_title}Detail", "children": []},
                {"name": f"{entity_title}Form", "children": []},
            ],
        })

    return tree


def _pick_tech_stack(req: AppRequirement) -> dict:
    stacks = {
        APP_TYPE_WEB: {"frontend": "React + TypeScript", "backend": "Python FastAPI", "database": "PostgreSQL", "cache": "Redis", "runtime": "Python >= 3.11"},
        APP_TYPE_API: {"frontend": "N/A", "backend": "Python FastAPI", "database": "PostgreSQL", "cache": "Redis", "runtime": "Python >= 3.11"},
        APP_TYPE_CLI: {"frontend": "N/A", "backend": "Python + Typer", "database": "SQLite", "cache": "N/A", "runtime": "Python >= 3.11"},
        APP_TYPE_MOBILE: {"frontend": "React Native + TypeScript", "backend": "Python FastAPI", "database": "PostgreSQL", "cache": "Redis", "runtime": "Python >= 3.11"},
        APP_TYPE_DESKTOP: {"frontend": "Electron + React + TypeScript", "backend": "Python FastAPI", "database": "SQLite", "cache": "N/A", "runtime": "Python >= 3.11"},
        APP_TYPE_LIBRARY: {"frontend": "N/A", "backend": "Python library", "database": "N/A", "cache": "N/A", "runtime": "Python >= 3.11"},
    }
    return stacks.get(req.app_type, stacks[APP_TYPE_WEB])
