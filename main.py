import uuid
from datetime import timedelta, datetime
from typing import Dict, List, Optional


class OrderStatus:
    PENDING = "Pending"
    PAID = "Paid"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"

class DeliveryInfo:
    def __init__(self, cost: float, delivery_time: timedelta, estimated_delivery_time: datetime):
        self.cost = cost
        self.delivery_time = delivery_time
        self.estimated_delivery_time = estimated_delivery_time

    def get_summary(self) -> str:
        return f"Информация о доставка - стоимость: {self.cost}, дата доставки: {self.estimated_delivery_time.strftime('%Y-%m-%d')})"

class Product:
    def __init__(self, name: str, description: str, price: float, stock_quantity: int):
        self.id = uuid.uuid4()
        self.name = name
        self.description = description
        self.price = price
        self.stock_quantity = stock_quantity

    def get_info(self) -> str:
        return f"Название: {self.name}, описание: {self.description}, цена: {self.price}, количество: {self.stock_quantity}"

class Customer:
    def __init__(self, name: str, email: str, address: str, phone_number: str):
        self.name = name
        self.email = email
        self.address = address
        self.phone_number = phone_number

    def get_contact_info(self) -> str:
        return f"Имя: {self.name}, электронная почта: {self.email}, адрес: {self.address}, номер телефона: {self.phone_number}"

class PaymentProcessor:
    def __init__(self, type: str):
        self.type = type

    def process_payment(self, amount: float, details: dict) -> bool:
        print('Обработка платежа')
        print(f"Платёж типа {self.type} был проведён, на сумму : {amount}.")
        print(f"Детали платежа: {details}")
        return True

class OrderItem:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity
        self.final_price = product.price * quantity

    def get_subtotal(self) -> float:
        return self.final_price

class ShoppingCart:
    def __init__(self):
        self.items: Dict[Product, int] = {}

    def add_item(self, product: Product, quantity: int):
        if product in self.items:
            self.items[product] += quantity
        else:
            self.items[product] = quantity

    def remove_item(self, product: Product):
        if product in self.items:
            del self.items[product]

    def get_items(self) -> Dict[Product, int]:
        return self.items

    def calculate_subtotal(self) -> float:
        subtotal = float(0)
        for product, quantity in self.items.items():
            subtotal += product.price * float(quantity)
        return subtotal

# стратегии скидок
class DiscountStrategy:
    def apply_discount(self, amount:float) ->float:
        raise NotImplementedError

class NoDiscount(DiscountStrategy):
    def apply_discount(self, amount:float) ->float:
        return amount

class PercentageDiscountStrategy(DiscountStrategy):
    def __init__(self, percentage:float):
        self.percentage = percentage /float('100.0')

    def apply_discount(self, amount:float) ->float:
        return amount * self.percentage

class FixedAmountDiscountStrategy(DiscountStrategy):
    def __init__(self, fixed_amount:float):
        self.fixed_amount = fixed_amount

    def apply_discount(self, amount:float) ->float:
        return min(amount, self.fixed_amount)

# --- DeliveryStrategy (Без изменений) ---
class DeliveryStrategy:
    def calculate_cost(self, address: str, total_weight: float) -> float:
        raise NotImplementedError

    def estimate_delivery_time(self, address: str) -> DeliveryInfo:
        raise NotImplementedError

class PickupDeliveryStrategy(DeliveryStrategy):
    COST = float('0.00')
    TIME_DELTA = timedelta(hours=4)

    def calculate_cost(self, address: str, total_weight: float) -> float:
        return self.COST

    def estimate_delivery_time(self, address: str) -> DeliveryInfo:
        estimated = datetime.now() + self.TIME_DELTA
        return DeliveryInfo(self.COST, self.TIME_DELTA, estimated)


class CourierDeliveryStrategy(DeliveryStrategy):
    COST = float('400.00')
    TIME_DELTA = timedelta(days=2)

    def calculate_cost(self, address: str, total_weight: float) -> float:
        return self.COST

    def estimate_delivery_time(self, address: str) -> DeliveryInfo:
        estimated = datetime.now() + self.TIME_DELTA
        return DeliveryInfo(float(0), self.TIME_DELTA, estimated)


class PostDeliveryStrategy(DeliveryStrategy):
    COST = float('150.00')
    TIME_DELTA = timedelta(days=7)

    def calculate_cost(self, address: str, total_weight: float) -> float:
        return self.COST

    def estimate_delivery_time(self, address: str) -> DeliveryInfo:
        estimated = datetime.now() + self.TIME_DELTA
        return DeliveryInfo(float(0), self.TIME_DELTA, estimated)


