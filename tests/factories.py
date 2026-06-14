from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from accounts.models import User, UserRole
from orders.models import Cart
from products.models import Product


def create_user(username, password="testpass123", role=UserRole.BUYER, **kwargs):
    user = User.objects.create_user(username=username, password=password, role=role, **kwargs)
    if role == UserRole.BUYER:
        Cart.objects.get_or_create(user=user)
    return user


def create_test_image(name="test.jpg"):
    image = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


def create_product(seller, title="Test Product", quantity=10, unit_price="19.99", **kwargs):
    defaults = {
        "description": "A test product description.",
        "unit_price": unit_price,
        "quantity": quantity,
        "image": create_test_image(),
    }
    defaults.update(kwargs)
    return Product.objects.create(seller=seller, title=title, **defaults)
