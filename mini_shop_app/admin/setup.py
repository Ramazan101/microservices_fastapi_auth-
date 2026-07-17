from sqladmin import Admin
from mini_shop_app.database.db import engine
from mini_shop_app.admin.views import UserAdmin

def setup_admin(app):
    admin = Admin(app, engine)

    admin.add_view(UserAdmin)