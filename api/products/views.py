from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
import json

from .producer import publish


from .models import Products, User
from .serializer import ProductSerializer
import random

class ProductViewSet(viewsets.ViewSet):
    def list(self, request): # /api/products
       products = Products.objects.all()
       serializer = ProductSerializer(products, many=True)
       return Response(serializer.data)

    def create(self, request): # /api/products
       serializer = ProductSerializer(data=request.data)
       serializer.is_valid(raise_exception=True)
       serializer.save()
       publish('product_created', serializer.data)
       return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrive(self, request, pk=None): # /api/products/<str:id>
        products = Products.objects.get(id=pk)
        serializer = ProductSerializer(products)
        return Response(serializer.data)

    def update(self, request, pk=None): # /api/products/<str:id>
        products = Products.objects.get(id=pk)
        serializer = ProductSerializer(instance=products, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        publish('product_updated', serializer.data)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


    def destroy(self, request, pk=None): # /api/products/<str:id>
        products = Products.objects.get(id=pk)
        products.delete()
        publish('product_deleted', pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class UserAPIView(APIView):
    def get(self, _):
        try:
            users = User.objects.all()
            user = random.choice(users)
            return Response({
                'id': user.id
            })
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        except Exception:
            return Response(error='Something went wrong', status=status.HTTP_500_INTERNAL_SERVER_ERROR)