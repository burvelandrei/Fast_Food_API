from sqladmin import Admin, ModelView
from db.models import User, Category, Product
from db.connect import engine
from admin.auth import admin_auth


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.tg_id]
    form_widget_args = {
        'email': {'readonly': True},  # Поле email нельзя редактировать
        'tg_id': {'readonly': True}   # Поле tg_id тоже запрещено к изменению
    }


class CategoryAdmin(ModelView, model=Category):
    column_list = [Category.id, Category.name]


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.id, Product.name, Product.price, Product.category_id]


def setup_admin(app):
    admin = Admin(
        app, engine, authentication_backend=admin_auth, templates_dir="admin/templates"
    )
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
