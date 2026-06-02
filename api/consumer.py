import os
import django
import pika
import json
from django.conf import settings
from dotenv import load_dotenv

# Load local .env then initialize Django
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from products.models import Products

# Use the URL from Django settings (which loads env/.env) or fallback to env
RABBITMQ_URL = getattr(settings, 'RABBITMQ_URL', os.environ.get('RABBITMQ_URL'))
params = pika.URLParameters(RABBITMQ_URL)

connection = pika.BlockingConnection(params)

channel = connection.channel()

channel.queue_declare(queue='product_liked', durable=True)

def callback(ch, method, properties, body):
    print('Received message in product_liked')
    data = json.loads(body)
    print(data)
    if data["event"] == "product_liked":
        product_data = data["data"]
        product = Products.objects.get(id=product_data['id'])
        product.likes += 1
        product.save()
        print('Product likes increased!')

channel.basic_consume(queue='product_liked', on_message_callback=callback, auto_ack=True)

print('started consuming')

channel.start_consuming()

channel.close()