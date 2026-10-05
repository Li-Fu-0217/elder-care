"""菜单路径白名单，须与 vue/src/router/routeMap.js 同步。"""

PROTECTED: frozenset[str] = frozenset(
    {
        "/admin/dashboard",
        "/admin/users",
        "/admin/logs",
        "/admin/menus",
    }
)

ALLOWED: frozenset[str] = frozenset(
    {
        "/admin/dashboard",
        "/admin/elders",
        "/admin/medications",
        "/admin/bookings",
        "/admin/activities",
        "/admin/alerts",
        "/admin/knowledge",
        "/admin/agent-tools",
        "/admin/agent-logs",
        "/admin/users",
        "/admin/logs",
        "/admin/menus",
    }
)
