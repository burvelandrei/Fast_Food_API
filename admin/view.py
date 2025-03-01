from sqladmin import Admin, ModelView
from db.models import User, Category, Product, Order, OrderItem
from db.connect import engine
from admin.auth import admin_auth
from wtforms import IntegerField


class UserAdmin(ModelView, model=User):
    column_list = [
        "id",
        "email",
        "tg_id",
    ]
    column_searchable_list = [
        "id",
        "email",
        "tg_id",
    ]
    column_sortable_list = ["id"]
    form_excluded_columns = [
        "orders",
        "refresh_tokens",
    ]
    can_create = False


class CategoryAdmin(ModelView, model=Category):
    column_list = [
        "id",
        "name",
    ]
    column_searchable_list = [
        "id",
        "name",
    ]
    column_sortable_list = ["id", "name"]
    form_excluded_columns = [
        "products",
    ]


class ProductAdmin(ModelView, model=Product):
    column_list = [
        "id",
        "name",
        "price",
        "category_id",
    ]
    column_searchable_list = [
        "id",
        "name",
    ]
    column_sortable_list = [
        "id",
        "name",
    ]
    form_excluded_columns = ["category"]


class OrderAdmin(ModelView, model=Order):
    column_list = [
        "id",
        "user_id",
        "total_amount",
    ]
    column_searchable_list = [
        "id",
        "user_id",
    ]
    column_sortable_list = [
        "id",
        "user_id",
    ]
    form_widget_args = {
        "created_at": {"readonly": True},
    }


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        "order_id",
        "product_id",
        "name",
        "quantity",
        "total_price",
    ]
    column_searchable_list = [
        "order_id",
        "product_id",
        "name",
    ]
    column_sortable_list = [
        "order_id",
        "product_id",
        "name",
    ]


def setup_admin(app):
    admin = Admin(
        app,
        engine,
        authentication_backend=admin_auth,
        templates_dir="admin/templates",
    )
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(OrderItemAdmin)
