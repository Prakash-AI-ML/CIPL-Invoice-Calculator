from fastapi import APIRouter

from .endpoints import auth, users, category, admin,  menu_permissions, menus, client_details, button_permissions, buttons, roles, user_management, impersonate, dashboard, cipl, delivery_order, delivery_order_setting

api_router = APIRouter()  # Main V1 router

# Include sub-routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(impersonate.router, prefix="/impersonate", tags=["Impersonate"], include_in_schema= False)
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=['Dashboard'])
api_router.include_router(user_management.router, prefix="/user", tags=["User Management"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(category.router, prefix="/category", tags=["Category Management"])
api_router.include_router(menus.router, prefix="/menus", tags=["menus"])
api_router.include_router(buttons.router, prefix="/buttons", tags=["buttons"])
api_router.include_router(button_permissions.router, prefix="/button-permissions", tags=["button_permissions"])
api_router.include_router(menu_permissions.router, prefix="/menu-permissions", tags=["menu_permissions"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(client_details.router, prefix="/client-details", tags=["Clients Details"])

api_router.include_router(cipl.router, prefix="/cipl", tags=["CIPL"])
api_router.include_router(delivery_order.router, prefix="/do", tags=["Delivery Orders"])
api_router.include_router(delivery_order_setting.router, prefix="/delivery-order", tags=["Delivery Order Settings"])
# Export for parent import
__all__ = ["api_router"]