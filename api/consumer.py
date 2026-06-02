import os
import django
import pika
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from products.models import Products

params = pika.URLParameters('amqps://kmyhyinc:2A1RjChfIOBnbQhNLEorkQUKRO0JLyMa@capybara.lmq.cloudamqp.com/kmyhyinc')

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