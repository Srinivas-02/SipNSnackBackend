from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pos.apps.menu.models import CategoryModel
from pos.apps.accounts.models import User
from pos.apps.locations.models import LocationModel
from django.shortcuts import get_object_or_404
from pos.utils.logger import POSLogger

logger = POSLogger(__name__)

class CategoryView(APIView):
    def _check_franchise_admin_locations(self, user, location_ids):
        """Check if franchise admin has access to all provided location IDs."""
        admin = get_object_or_404(User, id=user.id, is_franchise_admin=True)
        admin_location_ids = {loc.id for loc in admin.locations.all()}
        return all(loc_id in admin_location_ids for loc_id in location_ids)

    def get(self, request):
        """Get all categories."""
        try:
            if request.user.is_super_admin:
                categories = CategoryModel.objects.select_related('location').all().order_by('display_order')
            elif request.user.is_franchise_admin or request.user.is_staff_member:
                requester = get_object_or_404(User, id=request.user.id)
                categories = CategoryModel.objects.select_related('location').filter(
                    location__in=requester.locations.all()
                ).order_by('display_order')
            else:
                logger.warning(f"Unauthorized access attempt by {request.user.email}")
                return Response(
                    {'status': 'error', 'message': 'Not authorized'},
                    status=status.HTTP_403_FORBIDDEN
                )

            data = [{
                'id': category.id,
                'name': category.name,
                'location_id': category.location.id,
                'display_order': category.display_order
            } for category in categories]
            logger.info(f"Categories accessed by {request.user.email}: {len(data)} categories")
            return Response({'status': 'success', 'categories': data})
        except Exception as e:
            logger.error(f"Error fetching categories for {request.user.email}: {str(e)}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def post(self, request):
        """Create a new category."""
        try:
            # Validate input
            name = request.data.get('name')
            location_id = request.data.get('location_id')
            display_order = request.data.get('display_order', 0)
            
            if not name or not isinstance(name, str) or name.strip() == '':
                logger.warning(f"Invalid name in category creation by {request.user.email}: {name}")
                return Response(
                    {'status': 'error', 'message': 'Category name is required and must be a non-empty string'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not location_id or not isinstance(location_id, int):
                logger.warning(f"Invalid location_id in category creation by {request.user.email}: {location_id}")
                return Response(
                    {'status': 'error', 'message': 'Valid location_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if not isinstance(display_order, int) or display_order < 0:
                logger.warning(f"Invalid display_order in category creation by {request.user.email}: {display_order}")
                return Response(
                    {'status': 'error', 'message': 'Display order must be a non-negative integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            requested_location = LocationModel.objects.get(id=location_id)
            
            if request.user.is_super_admin:
                category = CategoryModel.objects.create(
                    name=name.strip(),
                    display_order=display_order,
                    location=requested_location
                )
                logger.info(f"Category '{category.name}' (ID: {category.id}) created by super admin {request.user.email} for location {location_id}")
                return Response({
                    'status': 'success',
                    'id': category.id,
                    'name': category.name,
                    'location_id': category.location.id,
                    'display_order': category.display_order
                }, status=status.HTTP_201_CREATED)
            
            elif request.user.is_franchise_admin:
                if not self._check_franchise_admin_locations(request.user, [location_id]):
                    logger.warning(f"Franchise admin {request.user.email} attempted to create category in unauthorized location {location_id}")
                    return Response(
                        {'status': 'error', 'message': 'You do not have access to this location'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                category = CategoryModel.objects.create(
                    name=name.strip(),
                    display_order=display_order,
                    location=requested_location
                )
                logger.info(f"Category '{category.name}' (ID: {category.id}) created by franchise admin {request.user.email} for location {location_id}")
                return Response({
                    'status': 'success',
                    'id': category.id,
                    'name': category.name,
                    'location_id': category.location.id,
                    'display_order': category.display_order
                }, status=status.HTTP_201_CREATED)
            
            else:
                logger.warning(f"Unauthorized create attempt by {request.user.email}")
                return Response(
                    {'status': 'error', 'message': 'Not authorized to create categories'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except LocationModel.DoesNotExist:
            logger.error(f"Location {location_id} not found for {request.user.email}")
            return Response(
                {'status': 'error', 'message': 'Location not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error creating category for {request.user.email}: {str(e)}, Request data: {request.data}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def put(self, request):
        """Update an existing category."""
        try:
            category_id = request.data.get('id')
            if not category_id or not isinstance(category_id, int):
                logger.warning(f"Invalid category ID in update attempt by {request.user.email}: {category_id}")
                return Response(
                    {'status': 'error', 'message': 'Valid category ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            category = CategoryModel.objects.select_related('location').get(id=category_id)
            
            # Validate input
            name = request.data.get('name')
            location_id = request.data.get('location_id')
            display_order = request.data.get('display_order')
            
            if name and (not isinstance(name, str) or name.strip() == ''):
                logger.warning(f"Invalid name in category update by {request.user.email}: {name}")
                return Response(
                    {'status': 'error', 'message': 'Category name must be a non-empty string'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if location_id and not isinstance(location_id, int):
                logger.warning(f"Invalid location_id in category update by {request.user.email}: {location_id}")
                return Response(
                    {'status': 'error', 'message': 'Valid location_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if display_order is not None and (not isinstance(display_order, int) or display_order < 0):
                logger.warning(f"Invalid display_order in category update by {request.user.email}: {display_order}")
                return Response(
                    {'status': 'error', 'message': 'Display order must be a non-negative integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if request.user.is_super_admin:
                if name:
                    category.name = name.strip()
                if display_order is not None:
                    category.display_order = display_order
                if location_id:
                    requested_location = LocationModel.objects.get(id=location_id)
                    category.location = requested_location
                category.save()
                logger.info(f"Category '{category.name}' (ID: {category.id}) updated by super admin {request.user.email}")
                return Response({
                    'status': 'success',
                    'id': category.id,
                    'name': category.name,
                    'location_id': category.location.id,
                    'display_order': category.display_order
                })
            
            elif request.user.is_franchise_admin:
                current_location_id = category.location.id
                new_location_id = location_id if location_id else current_location_id
                if not self._check_franchise_admin_locations(request.user, [current_location_id, new_location_id]):
                    logger.warning(f"Franchise admin {request.user.email} attempted to update category {category.id} without access to locations {current_location_id} or {new_location_id}")
                    return Response(
                        {'status': 'error', 'message': 'You do not have access to one or both locations'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                if name:
                    category.name = name.strip()
                if display_order is not None:
                    category.display_order = display_order
                if location_id:
                    requested_location = LocationModel.objects.get(id=location_id)
                    category.location = requested_location
                category.save()
                logger.info(f"Category '{category.name}' (ID: {category.id}) updated by franchise admin {request.user.email}")
                return Response({
                    'status': 'success',
                    'id': category.id,
                    'name': category.name,
                    'location_id': category.location.id,
                    'display_order': category.display_order
                })
            
            else:
                logger.warning(f"Unauthorized update attempt by {request.user.email} for category {category_id}")
                return Response(
                    {'status': 'error', 'message': 'Not authorized to update categories'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except CategoryModel.DoesNotExist:
            logger.error(f"Category {category_id} not found for {request.user.email}")
            return Response(
                {'status': 'error', 'message': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except LocationModel.DoesNotExist:
            logger.error(f"Location {location_id} not found for {request.user.email}")
            return Response(
                {'status': 'error', 'message': 'Location not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error updating category for {request.user.email}: {str(e)}, Request data: {request.data}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def delete(self, request):
        """Delete a category."""
        try:
            category_id = request.data.get('id')
            if not category_id or not isinstance(category_id, int):
                logger.warning(f"Invalid category ID in delete attempt by {request.user.email}: {category_id}")
                return Response(
                    {'status': 'error', 'message': 'Valid category ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            category = CategoryModel.objects.select_related('location').get(id=category_id)
            
            if request.user.is_super_admin:
                category_name = category.name
                category.delete()
                logger.info(f"Category '{category_name}' (ID: {category_id}) deleted by super admin {request.user.email}")
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            
            elif request.user.is_franchise_admin:
                if not self._check_franchise_admin_locations(request.user, [category.location.id]):
                    logger.warning(f"Franchise admin {request.user.email} attempted to delete category {category.id} without access to location {category.location.id}")
                    return Response(
                        {'status': 'error', 'message': 'You do not have access to this location'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                category_name = category.name
                category.delete()
                logger.info(f"Category '{category_name}' (ID: {category_id}) deleted by franchise admin {request.user.email}")
                return Response({'status': 'success'}, status=status.HTTP_200_OK)
            
            else:
                logger.warning(f"Unauthorized delete attempt by {request.user.email} for category {category_id}")
                return Response(
                    {'status': 'error', 'message': 'Not authorized to delete categories'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except CategoryModel.DoesNotExist:
            logger.error(f"Category {category_id} not found for {request.user.email}")
            return Response(
                {'status': 'error', 'message': 'Category not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting category for {request.user.email}: {str(e)}, Request data: {request.data}")
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )