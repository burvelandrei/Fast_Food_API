from sqladmin import ModelView
from wtforms import FileField
from db.models import (
    User,
    Category,
    Product,
    Order,
    OrderItem,
    Delivery,
    Size,
    ProductSize,
)
from db.connect import engine
from admin.auth import admin_auth
from admin.сustom_admin import CustomAdmin
from utils.s3_utils import upload_to_s3, get_s3_url, delete_from_s3


class UserAdmin(ModelView, model=User):
    column_list = [
        "id",
        "email",
        "tg_id",
        "created_at",
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
        "created_at",
        "updated_at",
    ]
    form_widget_args = {
        "created_at": {"readonly": True},
        "updated_at": {"readonly": True},
    }
    can_create = False
    can_export = False


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
    can_export = False


class ProductAdmin(ModelView, model=Product):
    column_list = [
        "id",
        "name",
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
    column_details_exclude_list = ["product_sizes"]
    form_excluded_columns = [
        "product_sizes",
        "created_at",
        "updated_at",
    ]
    edit_template = "sqladmin/product/edit.html"
    form_args = {"photo_name": {"label": "Photo"}}
    form_overrides = {"photo_name": FileField}
    can_export = False

    def get_photo_url(self, obj):
        model_name = obj.__class__.__name__
        file_folder = model_name.lower() + "s"
        return get_s3_url(file_folder=file_folder, file_name=obj.photo_name)

    async def on_model_change(self, data, model, is_created, request):
        file = data.get("photo_name")
        file_folder = model.__class__.__name__.lower() + "s"
        if file:
            uploaded_photo_name = await upload_to_s3(
                file_folder=file_folder,
                file=file,
                model=model,
                is_created=is_created,
            )
            model.photo_name = uploaded_photo_name
            data["photo_name"] = uploaded_photo_name

    async def on_model_delete(self, model, request):
        if model.photo_name:
            await delete_from_s3(
                file_folder = model.__class__.__name__.lower() + "s",
                file_name=model.photo_name,
            )


class SizeAdmin(ModelView, model=Size):
    column_list = ["id", "name"]
    column_searchable_list = ["id", "name"]
    column_sortable_list = ["id"]
    column_details_exclude_list = ["size_products"]
    form_excluded_columns = ["size_products"]
    can_export = False


class ProductSizeAdmin(ModelView, model=ProductSize):
    column_list = [
        "product_id",
        "product",
        "size",
        "size_id",
        "price",
        "discount",
    ]
    column_searchable_list = ["product_id", "size_id"]
    column_sortable_list = ["product_id", "size_id"]
    form_excluded_columns = [
        "created_at",
        "updated_at",
    ]
    can_export = False


class OrderAdmin(ModelView, model=Order):
    column_list = [
        "id",
        "user_id",
        "total_amount",
        "status",
        "created_at",
    ]
    column_default_sort = [
        ("status_sort", False),
        ("created_at", True),
    ]
    column_searchable_list = [
        "id",
        "user_id",
    ]
    column_sortable_list = [
        "id",
        "user_id",
        "status",
        "created_at",
    ]
    form_columns = [
        "user",
        "user_order_id",
        "order_items",
        "total_amount",
        "status",
    ]
    can_export = False


class OrderItemAdmin(ModelView, model=OrderItem):
    column_list = [
        "order_id",
        "product_id",
        "name",
        "size_name",
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
    can_export = False


class DeliveryAdmin(ModelView, model=Delivery):
    column_list = [
        "id",
        "order_id",
        "delivery_type",
        "delivery_address",
    ]
    column_searchable_list = [
        "order_id",
        "delivery_address",
    ]
    column_sortable_list = [
        "order_id",
        "delivery_type",
    ]
    can_export = False


# Функция для инициализации админки и подключения моделей админки
def setup_admin(app):
    admin = CustomAdmin(
        app,
        engine,
        authentication_backend=admin_auth,
        templates_dir="admin/templates",
        debug=True
    )
    admin.add_view(UserAdmin)
    admin.add_view(CategoryAdmin)
    admin.add_view(ProductAdmin)
    admin.add_view(ProductSizeAdmin)
    admin.add_view(SizeAdmin)
    admin.add_view(OrderAdmin)
    admin.add_view(OrderItemAdmin)
    admin.add_view(DeliveryAdmin)
