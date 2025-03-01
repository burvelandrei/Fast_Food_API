from sqladmin import Admin, ModelView
from db.models import User
from db.connect import engine
from admin.auth import admin_auth


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.tg_id]


def setup_admin(app):
    admin = Admin(
        app, engine, authentication_backend=admin_auth, templates_dir="admin/templates"
    )
    admin.add_view(UserAdmin)
