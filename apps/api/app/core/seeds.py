import asyncio
import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, async_engine
from app.models.role import Permission, Role, RolePermission

logger = structlog.get_logger(__name__)

# Définition des rôles selon docs/rbac-matrix.md
ROLES_DATA = [
    {
        "code": "admin",
        "label": "Administrateur",
        "description": "Configuration globale, utilisateurs, règles, paramètres, audit",
    },
    {
        "code": "operator",
        "label": "Opérateur",
        "description": "Supervision quotidienne, dashboard, événements, alertes, acquittement",
    },
    {
        "code": "analyst",
        "label": "Analyste",
        "description": "Historique, analytics, rapports, exports",
    },
    {
        "code": "viewer",
        "label": "Lecteur",
        "description": "Consultation en lecture seule des vues autorisées",
    },
]

# Permissions par rôle selon la matrice stricte de docs/rbac-matrix.md
ROLE_PERMISSIONS_MATRIX: dict[str, list[tuple[str, str]]] = {
    "admin": [
        ("user", "manage"),
        ("role", "manage"),
        ("site", "manage"),
        ("zone", "manage"),
        ("device", "manage"),
        ("sensor", "manage"),
        ("event", "read"),
        ("event", "export"),
        ("rule", "manage"),
        ("alert", "manage"),
        ("notification", "manage"),
        ("analysis", "manage"),
        ("report", "manage"),
        ("ai", "manage"),
        ("audit", "read"),
        ("setting", "manage"),
    ],
    "operator": [
        ("site", "read"),
        ("zone", "read"),
        ("zone", "update"),
        ("device", "read"),
        ("sensor", "read"),
        ("event", "read"),
        ("rule", "read"),
        ("alert", "read"),
        ("alert", "acknowledge"),
        ("alert", "assign"),
        ("alert", "update"),
        ("alert", "export"),
        ("notification", "read"),
        ("analysis", "read"),
        ("report", "read"),
        ("ai", "execute"),
    ],
    "analyst": [
        ("site", "read"),
        ("zone", "read"),
        ("device", "read"),
        ("sensor", "read"),
        ("event", "read"),
        ("event", "export"),
        ("rule", "read"),
        ("alert", "read"),
        ("alert", "export"),
        ("notification", "read"),
        ("analysis", "read"),
        ("analysis", "create"),
        ("analysis", "execute"),
        ("analysis", "export"),
        ("report", "read"),
        ("report", "create"),
        ("report", "export"),
        ("ai", "execute"),
        ("audit", "read"),
    ],
    "viewer": [
        ("site", "read"),
        ("zone", "read"),
        ("device", "read"),
        ("sensor", "read"),
        ("event", "read"),
        ("alert", "read"),
    ],
}


async def seed_roles_and_permissions(session: AsyncSession) -> None:
    """Seed idempotent des rôles, permissions et associations RBAC."""
    logger.info("Starting RBAC seed...")

    # 1. Collecter toutes les permissions uniques
    all_permissions_set: set[tuple[str, str]] = set()
    for perms in ROLE_PERMISSIONS_MATRIX.values():
        all_permissions_set.update(perms)

    # 2. Insérer ou récupérer les permissions
    permission_map: dict[str, Permission] = {}
    for resource, action in all_permissions_set:
        code = f"{resource}:{action}"
        perm_query = select(Permission).where(Permission.code == code)
        perm_result = await session.execute(perm_query)
        existing_perm = perm_result.scalar_one_or_none()
        if existing_perm is None:
            new_perm = Permission(
                id=uuid.uuid4(),
                code=code,
                resource=resource,
                action=action,
            )
            session.add(new_perm)
            await session.flush()
            permission_map[code] = new_perm
        else:
            permission_map[code] = existing_perm

    # 3. Insérer ou récupérer les rôles et lier les permissions
    for role_data in ROLES_DATA:
        role_code = str(role_data["code"])
        role_query = select(Role).where(Role.code == role_code)
        role_result = await session.execute(role_query)
        role_record = role_result.scalar_one_or_none()
        if role_record is None:
            role_record = Role(
                id=uuid.uuid4(),
                code=role_code,
                label=str(role_data["label"]),
                description=str(role_data["description"]),
            )
            session.add(role_record)
            await session.flush()

        # Associer les permissions au rôle
        expected_perms = ROLE_PERMISSIONS_MATRIX.get(role_record.code, [])
        for resource, action in expected_perms:
            perm_code = f"{resource}:{action}"
            target_perm = permission_map[perm_code]
            # Vérifier si l'association existe déjà
            assoc_query = select(RolePermission).where(
                RolePermission.role_id == role_record.id,
                RolePermission.permission_id == target_perm.id,
            )
            assoc_result = await session.execute(assoc_query)
            if assoc_result.scalar_one_or_none() is None:
                assoc_record = RolePermission(
                    role_id=role_record.id,
                    permission_id=target_perm.id,
                )
                session.add(assoc_record)

    await session.commit()
    logger.info("RBAC seed completed successfully.")


async def main() -> None:
    """Entrypoint CLI pour exécuter le seed directement."""
    async with AsyncSessionLocal() as session:
        await seed_roles_and_permissions(session)
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
