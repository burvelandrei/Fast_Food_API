from sqladmin import Admin, ModelView
from db.models import User, Category, Product, Order, OrderItem, Delivery
from db.connect import engine
from admin.auth import admin_auth


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
    form_columns = [
        "id",
        "email",
        "tg_id",
        "hashed_password",
        "orders",
        "is_admin",
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
    column_sortable_list = [
        "id",
        "name",
    ]
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


class OrderAdmin(ModelView, model=Order):
    column_list = [
        "id",
        "user_id",
        "total_amount",
        "status",
        "created_at_moscow",
    ]
    column_default_sort = [
        ("status_sort", False),
        ("created_at_moscow", True),
    ]
    column_searchable_list = [
        "id",
        "user_id",
    ]
    column_sortable_list = [
        "id",
        "user_id",
        "status",
        "created_at_moscow",
    ]
    form_columns = [
        "user",
        "user_order_id",
        "order_items",
        "total_amount",
        "status",
        "created_at",
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


class DeliveryAdmin(ModelView, model=Delivery):
    column_list = [
        "id",
        "order_id",
        "delivery_type",
        "delivery_address"
    ]
    column_searchable_list = [
        "order_id",
        "delivery_address",
    ]
    column_sortable_list = [
        "order_id",
        "delivery_type",
    ]


# Функция для инициализации админки и подключения моделей админки
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
    admin.add_view(DeliveryAdmin)
