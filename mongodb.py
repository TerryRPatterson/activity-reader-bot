import mongoengine as mongo
from model import User, Server
from os import environ


net_if = environ["NET_IF"]

mongo.connect("activity_reader", host=net_if)
net_if = environ["NET_IF"]

mongo.connect("activity_reader", host=net_if)

# serverObject = Server(name="TestServer", id=5).save()
#
# userObject = User(name="TestUser", id=11, discriminator=300)
#
# userObject2 = User(name="Test2User", id=10, discriminator=300)
#
#
# serverObject.update(add_to_set__users=[userObject, userObject2])
#
# serverObject.save()


for server in Server.objects():
    print(server.name, server.id)
    for user in server.users:
        print(user.name, user.id)

if 5 in Server.objects():
    print("done")