class Order:
    """Контекст: Фиксация транзакции. Делегирование расчета скидки и доставки стратегиям."""

    def __init__(self, customer: Customer):
        self.id = uuid.uuid4()
        self.customer = customer
        self.items: List[OrderItem] = []
        self.total_amount: float = float('0.00')
        self.status: str = OrderStatus.PENDING

        self.discount_strategy: DiscountStrategy = NoDiscount()
        self.delivery_strategy: Optional[DeliveryStrategy] = None

        self.applied_discount: float = float('0.00')
        self.delivery_info: Optional[DeliveryInfo] = None

        self.subtotal_calculated: float = float('0.00')
        self.delivery_cost: float = float('0.00')

    def set_discount_strategy(self, strategy: DiscountStrategy):
        self.discount_strategy = strategy

    def set_delivery_strategy(self, strategy: DeliveryStrategy):
        self.delivery_strategy = strategy

    def add_item_from_cart(self, product: Product, quantity: int):
        self.items.append(OrderItem(product, quantity))

    def calculate_subtotal(self) -> float:
        self.subtotal_calculated = sum(item.get_subtotal() for item in self.items)
        return self.subtotal_calculated

    def calculate_total(self, total_weight: float) -> float:

        subtotal = self.calculate_subtotal()

        self.applied_discount = self.discount_strategy.apply_discount(subtotal)
        amount_after_discount = subtotal - self.applied_discount

        if not self.delivery_strategy:
            raise ValueError("Необходимо выбрать стратегию доставки.")

        self.delivery_cost = self.delivery_strategy.calculate_cost(self.customer.address, total_weight)

        self.delivery_info = self.delivery_strategy.estimate_delivery_time(self.customer.address)
        self.delivery_info.cost = self.delivery_cost

        self.total_amount = amount_after_discount + self.delivery_cost
        return self.total_amount

    def get_order_summary(self) -> str:
        summary = (f"ID заказа: {self.id.hex[:8]}\n"
                   f"  покупатель: {self.customer.name}\n"
                   f"  Статус: {self.status}\n"
                   f"  Цена товара: {self.subtotal_calculated:.2f}\n"
                   f"  Скидка на товар: {self.applied_discount:.2f}\n"
                   f"  Цена доставки: {self.delivery_cost:.2f}\n"
                   f"  Итоговая цена: {self.total_amount:.2f}")
        return summary

# фасад

class OrderPlacementFacade:
    def __init__(self, payment_processor: PaymentProcessor):
        self.payment_processor = payment_processor

    def place_order(self,
                    cart: ShoppingCart,
                    customer: Customer,
                    discount_strategy: DiscountStrategy,
                    delivery_strategy: DeliveryStrategy,
                    delivery_details: dict,
                    payment_details: dict) -> Order:

        order = Order(customer)
        total_weight = float(delivery_details.get('weight', 0))

        for product, quantity in cart.get_items().items():
            order.add_item_from_cart(product, quantity)

        order.set_discount_strategy(discount_strategy)
        order.set_delivery_strategy(delivery_strategy)

        final_amount = order.calculate_total(total_weight)
        print(f"Расчет завершен. Сумма к оплате: {final_amount:.2f}")

        if self.payment_processor.process_payment(final_amount, payment_details):
            order.status = OrderStatus.PAID
            print(f"Заказ успешно оплачен. Статус: {order.status}")
        else:
            order.status = OrderStatus.PENDING
            print("Ошибка оплаты.")
            return order

        print("Заказ успешно оформлен")
        return order


milk = Product("Молоко", "2.5% жирности", float('85.00'), 100)
bread = Product("Хлеб", "Белый нарезной", float('40.00'), 50)
heavy_item = Product("Гантель 15кг", "Для спорта", float('1200.00'), 10)

client = Customer("Иван Петров", "ma@gmail.com", "ул. Ленина, 10, Москва", "+7-999-111-22-33")
processor = PaymentProcessor('Наличкой')

cart = ShoppingCart()
cart.add_item(milk, 2) # 170
cart.add_item(bread, 1) # 40
cart.add_item(heavy_item, 1) # 1200
print(f"Сумма корзины до скидок: {cart.calculate_subtotal():.2f}")

discount_strategy = FixedAmountDiscountStrategy(fixed_amount=float('100.0'))
delivery_strategy = CourierDeliveryStrategy()

delivery_details = {'address': client.address, 'weight': 16.0}
payment_details = {'card_number': '1234...'}

facade = OrderPlacementFacade(processor)

final_order = facade.place_order(
    cart=cart,
    customer=client,
    discount_strategy=discount_strategy,
    delivery_strategy=delivery_strategy,
    delivery_details=delivery_details,
    payment_details=payment_details
)

print("\n--- Финальный Заказ ---")
print(final_order.get_order_summary())
print(f"Детали доставки: {final_order.delivery_info.get_summary()}")



# Расчет проверки:
# Subtotal: 1410.00
# Discount: 100.00
# After Discount: 1310.00
# Delivery Cost (16кг < 20кг): 350.00
# Final Total: 1660.00