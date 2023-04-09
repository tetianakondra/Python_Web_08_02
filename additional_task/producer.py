import json

from mongoengine import disconnect
import pika
import faker

from model import Contact

credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', port=5672, credentials=credentials))
channel = connection.channel()

channel.exchange_declare(exchange='task_mock', exchange_type='direct')
channel.queue_declare(queue='task_sms', durable=True)
channel.queue_bind(exchange='task_mock', queue='task_sms')
channel.queue_declare(queue='task_email', durable=True)
channel.queue_bind(exchange='task_mock', queue='task_email')

def main():
    fake = faker.Faker('uk-UA')
    for i in range(15):
        contact = Contact(fullname=fake.name())
        contact.email = fake.email()
        contact.phone = fake.phone_number()
        if i % 2:
            contact.better_send_to = "SMS"
        else:
            contact.better_send_to = "email"
        contact.save()
        message = str(contact.id)
        if contact.better_send_to == "email":
            channel.basic_publish(
                exchange='task_mock',
                routing_key='task_email',
                body=json.dumps(message).encode(),
                properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE))
            print(" [x] Sent via email %r" % message)
        if contact.better_send_to == "SMS":
            channel.basic_publish(
                exchange='task_mock',
                routing_key='task_sms',
                body=json.dumps(message).encode(),
                properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE))
            print(" [x] Sent via SMS %r" % message)
    connection.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        