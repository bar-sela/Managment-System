from api import views as api_views 
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    # authentication routes 
    path("user/token/", api_views.MyTokenObtainPairView.as_view()) , # for getting a JWT token (demands Authintication)
    path("user/token/refresh/", TokenRefreshView.as_view()),
    path("user/register/", api_views.RegisterView.as_view()),
    path('user/password-reset-email/<str:email>/', api_views.PasswordResetEmailVerifyAPIView.as_view()), # Get specific USER
    path("user/password-change/" , api_views.PasswordChangeAPIView.as_view()) ,  # change password
    
    # Core EndPoints
    path("course/category/", api_views.CategoryListAPIview.as_view()),
    path("course/course-List/", api_views.CourseListAPIview.as_view()),
    path("course/course-detail/<slug>/", api_views.CourseDetailAPIview.as_view()),
    path("course/cart/", api_views.CartDetailsAPIview.as_view()), # create a new item in cart
    path("course/cart-list/<user_id>" , api_views.CartListAPIview.as_view()), # get all the cart items belongs to the user 
    path("course/cart-item-delete/<user_id>/<item_id>" , api_views.CartDeleteAPIview.as_view()), # dell from the elements inside the cart
    path("cart/stats/<user_id>", api_views.CartStatsAPIView.as_view()),  # prices of cart
    path("order/create-order/",api_views.CreateOrderApiView.as_view()),  # create order
    path("coupon/apply/<code><teacher_id><user_id>/", api_views.CouponApplyApiView.as_view()),
    path("payment/stripe-checkout/<cart_id>" , api_views.StripeCheckoutAPIView.as_view()),
    path("payment/payment-successes" , api_views.PaymentSuccessAPIView.as_view()), 
    path("course/search" , api_views.SearchCourseAPIView.as_view())
]
