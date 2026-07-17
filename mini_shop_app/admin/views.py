from sqladmin import ModelView

from mini_shop_app.database.models import (
    User
)
class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.username,
        User.email,
        User.user_name,
        User.phone_number,
        User.role,
        User.date_registered,
    ]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.date_registered]
    can_create = True
    can_edit = True
    can_delete = True